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
    bazzar_api_token: str = Field(
        default="",
        description="Localhost bearer token (env BAZZAR_API_TOKEN) required on "
        "every /api/* request when set. The Electron main process generates a "
        "random 32-byte hex token per launch and passes it here; when unset "
        "(plain `python -m backend.server` dev run) the API is open — "
        "documented development fallback.",
    )
    bazzar_api_concurrency: int = Field(
        default=4,
        ge=1,
        le=64,
        description="Max concurrent heavy endpoint jobs (chart rendering) so "
        "the sidecar event loop stays responsive.",
    )

    # --- market data provider (P3: kite is primary; openalgo fallback) -----
    market_data_provider: str = Field(
        default="openalgo",
        description="Active provider: kite | openalgo | nse_bhavcopy.",
    )
    kite_api_key: str = Field(
        default="",
        description="Kite Connect API key (non-secret). The API secret and the "
        "daily access token live in the OS keyring ONLY — never here.",
    )
    openalgo_base_url: str = Field(default="http://127.0.0.1:5000")
    openalgo_api_key: str = Field(default="")
    broker_api_key: str = Field(default="")
    broker_api_secret: str = Field(default="")

    # --- open-data source API keys (P4; non-secret public keys, .env only) --
    fred_api_key: str = Field(
        default="",
        description="FRED API key (env FRED_API_KEY) for the us_fed_funds "
        "benchmark. Free, non-secret public key from "
        "https://fred.stlouisfed.org/docs/api/api_key.html — .env only, never "
        "committed. When unset the FRED sync is skipped (never fabricated).",
    )
    ogd_api_key: str = Field(
        default="",
        description="Open Government Data (data.gov.in) API key (env "
        "OGD_API_KEY), used by the P4-B OGD fetchers. Free public key from "
        "https://data.gov.in/user — .env only, never committed.",
    )

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
