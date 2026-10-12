"""Kite Connect authentication state — OS keyring only (P3, roadmap 3.2).

Hard rule (SPEC): the Kite ``access_token`` and ``KITE_API_SECRET`` live in
the OS keyring ONLY — never in .env, never in the DB, never in git. The only
Kite value allowed in ``.env`` is the non-secret ``KITE_API_KEY``.

Keyring layout (service ``bazzar-terminal``):
  * ``kite_api_secret``   — app secret from developers.kite.trade
  * ``kite_access_token`` — daily access token from generate_session()
  * ``kite_session_meta`` — JSON: user id/name + login timestamp (non-secret)

CLI:
    python -m backend.kite_auth set-secret   # prompt for KITE_API_SECRET
    python -m backend.kite_auth status       # show config/auth state (no secrets)
    python -m backend.kite_auth logout       # clear the session (keeps the secret)
"""

from __future__ import annotations

import argparse
import datetime as dt
import getpass
import json
import sys
from typing import Any

import keyring
from keyring.errors import KeyringError

from .providers.base import ProviderError
from .providers.kite import KiteAuthRequired

SERVICE_NAME = "bazzar-terminal"
KEY_API_SECRET = "kite_api_secret"
KEY_ACCESS_TOKEN = "kite_access_token"
KEY_SESSION_META = "kite_session_meta"


class KeyringUnavailable(ProviderError):
    """The OS keyring backend is missing/unusable on this machine."""


def _set(key: str, value: str) -> None:
    try:
        keyring.set_password(SERVICE_NAME, key, value)
    except KeyringError as exc:
        raise KeyringUnavailable(f"OS keyring unavailable: {exc}") from exc


def _get(key: str) -> str | None:
    try:
        return keyring.get_password(SERVICE_NAME, key)
    except KeyringError as exc:
        raise KeyringUnavailable(f"OS keyring unavailable: {exc}") from exc


def _delete(key: str) -> None:
    try:
        keyring.delete_password(SERVICE_NAME, key)
    except keyring.errors.PasswordDeleteError:
        pass
    except KeyringError as exc:
        raise KeyringUnavailable(f"OS keyring unavailable: {exc}") from exc


# --- secret (long-lived, user enters once) ------------------------------------


def store_api_secret(secret: str) -> None:
    if not secret.strip():
        raise ProviderError("refusing to store an empty KITE_API_SECRET")
    _set(KEY_API_SECRET, secret.strip())


def get_api_secret() -> str | None:
    return _get(KEY_API_SECRET)


# --- session (daily) ------------------------------------------------------------


def store_session(access_token: str, meta: dict[str, Any] | None = None) -> None:
    if not access_token.strip():
        raise ProviderError("refusing to store an empty access token")
    _set(KEY_ACCESS_TOKEN, access_token.strip())
    payload = dict(meta or {})
    payload["login_time"] = dt.datetime.now(dt.UTC).isoformat()
    _set(KEY_SESSION_META, json.dumps(payload))


def get_access_token() -> str | None:
    return _get(KEY_ACCESS_TOKEN)


def get_session_meta() -> dict[str, Any]:
    raw = _get(KEY_SESSION_META)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def clear_session() -> None:
    """Drop the access token + session meta; the API secret is kept."""
    _delete(KEY_ACCESS_TOKEN)
    _delete(KEY_SESSION_META)


# --- status + login exchange -----------------------------------------------------


def auth_status(api_key: str = "") -> dict[str, Any]:
    """Non-secret auth state for the API/UI. NEVER includes tokens/secret."""
    meta = get_session_meta()
    return {
        "configured": bool(api_key) and get_api_secret() is not None,
        "api_key_set": bool(api_key),
        "authenticated": get_access_token() is not None,
        "user": meta.get("user_id") or meta.get("user_name"),
        "login_time": meta.get("login_time"),
        "expires_hint": "Kite access tokens expire daily (next trading morning).",
    }


def exchange_request_token(
    api_key: str,
    request_token: str,
    *,
    client: Any | None = None,
) -> dict[str, Any]:
    """Exchange the redirect ``request_token`` for an access token and store
    the session in the OS keyring. Returns non-secret user metadata."""
    secret = get_api_secret()
    if not secret:
        raise KiteAuthRequired(
            "KITE_API_SECRET not in the OS keyring — run "
            "`python -m backend.kite_auth set-secret` first."
        )
    if client is None:
        from kiteconnect import KiteConnect

        client = KiteConnect(api_key=api_key)
    try:
        session = client.generate_session(request_token, api_secret=secret)
    except Exception as exc:
        raise ProviderError(f"Kite session exchange failed: {exc}") from exc
    store_session(
        session["access_token"],
        {"user_id": session.get("user_id"), "user_name": session.get("user_name")},
    )
    return {"user_id": session.get("user_id"), "user_name": session.get("user_name")}


# --- CLI ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m backend.kite_auth")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("set-secret", help="store KITE_API_SECRET in the OS keyring")
    sub.add_parser("status", help="show non-secret auth state")
    sub.add_parser("logout", help="clear the session (keeps the API secret)")
    args = parser.parse_args(argv)

    if args.command == "set-secret":
        secret = getpass.getpass("KITE_API_SECRET (input hidden): ")
        store_api_secret(secret)
        print("Stored KITE_API_SECRET in the OS keyring.")
        return 0
    if args.command == "status":
        from .settings import get_settings

        print(json.dumps(auth_status(get_settings().kite_api_key), indent=2))
        return 0
    if args.command == "logout":
        clear_session()
        print("Cleared the Kite session (API secret kept).")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
