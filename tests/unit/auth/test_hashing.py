"""Unit tests for :mod:`feedback_triage.auth.hashing`.

Covers happy path, wrong-password rejection, malformed-hash rejection
(includes the legacy admin sentinel ``!disabled-legacy-v1-admin!``
written by Migration A), and the ``needs_rehash`` signal when stored
parameters drift from the current module constants.
"""

from __future__ import annotations

from argon2 import PasswordHasher

from feedback_triage.auth import hashing


def test_hash_password_round_trips() -> None:
    encoded = hashing.hash_password("correct horse battery staple")
    assert encoded.startswith("$argon2id$")
    assert hashing.verify_password("correct horse battery staple", encoded) is True


def test_verify_password_rejects_wrong_password() -> None:
    encoded = hashing.hash_password("right")
    assert hashing.verify_password("wrong", encoded) is False


def test_verify_password_rejects_legacy_admin_sentinel() -> None:
    """The synthetic legacy admin's ``password_hash`` is a sentinel,
    not a real Argon2 encoded value. Any caller that tries to
    authenticate as that user must fail closed."""
    sentinel = "!disabled-legacy-v1-admin!"
    assert hashing.verify_password("anything", sentinel) is False
    assert hashing.verify_password("", sentinel) is False


def test_verify_password_rejects_malformed_hash() -> None:
    assert hashing.verify_password("anything", "") is False
    assert hashing.verify_password("anything", "not-a-hash") is False


def test_needs_rehash_false_for_current_params() -> None:
    encoded = hashing.hash_password("password")
    assert hashing.needs_rehash(encoded) is False


def test_needs_rehash_true_for_weaker_params() -> None:
    """A hash minted with weaker parameters must signal a rehash.

    Simulates the upgrade path where an older deploy used a smaller
    ``time_cost`` or ``memory_cost``.
    """
    weak = PasswordHasher(time_cost=1, memory_cost=8 * 1024, parallelism=1)
    weak_encoded = weak.hash("password")
    assert hashing.needs_rehash(weak_encoded) is True
    # The weaker hash still verifies — needs_rehash is a *separate*
    # signal from verify_password.
    assert hashing.verify_password("password", weak_encoded) is True


def test_warmup_does_not_raise() -> None:
    # No assertion beyond "doesn't blow up"; the FastAPI lifespan calls
    # this on startup and we don't want it to mask a packaging mistake.
    hashing.warmup()
