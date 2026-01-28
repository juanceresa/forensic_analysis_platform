"""Translation service using Google Cloud Translation API.

Requires google-cloud-translate package and GCP credentials.
Free tier: 500k characters/month, then $20/million characters.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Language codes that don't need translation
ENGLISH_CODES = {"en", "en-us", "en-gb", "eng"}


def needs_translation(language_code: Optional[str]) -> bool:
    """
    Check if text in the given language needs translation to English.

    Returns False for unknown codes to avoid unnecessary work when detection fails.
    """
    if not language_code or language_code == "unknown":
        return False
    return language_code.lower() not in ENGLISH_CODES


def _split_into_chunks(text: str, max_size: int) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current: list[str] = []
    current_size = 0

    for para in paragraphs:
        para_size = len(para) + 2
        if current_size + para_size > max_size and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_size = para_size
        else:
            current.append(para)
            current_size += para_size

    if current:
        chunks.append("\n\n".join(current))

    return chunks


class GCPTranslationService:
    """
    Translation using Google Cloud Translation API (v2).

    Requires google-cloud-translate package and GCP credentials.
    Free tier: 500k characters/month, then $20/million characters.
    """

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language
        self._client = None
        self._available: Optional[bool] = None

    @property
    def is_available(self) -> bool:
        """Check if google-cloud-translate is installed and credentials exist."""
        if self._available is None:
            try:
                from google.cloud import translate_v2  # noqa: F401
                self._available = True
            except ImportError:
                logger.warning(
                    "GCP translation not available. "
                    "Install with: pip install google-cloud-translate"
                )
                self._available = False
        return self._available

    def _get_client(self):
        """Lazily initialize the GCP Translation client."""
        if self._client is None:
            from google.cloud import translate_v2
            self._client = translate_v2.Client()
            logger.info("Initialized GCP Translation client")
        return self._client

    def translate(
        self,
        text: str,
        source_language: str = "es",
        max_chunk_size: int = 5000,
    ) -> Optional[str]:
        """Translate text using Google Cloud Translation API."""
        if not text or not text.strip():
            return text
        if source_language.lower() in ENGLISH_CODES and self.target_language == "en":
            return text
        if not self.is_available:
            return None

        try:
            client = self._get_client()
        except Exception as e:
            logger.error("Failed to initialize GCP Translation client: %s", e)
            return None

        if len(text) <= max_chunk_size:
            return self._translate_segment(text, source_language, client)

        chunks = _split_into_chunks(text, max_chunk_size)
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                result = self._translate_segment(chunk, source_language, client)
                translated_chunks.append(result if result else chunk)
                logger.debug("GCP translated chunk %s/%s", i + 1, len(chunks))
            except Exception as e:
                logger.warning("GCP translation failed for chunk %s: %s", i + 1, e)
                translated_chunks.append(chunk)

        return "\n\n".join(translated_chunks)

    def _translate_segment(
        self, text: str, source_language: str, client
    ) -> Optional[str]:
        """Translate a single segment via GCP."""
        try:
            result = client.translate(
                text,
                source_language=source_language,
                target_language=self.target_language,
                format_="text",
            )
            return result["translatedText"]
        except Exception as e:
            logger.error("GCP translation failed: %s", e)
            return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_default_service: Optional[GCPTranslationService] = None


def get_translation_service() -> GCPTranslationService:
    """Get the GCP translation service."""
    global _default_service
    if _default_service is None:
        from farmer_factory.config.settings import settings

        logger.info("Using GCP Cloud Translation backend")
        _default_service = GCPTranslationService(
            target_language=settings.translation_target_language,
        )
    return _default_service


def translate_text(
    text: str,
    source_language: Optional[str] = None,
    target_language: str = "en",
) -> Optional[str]:
    """
    Translate text using Google Cloud Translation API.

    If source_language is unknown/None, defaults to 'es' (most common intake language).
    """
    service = get_translation_service()
    if service.target_language != target_language:
        service = GCPTranslationService(target_language=target_language)

    source = source_language.lower() if source_language else "es"
    return service.translate(text, source)
