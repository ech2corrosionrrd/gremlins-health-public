from typing import Annotated, List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Gremlins Health API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    # "development" relaxes secret validation for local work.
    # Anything else (staging/production) requires real secrets to be supplied.
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # No default: the app refuses to start without an explicit key.
    SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./gremlins_health.db"

    # Redis (used by the rate limiter when reachable)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Solana
    SOLANA_RPC_URL: str = "https://api.devnet.solana.com"
    SOLANA_NETWORK: str = "devnet"
    PROGRAM_ID: str = "A9oXQuqhwkycQKPRAHTrqBYZ8v985PagPmcQvEWtSmEX"

    # Telegram. Empty means Telegram login is disabled rather than insecure.
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBAPP_URL: str = "http://localhost:5173"
    # Reject initData older than this. Telegram reissues initData every time
    # the Mini App is opened, so a 24h window bought nothing except 21 extra
    # hours of life for an intercepted string. 3h matches the sibling sibling gateway.
    TELEGRAM_INIT_DATA_MAX_AGE_SECONDS: int = 10800

    # Anti-Cheat Thresholds
    MIN_STEP_CADENCE_VARIANCE: float = 0.04  # Below this indicates mechanical shaker
    MAX_HUMAN_CADENCE_SPM: int = 240         # Steps per minute ceiling
    MAX_HUMAN_SPEED_KMH: float = 45.0        # Max realistic human sprint
    ELEVATION_CHECK_TOLERANCE_M: float = 150.0  # Tolerance for barometric/GPS mismatch

    # Economy guard rails (per UTC day, per user)
    DAILY_STEP_CAP: int = 80_000
    DAILY_STAMINA_CAP: int = 600
    DAILY_XP_CAP: int = 25_000
    MAX_ACTIVITY_DURATION_SECONDS: int = 24 * 3600

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 120
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10
    # Number of reverse proxies in front of the app. 0 = trust request.client
    # only. Set to 1 behind a single nginx so X-Forwarded-For is honoured.
    TRUSTED_PROXY_COUNT: int = 0

    # CORS - explicit origins only. "*" is rejected below.
    # NoDecode: pydantic-settings would otherwise try to JSON-parse this
    # from the environment; the validator below accepts a plain
    # comma-separated string instead.
    BACKEND_CORS_ORIGINS: Annotated[List[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://web.telegram.org",
    ]

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        # Allow a comma-separated string in the environment.
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def _no_wildcard_origin(cls, v: List[str]) -> List[str]:
        # A wildcard origin combined with allow_credentials=True is both
        # rejected by browsers and a CSRF footgun, so refuse it outright.
        if any(o.strip() == "*" for o in v):
            raise ValueError(
                "BACKEND_CORS_ORIGINS must not contain '*'. "
                "List the exact origins that may call this API."
            )
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def _reject_known_weak_key(cls, v: str) -> str:
        if "change-in-prod" in v or v.startswith("gremlins-super-secret"):
            raise ValueError(
                "SECRET_KEY is the shipped placeholder. Generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT != "development"


settings = Settings()  # type: ignore[call-arg]  # values come from env/.env
