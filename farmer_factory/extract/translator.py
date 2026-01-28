"""Translation service with local (CTranslate2) and cloud (GCP) backends.

Local: Uses Argos model files via CTranslate2 + subword-nmt. No network calls.
Cloud: Uses Google Cloud Translation API. Better quality, requires credentials.

Backend is selected via TRANSLATION_BACKEND setting ("local" or "gcp").
"""

import codecs
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Language codes that don't need translation
ENGLISH_CODES = {"en", "en-us", "en-gb", "eng"}

# Default location for Argos model packages
_ARGOS_PACKAGES_DIR = Path.home() / ".local" / "share" / "argos-translate" / "packages"


def needs_translation(language_code: Optional[str]) -> bool:
    """
    Check if text in the given language needs translation to English.

    Returns False for unknown codes to avoid unnecessary work when detection fails.
    """
    if not language_code or language_code == "unknown":
        return False
    return language_code.lower() not in ENGLISH_CODES


def _find_model_dir(source_lang: str, target_lang: str) -> Optional[Path]:
    """Find an installed Argos model package for the given language pair."""
    if not _ARGOS_PACKAGES_DIR.exists():
        return None

    pattern = f"translate-{source_lang}_{target_lang}*"
    matches = sorted(_ARGOS_PACKAGES_DIR.glob(pattern))
    if matches:
        return matches[-1]  # Latest version
    return None


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


# ---------------------------------------------------------------------------
# Local backend: CTranslate2 + subword-nmt (BPE)
# ---------------------------------------------------------------------------

class LocalTranslationService:
    """
    Offline translation using CTranslate2 with Argos model packages.

    Bypasses the Argos Python API to avoid stanza/sentencepiece compatibility
    issues. Uses subword-nmt for BPE tokenization (pure Python).
    """

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language
        self._translators: dict[str, tuple] = {}
        self._available: Optional[bool] = None

    @property
    def is_available(self) -> bool:
        """Check if ctranslate2 and subword_nmt are installed."""
        if self._available is None:
            try:
                import ctranslate2  # noqa: F401
                from subword_nmt.apply_bpe import BPE  # noqa: F401
                self._available = True
            except ImportError as e:
                logger.warning(
                    "Local translation dependencies missing (%s). "
                    "Install with: pip install ctranslate2 subword-nmt", e,
                )
                self._available = False
        return self._available

    def _get_translator(self, source_language: str) -> Optional[tuple]:
        """Get or create a (ctranslate2.Translator, BPE) pair."""
        if not self.is_available:
            return None

        cache_key = f"{source_language}_{self.target_language}"
        if cache_key in self._translators:
            return self._translators[cache_key]

        # Prefer exact code, then prefix match for installed models
        model_dir = _find_model_dir(source_language, self.target_language)
        if not model_dir:
            # Try prefix match (e.g., es-419 vs es)
            base_src = source_language.split("-")[0]
            base_tgt = self.target_language.split("-")[0]
            model_dir = _find_model_dir(base_src, base_tgt)

        if not model_dir:
            logger.warning(
                "Argos model not found for %s→%s. Download from "
                "https://argos-net.com/ and install with: "
                "python -c \"from argostranslate import package; "
                "package.install_from_path('translate-%s_%s-*.argosmodel')\"",
                source_language, self.target_language,
                source_language, self.target_language,
            )
            return None

        try:
            import ctranslate2
            from subword_nmt.apply_bpe import BPE

            os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

            ct2_model_dir = model_dir / "model"
            bpe_model_path = model_dir / "bpe.model"

            if not ct2_model_dir.exists() or not bpe_model_path.exists():
                logger.error("Model files missing in %s", model_dir)
                return None

            translator = ctranslate2.Translator(str(ct2_model_dir), device="cpu")
            bpe_file = codecs.open(str(bpe_model_path), encoding="utf-8")
            bpe = BPE(bpe_file)

            pair = (translator, bpe)
            self._translators[cache_key] = pair
            logger.info("Loaded local translation model: %s", model_dir.name)
            return pair
        except Exception as e:
            logger.error("Failed to load local translation model: %s", e)
            return None

    def translate(
        self,
        text: str,
        source_language: str = "es",
        max_chunk_size: int = 3000,
    ) -> Optional[str]:
        """Translate text using local CTranslate2 model."""
        if not text or not text.strip():
            return text
        if source_language.lower() in ENGLISH_CODES and self.target_language == "en":
            return text

        translator = self._get_translator(source_language)
        if not translator:
            return None

        if len(text) <= max_chunk_size:
            try:
                return self._translate_segment(text, translator)
            except Exception as e:
                logger.error("Local translation failed: %s", e)
                return None

        chunks = _split_into_chunks(text, max_chunk_size)
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                translated_chunks.append(self._translate_segment(chunk, translator))
                logger.debug("Translated chunk %s/%s", i + 1, len(chunks))
            except Exception as e:
                logger.warning("Failed to translate chunk %s: %s", i + 1, e)
                translated_chunks.append(chunk)

        return "\n\n".join(translated_chunks)

    def _translate_segment(self, text: str, translator: tuple) -> str:
        """Translate a single segment via CTranslate2 + BPE."""
        ct2_translator, bpe = translator
        tokens = bpe.process_line(text).split()
        results = ct2_translator.translate_batch([tokens])
        output_tokens = results[0].hypotheses[0]
        return " ".join(output_tokens).replace("@@ ", "").replace("@@", "")


# ---------------------------------------------------------------------------
# Cloud backend: Google Cloud Translation API
# ---------------------------------------------------------------------------

class GCPTranslationService:
    """
    Cloud translation using Google Cloud Translation API (v2).

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

_default_service: Optional[LocalTranslationService | GCPTranslationService] = None


def get_translation_service() -> LocalTranslationService | GCPTranslationService:
    """Get the translation service based on TRANSLATION_BACKEND setting."""
    global _default_service
    if _default_service is None:
        from farmer_factory.config.settings import settings

        backend = getattr(settings, "translation_backend", "local")

        if backend == "gcp":
            logger.info("Using GCP Cloud Translation backend")
            _default_service = GCPTranslationService(
                target_language=settings.translation_target_language,
            )
        else:
            logger.info("Using local CTranslate2 translation backend")
            _default_service = LocalTranslationService(
                target_language=settings.translation_target_language,
            )
    return _default_service


def translate_text(
    text: str,
    source_language: Optional[str] = None,
    target_language: str = "en",
) -> Optional[str]:
    """
    Translate text using the configured backend (local or GCP).

    If source_language is unknown/None, defaults to 'es' (most common intake language).
    """
    service = get_translation_service()
    if service.target_language != target_language:
        # Preserve backend type when switching target language
        if isinstance(service, LocalTranslationService):
            service = LocalTranslationService(target_language=target_language)
        else:
            service = GCPTranslationService(target_language=target_language)

    source = source_language.lower() if source_language else "es"
    return service.translate(text, source)
