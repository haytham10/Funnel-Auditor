"""
Direct Gmail API integration for haytham@gethaytham.com — the second UAE
send inbox.

## Why this exists instead of a second Claude Gmail connector

Google's Gmail MCP server is one canonical endpoint
(https://gmailmcp.googleapis.com/mcp/v1) and Claude allows exactly one
connector bound to it — already claimed by auto-mate.one. Confirmed dead
ends: a modified query string collides with Claude's URL-uniqueness check
in a different way (passes the check, then Google's own routing can't find
a server at the modified path); a URL fragment gets stripped before the
uniqueness check even runs, so it's treated as identical to the existing
connector. There is no supported way to bind a second Google account
through that connector today (Anthropic has an open, unresolved feature
request for multi-account MCP connectors).

This module is the fallback: talk to the Gmail REST API directly, the same
pattern as audit/apify.py — raw HTTP, credentials read from the
environment, fail closed on anything missing. No Claude connector involved
for this inbox at all.

## Setup (one-time, outside this repo)

1. In the SAME Google Cloud project used for the Gmail MCP OAuth client
   (gethaytham-mcp), create a SECOND OAuth client, type "Desktop app" —
   the Claude-connector redirect URI (https://claude.ai/api/mcp/auth_callback)
   doesn't apply to this flow; a Desktop client uses a local loopback
   redirect instead.
2. Run `scripts/gethaytham_gmail_auth.py` — on a machine with a real
   browser (your laptop, NOT a cloud session, which has no interactive
   browser). It walks the one-time consent as haytham@gethaytham.com and
   prints a refresh token.
3. Store three values as environment secrets on the runner, never in code
   or committed anywhere (same handling as APIFY_TOKEN):
     GETHAYTHAM_GMAIL_CLIENT_ID
     GETHAYTHAM_GMAIL_CLIENT_SECRET
     GETHAYTHAM_GMAIL_REFRESH_TOKEN

## Scope

gmail.readonly + gmail.compose only — read threads/messages, create/list
drafts, list labels. No gmail.send: this module can't send mail even if
asked to, the same hard rule the Gmail MCP connector already enforces for
auto-mate.one. This system ends at drafts; sending is human.
"""

from __future__ import annotations

import base64
import os
import time
from email.mime.text import MIMEText
from typing import Any

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"

SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
)


class GmailGethaythamError(RuntimeError):
    """Any failure in the direct Gmail API path: missing creds, auth, HTTP."""


def _creds() -> tuple[str, str, str]:
    client_id = os.environ.get("GETHAYTHAM_GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GETHAYTHAM_GMAIL_CLIENT_SECRET")
    refresh_token = os.environ.get("GETHAYTHAM_GMAIL_REFRESH_TOKEN")
    missing = [name for name, val in (
        ("GETHAYTHAM_GMAIL_CLIENT_ID", client_id),
        ("GETHAYTHAM_GMAIL_CLIENT_SECRET", client_secret),
        ("GETHAYTHAM_GMAIL_REFRESH_TOKEN", refresh_token),
    ) if not val]
    if missing:
        raise GmailGethaythamError(
            f"{', '.join(missing)} not set. This runner needs all three as "
            "environment secrets — run scripts/gethaytham_gmail_auth.py "
            "locally once to mint the refresh token (see this module's "
            "docstring for the full setup)."
        )
    return client_id, client_secret, refresh_token


# In-memory only — re-exchanged every process start, never written to disk.
_access_token_cache: dict[str, Any] = {"token": None, "expires_at": 0.0}


def _access_token() -> str:
    """Exchange the refresh token for a short-lived access token, cached for
    the life of the process (Gmail access tokens last ~1 hour)."""
    now = time.time()
    if _access_token_cache["token"] and now < _access_token_cache["expires_at"] - 60:
        return _access_token_cache["token"]

    client_id, client_secret, refresh_token = _creds()
    try:
        resp = requests.post(TOKEN_URL, data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }, timeout=30)
    except requests.RequestException as exc:
        raise GmailGethaythamError(f"network error reaching Google OAuth: {exc}") from exc
    if not resp.ok:
        raise GmailGethaythamError(
            f"{resp.status_code} refreshing access token: {resp.text[:300]} — "
            "the refresh token may be revoked or the client creds are wrong; "
            "re-run scripts/gethaytham_gmail_auth.py"
        )
    data = resp.json()
    _access_token_cache["token"] = data["access_token"]
    _access_token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return _access_token_cache["token"]


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_access_token()}"}


