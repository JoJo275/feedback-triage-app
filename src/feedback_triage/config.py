"""Application settings via pydantic-settings.

Loads configuration from process env vars (and optionally a `.env` file
in development). Values here are the single source of truth for runtime
configuration; nothing else should read `os.environ` directly.

See `docs/project/spec/spec-v1.md` for the full env-var surface and
`.env.example` for documented defaults.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LOCAL_DB_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", ""})


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "production", "test"] = "development"
    log_level: Literal["trace", "debug", "info", "warning", "error", "critical"] = (
        "info"
    )
    port: int = Field(default=8000, ge=1, le=65535)

    database_url: SecretStr = Field(
        default=SecretStr(
            "postgresql+psycopg://feedback:feedback@localhost:5432/feedback",
        ),
    )

    cors_allowed_origins: str = ""

    page_size_default: int = Field(default=20, ge=1, le=1000)
    page_size_max: int = Field(default=100, ge=1, le=1000)

    # ------------------------------------------------------------------
    # Auth (v2.0). See ``docs/project/spec/v2/auth.md``.
    # ------------------------------------------------------------------
    feature_auth: bool = Field(default=True)
    """v2.0-alpha → v2.0-beta gate for the auth surface.

    When false, ``/login``, ``/signup``, ``/forgot-password``,
    ``/reset-password``, ``/verify-email``, and ``/api/v1/auth/*`` all
    return ``503 Service Unavailable``. Read once at startup; flipping
    the flag requires a redeploy. Per ``v2/auth.md``, defaults to
    ``true`` in development and is flipped to ``true`` in production
    at the alpha → beta boundary.
    """

    secure_cookies: bool = Field(default=False)
    """Toggle the ``Secure`` attribute on auth cookies.

    Defaults to ``false`` so local HTTP development works; production
    deployments MUST set ``SECURE_COOKIES=true``. The model validator
    ``_require_secure_cookies_in_production`` enforces this.
    """

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: object) -> object:
        """Normalize Railway's legacy ``postgres://`` scheme to psycopg v3.

        Wraps the result in :class:`pydantic.SecretStr` so the URL (which
        contains the DB password) never appears in ``repr(settings)``,
        ``logger.info(settings)``, or a Pydantic validation error.
        Read the plain value via ``settings.database_url.get_secret_value()``.
        """
        if isinstance(value, SecretStr):
            value = value.get_secret_value()
        if isinstance(value, str) and value.startswith("postgres://"):
            return SecretStr(
                "postgresql+psycopg://" + value[len("postgres://") :],
            )
        if isinstance(value, str) and value.startswith("postgresql://"):
            return SecretStr(
                "postgresql+psycopg://" + value[len("postgresql://") :],
            )
        if isinstance(value, str):
            return SecretStr(value)
        return value

    @property
    def cors_origins(self) -> list[str]:
        """Parsed list of CORS-allowed origins (empty list disables CORS)."""
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        """Return True when running with production semantics."""
        return self.app_env == "production"

    @model_validator(mode="after")
    def _require_remote_db_in_production(self) -> Settings:
        """Refuse to boot in production with a localhost ``DATABASE_URL``.

        Railway's pre-deploy command (``alembic upgrade head``) and the
        app process inherit env vars from the service. If the operator
        forgets to link ``${{ Postgres.DATABASE_URL }}`` per
        ``docs/project/railway-setup.md`` step 2, the default below
        silently points at ``localhost:5432`` and psycopg fails with a
        confusing ``Connection refused``. Fail loudly with an
        actionable message instead.
        """
        if self.app_env != "production":
            return self
        host = urlparse(self.database_url.get_secret_value()).hostname or ""
        if host.lower() in _LOCAL_DB_HOSTS:
            msg = (
                "DATABASE_URL is unset or points at localhost while "
                "APP_ENV=production. Link the Postgres plugin in the "
                "Railway dashboard (Variables → Reference Variable → "
                "Postgres → DATABASE_URL). See "
                "docs/project/railway-setup.md step 2."
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _require_secure_cookies_in_production(self) -> Settings:
        """Refuse to boot in production without ``SECURE_COOKIES=true``.

        Auth cookies that omit the ``Secure`` flag travel over plain
        HTTP, exposing the session token to passive network observers.
        See ``docs/project/spec/v2/auth.md`` — Session cookie.
        """
        if self.app_env == "production" and not self.secure_cookies:
            msg = (
                "SECURE_COOKIES must be true when APP_ENV=production. "
                "Auth cookies without the Secure flag leak the session "
                "token over plain HTTP. See docs/project/spec/v2/auth.md."
            )
            raise ValueError(msg)
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide cached :class:`Settings` instance."""
    return Settings()
