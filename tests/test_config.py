"""Unit tests for :mod:`feedback_triage.config`."""

from __future__ import annotations

import pytest

from feedback_triage.config import Settings


def test_defaults_are_development() -> None:
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.app_env == "development"
    assert s.is_production is False
    assert s.port == 8000
    assert s.page_size_default == 20
    assert s.page_size_max == 100


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "postgres://u:p@h:5432/d",
            "postgresql+psycopg://u:p@h:5432/d",
        ),
        (
            "postgresql://u:p@h:5432/d",
            "postgresql+psycopg://u:p@h:5432/d",
        ),
        (
            "postgresql+psycopg://u:p@h:5432/d",
            "postgresql+psycopg://u:p@h:5432/d",
        ),
    ],
)
def test_database_url_normalised_to_psycopg(raw: str, expected: str) -> None:
    s = Settings(_env_file=None, database_url=raw)  # type: ignore[call-arg]
    assert s.database_url.get_secret_value() == expected


def test_cors_origins_split_and_trimmed() -> None:
    s = Settings(  # type: ignore[call-arg]
        _env_file=None,
        cors_allowed_origins="http://a.test, http://b.test ,",
    )
    assert s.cors_origins == ["http://a.test", "http://b.test"]


def test_cors_origins_empty_disables_cors() -> None:
    s = Settings(_env_file=None, cors_allowed_origins="")  # type: ignore[call-arg]
    assert s.cors_origins == []


def test_database_url_password_is_masked_in_repr() -> None:
    """The DB password must never leak via repr/str/model_dump.

    Guards against an accidental ``logger.info(settings)`` exposing the
    URL on a public Railway deploy.
    """
    secret = "s3cret-pw"  # fixture password, not a real credential
    s = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=f"postgresql+psycopg://u:{secret}@h:5432/d",
    )
    assert secret not in repr(s)
    assert secret not in str(s)
    assert secret not in repr(s.database_url)
    assert secret not in str(s.model_dump())
    # The plaintext is still reachable for callers that explicitly opt in.
    assert s.database_url.get_secret_value().endswith(f":{secret}@h:5432/d")