def _request(method: str, path: str, **kwargs) -> dict:
    try:
        resp = requests.request(
            method, f"{GMAIL_API}{path}", headers=_headers(), timeout=30, **kwargs,
        )
    except requests.RequestException as exc:
        raise GmailGethaythamError(f"network error reaching Gmail API: {exc}") from exc
    if resp.status_code == 401:
        raise GmailGethaythamError("401 from Gmail API — access token invalid/expired unexpectedly.")
    if resp.status_code == 403:
        raise GmailGethaythamError(
            f"403 from Gmail API: {resp.text[:300]} — check the granted scopes "
            "cover this call (gmail.readonly / gmail.compose)."
        )
    if not resp.ok:
        raise GmailGethaythamError(f"{resp.status_code} from Gmail API: {resp.text[:300]}")
    if resp.status_code == 204 or not resp.content:
        return {}
    return resp.json()


# --------------------------------------------------------------------------
# Reads
# --------------------------------------------------------------------------

def search_threads(query: str, max_results: int = 10) -> list[dict]:
    """Gmail search syntax, e.g. 'is:unread newer_than:3d from:jane@site.com'."""
    data = _request("GET", "/threads", params={"q": query, "maxResults": max_results})
    return data.get("threads", [])


def count_messages(query: str, hard_cap: int = 500) -> int:
    """Exact count of messages matching a Gmail query, paginating so the
    daily send count is real (not resultSizeEstimate, which is approximate).
    Used by `main.py inbox counts` for this inbox's ceiling accounting;
    daily counts are tiny so this is one page in practice. `hard_cap` bounds
    a pathological query so it never loops unboundedly."""
    total = 0
    page_token: str | None = None
    while total < hard_cap:
        params = {"q": query, "maxResults": 100}
        if page_token:
            params["pageToken"] = page_token
        data = _request("GET", "/messages", params=params)
        total += len(data.get("messages", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return total


def get_thread(thread_id: str) -> dict:
    return _request("GET", f"/threads/{thread_id}", params={"format": "full"})


def get_message(message_id: str) -> dict:
    return _request("GET", f"/messages/{message_id}", params={"format": "full"})


def list_labels() -> list[dict]:
    return _request("GET", "/labels").get("labels", [])


# --------------------------------------------------------------------------
# Drafts (compose scope; no send scope exists on this client — see above)
# --------------------------------------------------------------------------

def create_draft(
    to: str, subject: str, body: str,
    thread_id: str | None = None, in_reply_to: str | None = None,
) -> dict:
    """Creates a Gmail DRAFT — never sends. `thread_id` keeps a follow-up in
    the same thread as the original send; `in_reply_to` is the Message-Id
    header of the message being replied to, for proper threading headers.

    The body is linted by the SAME rule the Gmail MCP path is guarded by
    (audit/draft_lint) — this transport has no PreToolUse hook, so the check
    is enforced here in code: a bare domain/email or an em-dash blocks the
    draft rather than shipping."""
    from audit import draft_lint
    problems = draft_lint.scan(body)
    if problems:
        raise GmailGethaythamError(
            "draft body fails the copy rules (same as the Gmail MCP link "
            "guard): " + "; ".join(problems)
        )

    mime = MIMEText(body)
    mime["to"] = to
    mime["subject"] = subject
    if in_reply_to:
        mime["In-Reply-To"] = in_reply_to
        mime["References"] = in_reply_to
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("ascii")
    message: dict[str, Any] = {"raw": raw}
    if thread_id:
        message["threadId"] = thread_id
    return _request("POST", "/drafts", json={"message": message})


def list_drafts(max_results: int = 20) -> list[dict]:
    return _request("GET", "/drafts", params={"maxResults": max_results}).get("drafts", [])
