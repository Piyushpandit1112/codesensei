"""Central configuration loaded from environment / .env file."""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    gemini_api_key: str = ""
    groq_api_key: str = ""
    sarvam_api_key: str = ""

    default_voice: str = "amol"           # amol (deep male) | arvind | meera | diya
    default_lang: str = "hinglish"        # hinglish | hindi
    think_seconds: int = 180

    gemini_model: str = "gemini-2.0-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    sarvam_model: str = "bulbul:v2"

    cache_dir: Path = ROOT / ".codesensei_cache"
    prompts_dir: Path = ROOT / "prompts"
    assets_dir: Path = ROOT / "assets"
    data_dir: Path = ROOT / "data"

    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_prefix="",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_sarvam(self) -> bool:
        return bool(self.sarvam_api_key)


settings = Settings()
try:
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
except OSError:
    # Fallback for read-only filesystems (some PaaS deployments).
    import tempfile
    settings.cache_dir = Path(tempfile.gettempdir()) / "codesensei_cache"
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
