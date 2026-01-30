"""Claude API client with retry logic for extraction."""

import logging
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ClaudeAPIClient:
    """Wrapper for Anthropic Claude API with retry logic."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key (loads from env if None)
        """
        self.api_key = api_key
        self._client = None  # Lazy initialization

    def _get_client(self):
        """Get or initialize Anthropic client (lazy initialization)."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
        return self._client

    def call_standard(
        self,
        prompt: str,
        model: str = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        api_timeout: int = 120
    ) -> str:
        """
        Call Claude API with exponential backoff retry logic.

        Args:
            prompt: The prompt to send
            model: Model to use (defaults to settings)
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            api_timeout: API timeout in seconds

        Returns:
            Claude's response text

        Raises:
            Exception: If all retries fail
        """
        from farmer_factory.config.settings import settings

        if model is None:
            model = settings.claude_model

        client = self._get_client()
        retry_model = settings.claude_model_retry

        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Claude API (attempt {attempt + 1}/{max_retries}, model: {model})")

                response = client.messages.create(
                    model=model,
                    max_tokens=4096,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=api_timeout
                )

                # Extract text from response
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                else:
                    raise ValueError("Empty response from Claude API")

            except Exception as e:
                error_type = type(e).__name__
                logger.warning(f"Claude API error (attempt {attempt + 1}): {error_type}: {str(e)}")

                # Check if we should retry
                is_last_attempt = (attempt == max_retries - 1)

                # Rate limit errors - exponential backoff
                if "rate_limit" in str(e).lower() or "RateLimitError" in error_type:
                    if not is_last_attempt:
                        delay = retry_delay * (2 ** attempt)
                        logger.info(f"Rate limited, waiting {delay}s before retry...")
                        time.sleep(delay)
                        continue

                # Timeout errors - retry with upgrade to Sonnet
                if "timeout" in str(e).lower() or "APITimeoutError" in error_type:
                    if not is_last_attempt and model != retry_model:
                        logger.info(f"Timeout, upgrading to {retry_model} for retry...")
                        model = retry_model
                        time.sleep(retry_delay)
                        continue

                # Connection/server errors - simple retry
                if any(keyword in str(e).lower() for keyword in ["connection", "server", "503", "502", "500"]):
                    if not is_last_attempt:
                        time.sleep(retry_delay)
                        continue

                # If we've exhausted retries or it's a non-retryable error, raise
                if is_last_attempt:
                    logger.error(f"All Claude API retries exhausted: {str(e)}")
                    raise

                # For other errors, just wait and retry
                time.sleep(retry_delay)

        raise Exception("Claude API retries exhausted (should not reach here)")

    def call_with_thinking(
        self,
        prompt: str,
        model: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        api_timeout: int = 180,
        thinking_budget: int = 10000,
        max_tokens: int = 16000,
    ) -> Tuple[str, Dict[str, Any]]:
        """Call Claude with extended thinking enabled.

        Args:
            prompt: The prompt to send
            model: Model ID (must support thinking — Sonnet or Opus)
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            api_timeout: API timeout in seconds
            thinking_budget: Token budget for thinking
            max_tokens: Max output tokens (must exceed thinking_budget)

        Returns:
            (response_text, usage_dict) where usage_dict contains:
            input_tokens, output_tokens, thinking_tokens, model, cost
        """
        from farmer_factory.config.settings import settings

        if model is None:
            model = settings.claude_model_retry  # Default to Sonnet for thinking

        # Model guard: thinking requires Sonnet or higher
        if not any(k in model for k in ("sonnet", "opus")):
            logger.warning(
                f"Model {model} does not support thinking, "
                f"delegating to call_standard()"
            )
            text = self.call_standard(prompt=prompt, model=model)
            estimated_usage = {
                "input_tokens": 0,
                "output_tokens": 0,
                "thinking_tokens": 0,
                "model": model,
                "cost": 0.0,
            }
            return text, estimated_usage

        client = self._get_client()
        fallback_model = settings.claude_model  # Haiku

        for attempt in range(max_retries):
            try:
                current_model = model
                use_thinking = True

                # Final attempt: downgrade to Haiku without thinking
                if attempt == max_retries - 1 and max_retries > 1:
                    current_model = fallback_model
                    use_thinking = False
                    logger.warning(
                        f"Final attempt: downgrading to {fallback_model} (no thinking)"
                    )

                logger.info(
                    f"Calling Claude API (attempt {attempt + 1}/{max_retries}, "
                    f"model: {current_model}, thinking: {use_thinking})"
                )

                kwargs: Dict[str, Any] = {
                    "model": current_model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                    "timeout": api_timeout,
                }

                if use_thinking:
                    kwargs["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": thinking_budget,
                    }
                    # Anthropic rejects temperature with thinking enabled
                else:
                    kwargs["temperature"] = 0.1

                response = client.messages.create(**kwargs)

                # Extract text block (skip thinking blocks)
                text = ""
                for block in response.content:
                    if block.type == "text":
                        text = block.text
                        break

                if not text:
                    raise ValueError("No text block in thinking response")

                # Build usage dict from actual API response
                usage = response.usage
                input_tokens = getattr(usage, "input_tokens", 0)
                output_tokens = getattr(usage, "output_tokens", 0)
                # cache_read_input_tokens may exist on some responses
                thinking_tokens = 0
                if hasattr(usage, "thinking_tokens"):
                    thinking_tokens = usage.thinking_tokens
                elif use_thinking:
                    # Estimate from total output minus visible output
                    visible_tokens = len(text.split()) * 1.3
                    thinking_tokens = max(0, int(output_tokens - visible_tokens))

                # Compute cost
                cost = self._compute_cost(
                    current_model, input_tokens, output_tokens
                )

                usage_dict = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "thinking_tokens": thinking_tokens,
                    "model": current_model,
                    "cost": cost,
                }

                return text, usage_dict

            except Exception as e:
                error_type = type(e).__name__
                logger.warning(
                    f"Thinking call error (attempt {attempt + 1}): "
                    f"{error_type}: {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                raise

        raise Exception("Claude API thinking retries exhausted")

    @staticmethod
    def _compute_cost(
        model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Compute cost from actual token counts."""
        # Pricing per token (2026 estimates)
        if "opus" in model:
            inp, out = 15.00 / 1_000_000, 75.00 / 1_000_000
        elif "sonnet" in model:
            inp, out = 3.00 / 1_000_000, 15.00 / 1_000_000
        else:
            inp, out = 0.25 / 1_000_000, 1.25 / 1_000_000
        return (input_tokens * inp) + (output_tokens * out)
