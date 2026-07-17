"""
ZeroBounce email verification — the no-Apify deliverability confirm.

Replaces `apify.verify_emails` (account56/email-verifier, an Apify Store
actor) as the default verifier used by `main.py email-verify` and
`email_enrich.enrich`. Same trust model as everything else in this
codebase: `email_check.classify_verification` owns the PASS/WARN/FAIL
verdict — this module only calls the API and normalizes its response
shape into what that classifier already reads (email/status/free/role).
It exists because ZeroBounce's free tier (100 verification credits/month,
no card, credits don't expire) covers this system's real volume without
drawing on Apify's small shared monthly cap, which LinkedIn/Instagram
(the one thing with no substitute) need instead.

Reads `ZEROBOUNCE_API_KEY` from the environment — an env secret on the
runner, never in code. A missing key fails closed with a clear message,
same contract as `apify.ApifyError`. `apify.verify_emails` still exists as
a manual cross-check/fallback if this key isn't set.

API: https://api.zerobounce.net/v2/validatebatch (POST, up to 100
addresses per call) — one address is just a one-item batch, so this one
function covers both `email-verify`'s single address and
`email-enrich`'s batched candidate list.
"""

from __future__ import annotations

import os
from typing import Any

import requests

ZEROBOUNCE_BASE = "https://api.zerobounce.net/v2"

# ZeroBounce's documented status vocabulary. `email_check.classify_verification`
# already treats "status" as a recognized result-token field and understands
# valid/invalid/catch-all(-_)/unknown/spamtrap/abuse/do_not_mail.
_STATUSES = ("valid", "invalid", "catch-all", "unknown", "spamtrap", "abuse", "do_not_mail")


class EmailVerifierError(RuntimeError):
    """Any verifier-side failure: missing key, network, bad response."""


def _api_key() -> str:
    key = os.environ.get("ZEROBOUNCE_API_KEY")
    if not key:
        raise EmailVerifierError(
            "ZEROBOUNCE_API_KEY is not set. This runner needs the key as an "
            "environment secret (ZEROBOUNCE_API_KEY) — the free tier (100 "
            "credits/month, no card, no expiry) covers normal verify volume."
        )
    return key


def _normalize(row: dict) -> dict:
    """ZeroBounce's response shape -> the shape
    `email_check.classify_verification` already reads (email/status/free/role)."""
    sub_status = (row.get("sub_status") or "").strip().lower()
    return {
        "email": row.get("address"),
        "status": (row.get("status") or "").strip().lower(),
        "sub_status": sub_status,
        "free": bool(row.get("free_email")),
        "role": sub_status == "role_based",
    }


def verify_emails(emails: list[str], *, raw: bool = False) -> list[dict]:
    """Verify one or more addresses via ZeroBounce's batch endpoint (up to
    100 per call) — the confirm step before an address enters the CRM.

    Same input/output contract as `apify.verify_emails`: a list of
    addresses in, a list of result rows out (each readable by
    `email_check.classify_verification`), an `EmailVerifierError` on any
    failure worth distinguishing (missing key, network, bad response).
    """
    if not emails:
        raise EmailVerifierError("verify_emails needs at least one address")
    payload: dict[str, Any] = {
        "api_key": _api_key(),
        "email_batch": [{"email_address": e} for e in emails],
    }
    try:
        resp = requests.post(f"{ZEROBOUNCE_BASE}/validatebatch", json=payload, timeout=90)
    except requests.RequestException as exc:
        raise EmailVerifierError(f"network error reaching ZeroBounce: {exc}") from exc

    if resp.status_code == 401:
        raise EmailVerifierError("401 Unauthorized — ZEROBOUNCE_API_KEY is missing or invalid.")
    if resp.status_code == 402:
        raise EmailVerifierError("402 Payment Required — the ZeroBounce account is out of credits.")
    if not resp.ok:
        raise EmailVerifierError(f"{resp.status_code} from ZeroBounce: {resp.text[:400]}")
    try:
        data = resp.json()
    except ValueError as exc:
        raise EmailVerifierError(f"non-JSON response from ZeroBounce: {resp.text[:200]}") from exc

    rows = data.get("email_batch", []) or []
    if raw:
        return rows
    return [_normalize(r) for r in rows]
