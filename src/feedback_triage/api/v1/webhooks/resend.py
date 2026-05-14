"""``POST /api/v1/webhooks/resend`` — Resend delivery-status ingestion.

PR 4.3. Translates incoming Resend webhook events into idempotent
``email_log.status`` updates via
:mod:`feedback_triage.services.email_log_updater`.

Wire format
-----------

Resend signs every webhook with the
`Standard Webhooks <https://standardwebhooks.com>`_ scheme (Svix-
compatible):

* ``svix-id``         — unique message id (``msg_…``).
* ``svix-timestamp``  — unix-seconds when Resend signed the request.
* ``svix-signature``  — space-separated list of ``v1,<base64-sig>``
  pairs; multiple signatures support secret rotation.

The signed payload is the literal string
``"{svix-id}.{svix-timestamp}.{body}"``; the signature is
``base64(HMAC-SHA256(payload, secret))`` where ``secret`` is the
base64-decoded suffix of ``whsec_<base64>`` configured as
``RESEND_WEBHOOK_SECRET``.

We hand-implement the verifier (≈ 30 LOC) rather than depending on
``svix-py``: the runtime image already pays for ``hmac`` / ``hashlib``
/ ``base64``, and ADR 061 is explicit about avoiding optional
provider SDKs.

Event mapping
-------------

============================  ==========================
Resend event ``type``         ``EmailStatus`` written
============================  ==========================
``email.delivered``           ``delivered``
``email.bounced``             ``bounced``
``email.complained``          ``complained``
============================  ==========================

Every other event type (``email.sent``, ``email.delivery_delayed``,
``email.opened``, ``email.clicked``, ``email.failed``) is acknowledged
with ``204 No Content`` and ignored. ``email.sent`` in particular is
already written by the in-process send loop, so re-applying it from
the webhook would be redundant.

Failure modes
-------------

* ``503`` — ``RESEND_WEBHOOK_SECRET`` is unset (route is mounted but
  not enabled). Configuring the secret enables ingestion without a
  redeploy.
* ``400`` — missing / malformed Svix headers, body that is not a JSON
  object, or a payload that lacks ``data.email_id``.
* ``401`` — signature verification failed (unknown secret, replayed
  body, or tampered headers).
* ``2xx`` — every other case, including ``IGNORED`` (lower-precedence
  event arrived after a higher-precedence one) and ``NOT_FOUND``
  (provider id we never wrote — verification sends predating the
  webhook secret rollout). Returning a non-2xx for ``NOT_FOUND``
  would trigger Resend's redelivery loop.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session as DbSession

from feedback_triage.config import Settings, get_settings
from feedback_triage.database import get_db
from feedback_triage.enums import EmailStatus
from feedback_triage.services.email_log_updater import apply_provider_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

DbDep = Annotated[DbSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

#: Replay window enforced by the verifier. Standard Webhooks recommends
#: 5 minutes; Resend retries on a 5xx from us, so a tight window is
#: safe.
_TIMESTAMP_TOLERANCE_SECONDS = 5 * 60

#: Resend event ``type`` → ``EmailStatus`` mapping. Anything outside
#: this set is acknowledged with 204 and not written.
_EVENT_TYPE_MAP: dict[str, EmailStatus] = {
    "email.delivered": EmailStatus.DELIVERED,
    "email.bounced": EmailStatus.BOUNCED,
    "email.complained": EmailStatus.COMPLAINED,
}


def _bad_request(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": "bad_webhook_payload", "message": message},
    )


_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={
        "code": "invalid_signature",
        "message": "Webhook signature did not verify.",
    },
)

_NOT_CONFIGURED = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail={
        "code": "webhook_not_configured",
        "message": "Resend webhook secret is not configured.",
    },
)


def _decode_secret(raw: str) -> bytes:
    """Decode a ``whsec_<base64>``-prefixed shared secret to raw bytes.

    Standard Webhooks ships the secret with a ``whsec_`` prefix that
    is stripped before base64-decoding the rest. A secret without the
    prefix is also accepted (some providers omit it) and used
    verbatim — base64-decoded if it parses, raw otherwise.
    """
    body = raw.removeprefix("whsec_")
    try:
        return base64.b64decode(body, validate=True)
    except (ValueError, base64.binascii.Error):  # type: ignore[attr-defined]
        # Treat as a raw shared secret (Resend currently always
        # ships base64, but this keeps the verifier robust to a
        # provider tweak).
        return raw.encode("utf-8")


def _verify_signature(
    *,
    secret: bytes,
    msg_id: str,
    timestamp: str,
    body: bytes,
    signature_header: str,
) -> bool:
    """Constant-time-verify a Standard-Webhooks ``svix-signature`` header.

    Returns ``True`` if any of the comma-or-space-separated
    ``v1,<base64>`` pairs in ``signature_header`` matches the
    HMAC-SHA256 of ``"{msg_id}.{timestamp}.{body}"`` under ``secret``.
    """
    payload = f"{msg_id}.{timestamp}.".encode() + body
    expected = base64.b64encode(
        hmac.new(secret, payload, hashlib.sha256).digest(),
    ).decode("ascii")
    # Multiple signatures are separated by *whitespace* per Standard
    # Webhooks (rotation support); each entry is a ``"<version>,<sig>"``
    # pair. We must not split on the comma inside the pair.
    for candidate in signature_header.split():
        version, _, sig = candidate.partition(",")
        if version != "v1" or not sig:
            continue
        if hmac.compare_digest(sig, expected):
            return True
    return False


def _parse_payload(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise _bad_request("Body is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise _bad_request("Body must be a JSON object.")
    return payload


@router.post(
    "/resend",
    summary="Resend delivery / bounce / complaint events",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    include_in_schema=False,
)
async def resend_webhook(
    request: Request,
    db: DbDep,
    settings: SettingsDep,
) -> Response:
    """Verify and ingest a single Resend webhook event."""
    secret_value = settings.resend_webhook_secret.get_secret_value()
    if not secret_value:
        raise _NOT_CONFIGURED

    msg_id = request.headers.get("svix-id")
    timestamp = request.headers.get("svix-timestamp")
    signature = request.headers.get("svix-signature")
    if not (msg_id and timestamp and signature):
        raise _bad_request("Missing svix-* signature headers.")

    try:
        ts_int = int(timestamp)
    except ValueError as exc:
        raise _bad_request("svix-timestamp is not an integer.") from exc
    if abs(int(time.time()) - ts_int) > _TIMESTAMP_TOLERANCE_SECONDS:
        raise _UNAUTHORIZED

    body = await request.body()
    secret = _decode_secret(secret_value)
    if not _verify_signature(
        secret=secret,
        msg_id=msg_id,
        timestamp=timestamp,
        body=body,
        signature_header=signature,
    ):
        raise _UNAUTHORIZED

    payload = _parse_payload(body)
    event_type = payload.get("type")
    if not isinstance(event_type, str):
        raise _bad_request("Missing 'type' field.")

    new_status = _EVENT_TYPE_MAP.get(event_type)
    if new_status is None:
        # Acknowledge so Resend stops redelivering, but no-op.
        logger.info("resend.webhook.skip unmapped-event")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    data = payload.get("data")
    if not isinstance(data, dict):
        raise _bad_request("Missing 'data' object.")
    provider_id = data.get("email_id")
    if not isinstance(provider_id, str) or not provider_id:
        raise _bad_request("Missing 'data.email_id'.")

    apply_provider_event(
        db,
        provider_id=provider_id,
        new_status=new_status,
    )
    logger.info("resend.webhook.processed")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
