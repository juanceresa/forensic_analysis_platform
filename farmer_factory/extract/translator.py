"""Offline translation service using Argos Translate."""

import logging
from typing import Optional, Callable

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


class TranslationService:
    """
    Offline translation using Argos Translate.

    Requires language packages to be installed on the host. No network calls are made
    during translation (once packages are present).
    """

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language
        self._available = None

    @property
    def is_available(self) -> bool:
        """Check if argostranslate is installed."""
        if self._available is None:
            try:
                import argostranslate  # noqa: F401
                self._available = True
            except ImportError:
                logger.warning(
                    "argostranslate not installed. Install with: pip install argostranslate"
                )
                self._available = False
        return self._available

    def _get_translation_fn(self, source_language: str) -> Optional[Callable[[str], str]]:
        """Get a translate(text) callable for the given source language."""
        if not self.is_available:
            return None

        try:
            from argostranslate import translate

            langs = translate.get_installed_languages()
            src = next((l for l in langs if l.code.startswith(source_language)), None)
            tgt = next((l for l in langs if l.code.startswith(self.target_language)), None)

            if not src or not tgt:
                logger.warning(
                    "Argos language pack missing (source=%s, target=%s). "
                    "Install with: argospm install %s_%s",
                    source_language,
                    self.target_language,
                    source_language,
                    self.target_language,
                )
                return None

            translation = src.get_translation(tgt)
            return translation.translate
        except Exception as e:
            logger.error(f"Failed to initialize Argos translation: {e}")
            return None

    def translate(
        self,
        text: str,
        source_language: str = "es",
        max_chunk_size: int = 3000,
    ) -> Optional[str]:
        """
        Translate text to target language using Argos.

        Args:
            text: Text to translate
            source_language: Source language code (default: "es")
            max_chunk_size: Max characters per chunk
        """
        if not text or not text.strip():
            return text

        # If already English, skip
        if source_language.lower() in ENGLISH_CODES and self.target_language == "en":
            return text

        translate_fn = self._get_translation_fn(source_language)
        if not translate_fn:
            return None

        # Handle long text by chunking on paragraph boundaries
        if len(text) <= max_chunk_size:
            try:
                return translate_fn(text)
            except Exception as e:
                logger.error(f"Translation failed: {e}")
                return None

        chunks = self._split_into_chunks(text, max_chunk_size)
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                translated_chunks.append(translate_fn(chunk))
                logger.debug("Translated chunk %s/%s", i + 1, len(chunks))
            except Exception as e:
                logger.warning("Failed to translate chunk %s: %s", i + 1, e)
                translated_chunks.append(chunk)

        return "\n\n".join(translated_chunks)

    def _split_into_chunks(self, text: str, max_size: int) -> list[str]:
        """Split text into chunks at paragraph boundaries."""
        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current: list[str] = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para) + 2  # account for \n\n joiner
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


# Singleton instance for convenience
_default_service: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """Get the default translation service instance."""
    global _default_service
    if _default_service is None:
        _default_service = TranslationService()
    return _default_service


def translate_text(
    text: str,
    source_language: Optional[str] = None,
    target_language: str = "en",
) -> Optional[str]:
    """
    Convenience function to translate text.

    If source_language is unknown/None, defaults to 'es' (most common intake language).
    """
    service = get_translation_service()
    if service.target_language != target_language:
        service = TranslationService(target_language=target_language)

    source = source_language.lower() if source_language else "es"
    return service.translate(text, source)
