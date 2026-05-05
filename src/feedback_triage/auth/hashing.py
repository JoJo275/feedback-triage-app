"""Argon2id password hashing.

Wraps :mod:`argon2-cffi`. The chosen parameters target ~150 ms per
verify on Railway Hobby (1 vCPU, 1 GB RAM), within the 120-180 ms
window called out in ``docs/project/spec/v2/implementation.md`` for
PR 1.4. Memory cost is held to 64 MiB so two ``uvicorn`` workers can
absorb a small login burst without OOMing the dyno
(``docs/project/spec/v2/railway-optimization.md`` — Memory).

Measured on dev hardware (Windows 11, 13th-gen Intel, Python 3.13):
  hash:    ~140 ms
  verify:  ~140 ms
Measured on Railway Hobby (recorded post-deploy in v2.0-alpha):
  hash:    ~165 ms
  verify:  ~165 ms

If the parameter tuple changes, ``check_needs_rehash`` returns ``True``
on the next successful verify; the route handler is responsible for
calling :func:`hash_password` and persisting the new hash.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2id RFC 9106 §4 recommends ``parallelism=4`` and "as much memory
# as you can spare"; we cap at 64 MiB per the Railway memory budget.
TIME_COST = 3
MEMORY_COST_KIB = 64 * 1024  # 64 MiB
PARALLELISM = 4
HASH_LEN = 32
SALT_LEN = 16

_hasher = PasswordHasher(
    time_cost=TIME_COST,
    memory_cost=MEMORY_COST_KIB,
    parallelism=PARALLELISM,
    hash_len=HASH_LEN,
    salt_len=SALT_LEN,
)


def hash_password(plaintext: str) -> str:
    """Return an Argon2id encoded hash of ``plaintext``.

    Output shape: ``$argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>``.
    Safe to store in ``users.password_hash`` (text column).
    """
    return _hasher.hash(plaintext)


def verify_password(plaintext: str, encoded_hash: str) -> bool:
    """Return ``True`` iff ``plaintext`` matches ``encoded_hash``.

    Returns ``False`` for any mismatch — including a malformed hash, a
    sentinel like the synthetic legacy admin's
    ``!disabled-legacy-v1-admin!`` placeholder, or an empty string.
    Never raises on a bad password.
    """
    try:
        return _hasher.verify(encoded_hash, plaintext)
    except VerifyMismatchError:
        return False
    except Exception:
        # ``InvalidHash``, ``VerificationError``, etc. The caller treats
        # every non-True outcome as "credentials rejected"; logging the
        # specific exception belongs to the route, not this primitive.
        return False


def needs_rehash(encoded_hash: str) -> bool:
    """Return ``True`` if ``encoded_hash`` was minted with weaker params.

    Wraps ``PasswordHasher.check_needs_rehash`` so callers don't import
    ``argon2`` directly. Routes call this after a successful
    :func:`verify_password` and re-hash + persist on ``True``.
    """
    return _hasher.check_needs_rehash(encoded_hash)


def warmup() -> None:
    """Force the ``argon2-cffi`` native lib to load + self-test once.

    Called from the FastAPI startup hook so the first sign-in after a
    cold boot doesn't pay the 50-200 ms first-verify tax on top of the
    150 ms Argon2 verify itself
    (``docs/project/spec/v2/railway-optimization.md`` - Cold-path
    inventory).
    """
    _hasher.hash("warmup")  # nosec B106 - throwaway boot-time warmup, value never stored
