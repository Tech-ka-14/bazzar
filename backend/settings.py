"""Central, validated configuration for the Bazzar backend.

Single source of truth for environment-driven settings. Replaces scattered
``os.environ.get`` calls: instantiate ``get_settings()`` and every value is
type-checked at boot with a clear error message on misconfiguration.

Values come from (lowest to highest precedence): defaults < repo-root ``.env``
< real environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Bazzar backend settings (env prefix: none — names are already explicit)."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- data layer -------------------------------------------------------
    bazzar_data_dir: Path = Field(
        default=REPO_ROOT / "data",
        description="Directory holding bazzar.duckdb, chart cache, and logs.",
    )
    bazzar_api_port: int = Field(default=8787, ge=1, le=65535)
    bazzar_api_host: str = Field(default="127.0.0.1")

    # --- market data provider (OpenAlgo today; Kite lands in P3) ----------
    openalgo_base_url: str = Field(default="http://127.0.0.1:5000")
    openalgo_api_key: str = Field(default="")
    broker_api_key: str = Field(default="")
    broker_api_secret: str = Field(default="")

    # --- observability -----------------------------------------------------
    log_level: str = Field(default="INFO")

    @property
    def db_path(self) -> Path:
        return self.bazzar_data_dir / "bazzar.duckdb"

    @property
    def log_dir(self) -> Path:
        return self.bazzar_data_dir / "logs"

    @property
    def chart_cache_dir(self) -> Path:
        return self.bazzar_data_dir / "chart_cache"


@lru_cache
def get_settings() -> Settings:
    """Process-wide cached settings; validates on first access."""
    return Settings()
