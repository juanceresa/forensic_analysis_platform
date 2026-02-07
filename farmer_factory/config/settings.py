"""
Configuration settings for Farmer Factory.
Loads from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Ignore unknown environment variables
    )

    # Google Cloud Vision
    google_application_credentials: Optional[Path] = None
    google_cloud_project: Optional[str] = None

    # Anthropic Claude API
    anthropic_api_key: Optional[str] = None

    # Supabase
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None  # Anon key for client
    supabase_service_role_key: Optional[str] = None  # Service role key for admin operations

    # Processing Configuration
    log_level: str = "INFO"
    max_workers: int = 4
    ocr_confidence_threshold: float = 0.60
    entity_confidence_threshold: float = 0.70

    # Paths
    cases_dir: Path = Path("./cases")
    output_dir: Path = Path("./output")

    # Translation
    translation_enabled: bool = True
    translation_backend: str = "gcp"
    translation_target_language: str = "en"

    # Model Configuration
    # NOTE: Anthropic requires explicit version dates, update these when new versions release
    claude_model: str = "claude-haiku-4-5-20251001"  # Default to Haiku 4.5 (cheap)
    claude_model_retry: str = "claude-sonnet-4-5-20250929"  # Upgrade on retry to Sonnet 4.5

    # API Limits
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    api_timeout: int = 120  # seconds

    # Processing Limits
    max_pages_per_document: int = 50
    max_entities_per_document: int = 500
    max_graph_nodes: int = 2000

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.cases_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()
