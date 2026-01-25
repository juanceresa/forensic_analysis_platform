"""Claude API client with retry logic for extraction."""

import logging
import time
from typing import Optional

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

    def call_with_retry(
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
