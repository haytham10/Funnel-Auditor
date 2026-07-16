#!/usr/bin/env python3
"""
One-time local OAuth authorization for haytham@gethaytham.com's Gmail API
access — mints the refresh token audit/gmail_gethaytham.py needs.

MUST run on a machine with a real, interactive browser (your laptop). This
cannot run inside a Claude Code cloud session — there's no browser there to
complete the consent screen.

Usage:
    python scripts/gethaytham_gmail_auth.py

You'll be asked for the Desktop OAuth client's Client ID and Secret — from
the SAME Google Cloud project as the Gmail MCP connector client
(gethaytham-mcp), but a SECOND client, type "Desktop app" (see
audit/gmail_gethaytham.py's module docstring for the full one-time setup).
A browser tab opens for you to sign in and approve as
haytham@gethaytham.com. On success this prints three lines — set them as
environment secrets on the runner, never commit them anywhere:

    GETHAYTHAM_GMAIL_CLIENT_ID
    GETHAYTHAM_GMAIL_CLIENT_SECRET
    GETHAYTHAM_GMAIL_REFRESH_TOKEN
"""

from __future__ import annotations

import getpass
import http.server
import urllib.parse
import webbrowser

import requests

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = (
    "https://www.googleapis.com/auth/gmail.readonly "
    "https://www.googleapis.com/auth/gmail.compose"
)


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    code: str | None = None

    def do_GET(self) -> None:  # noqa: N802 — http.server's required method name
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _CallbackHandler.code = params.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<html><body>Authorized. You can close this tab and return "
            b"to the terminal.</body></html>"
        )

    def log_message(self, *args) -> None:  # silence default request logging
        pass


def main() -> None:
    print("Second OAuth client for haytham@gethaytham.com — Desktop app type,")
    print("same Google Cloud project as the Gmail MCP connector (gethaytham-mcp).\n")
    client_id = input("Client ID: ").strip()
    client_secret = getpass.getpass("Client Secret (input hidden): ").strip()
    if not client_id or not client_secret:
        print("Both fields are required.")
        raise SystemExit(1)

    server = http.server.HTTPServer(("localhost", 0), _CallbackHandler)
    port = server.server_address[1]
    redirect_uri = f"http://localhost:{port}"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "login_hint": "haytham@gethaytham.com",
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    print("\nOpening a browser tab — sign in and approve as haytham@gethaytham.com.")
    print(f"If it doesn't open automatically, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    server.handle_request()  # blocks until the one redirect request lands
    code = _CallbackHandler.code
    if not code:
        print("No authorization code received — did the consent screen get cancelled?")
        raise SystemExit(1)

    resp = requests.post(TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }, timeout=30)
    if not resp.ok:
        print(f"Token exchange failed: {resp.status_code} {resp.text[:300]}")
        raise SystemExit(1)

    data = resp.json()
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        print(
            "No refresh_token in the response — Google only issues one on the "
            "FIRST consent for a given client+account (this script already "
            "sets prompt=consent to force re-issue, so this is unexpected). "
            "If you've run this before, revoke the app's access at "
            "https://myaccount.google.com/permissions and run this again."
        )
        raise SystemExit(1)

    print("\nSuccess. Set these as environment secrets on the runner (never in code):\n")
    print(f"  GETHAYTHAM_GMAIL_CLIENT_ID={client_id}")
    print(f"  GETHAYTHAM_GMAIL_CLIENT_SECRET={client_secret}")
    print(f"  GETHAYTHAM_GMAIL_REFRESH_TOKEN={refresh_token}")


if __name__ == "__main__":
    main()
