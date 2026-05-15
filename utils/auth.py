"""Google Authentication Platform helpers for the Streamlit app."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st
from streamlit_google_auth import Authenticate


_CONFIG_HELP = """
Configure Google sign-in with one of the following options:

1. Set `GOOGLE_CLIENT_SECRETS_FILE` to a Google OAuth client JSON file path, or
2. Set `GOOGLE_CLIENT_CONFIG_JSON` to the same JSON content, or
3. Add `google_oauth.client_id`, `google_oauth.client_secret`, and
   `google_oauth.redirect_uri` to Streamlit secrets.

Also set a strong `GOOGLE_AUTH_COOKIE_KEY` (or `google_oauth.cookie_key`) for
sign-in cookie signing. Optional access controls are available through
`GOOGLE_AUTH_ALLOWED_EMAILS` and `GOOGLE_AUTH_ALLOWED_DOMAINS`.
""".strip()

_DEFAULT_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
_DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"
_DEFAULT_COOKIE_NAME = "is_steel_design_google_auth"


@dataclass(frozen=True)
class GoogleAuthConfig:
    """Runtime configuration required to initialize Google OAuth login."""

    client_secrets_path: str
    redirect_uri: str
    cookie_name: str
    cookie_key: str
    cookie_expiry_days: float
    allowed_emails: frozenset[str]
    allowed_domains: frozenset[str]


def _secret_value(*keys: str) -> Any | None:
    """Return the first non-empty Streamlit secret from top-level or google_oauth."""
    try:
        secrets = st.secrets
    except Exception:
        return None

    for key in keys:
        try:
            value = secrets.get(key)
        except Exception:
            value = None
        if value:
            return value

    try:
        google_oauth = secrets.get("google_oauth", {})
    except Exception:
        google_oauth = {}

    if google_oauth:
        for key in keys:
            try:
                value = google_oauth.get(key)
            except Exception:
                value = None
            if value:
                return value

    return None


def _configured_value(env_key: str, *secret_keys: str) -> str | None:
    """Read a config value from the environment first, then Streamlit secrets."""
    value = os.getenv(env_key)
    if value:
        return value

    secret = _secret_value(*secret_keys)
    if secret:
        return str(secret)

    return None


def _split_csv(value: str | None) -> frozenset[str]:
    """Parse comma-separated config values into a normalized set."""
    if not value:
        return frozenset()

    return frozenset(part.strip().lower() for part in value.split(",") if part.strip())


def _coerce_float(value: str | None, default: float) -> float:
    """Safely coerce a user-provided float config value."""
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _client_config_from_parts(client_id: str, client_secret: str, redirect_uri: str) -> dict[str, Any]:
    """Build a Google OAuth client-secrets document from individual settings."""
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": _DEFAULT_AUTH_URI,
            "token_uri": _DEFAULT_TOKEN_URI,
            "redirect_uris": [redirect_uri],
        }
    }


def _write_temp_client_config(config: dict[str, Any]) -> str:
    """Write generated Google client config to a deterministic temp file."""
    serialized = json.dumps(config, sort_keys=True)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
    path = Path(tempfile.gettempdir()) / f"is_steel_google_oauth_{digest}.json"
    path.write_text(serialized, encoding="utf-8")
    return str(path)


def _client_secrets_path(redirect_uri: str | None) -> str | None:
    """Resolve the Google OAuth client-secrets file path."""
    path = _configured_value(
        "GOOGLE_CLIENT_SECRETS_FILE",
        "GOOGLE_CLIENT_SECRETS_FILE",
        "google_client_secrets_file",
        "client_secrets_file",
    )
    if path:
        return path

    raw_json = _configured_value(
        "GOOGLE_CLIENT_CONFIG_JSON",
        "GOOGLE_CLIENT_CONFIG_JSON",
        "google_client_config_json",
        "client_config_json",
        "credentials_json",
    )
    if raw_json:
        try:
            return _write_temp_client_config(json.loads(raw_json))
        except json.JSONDecodeError:
            return None

    client_id = _configured_value("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID", "client_id")
    client_secret = _configured_value(
        "GOOGLE_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET", "client_secret"
    )
    if client_id and client_secret and redirect_uri:
        return _write_temp_client_config(
            _client_config_from_parts(client_id, client_secret, redirect_uri)
        )

    return None


def _google_auth_config() -> GoogleAuthConfig | None:
    """Return the configured Google OAuth settings, if all required values exist."""
    redirect_uri = _configured_value(
        "GOOGLE_REDIRECT_URI", "GOOGLE_REDIRECT_URI", "google_redirect_uri", "redirect_uri"
    )
    client_secrets_path = _client_secrets_path(redirect_uri)
    cookie_key = _configured_value(
        "GOOGLE_AUTH_COOKIE_KEY",
        "GOOGLE_AUTH_COOKIE_KEY",
        "google_auth_cookie_key",
        "cookie_key",
    )

    if not (redirect_uri and client_secrets_path and cookie_key):
        return None

    cookie_name = _configured_value(
        "GOOGLE_AUTH_COOKIE_NAME",
        "GOOGLE_AUTH_COOKIE_NAME",
        "google_auth_cookie_name",
        "cookie_name",
    ) or _DEFAULT_COOKIE_NAME
    cookie_expiry_days = _coerce_float(
        _configured_value(
            "GOOGLE_AUTH_COOKIE_EXPIRY_DAYS",
            "GOOGLE_AUTH_COOKIE_EXPIRY_DAYS",
            "google_auth_cookie_expiry_days",
            "cookie_expiry_days",
        ),
        30.0,
    )

    return GoogleAuthConfig(
        client_secrets_path=client_secrets_path,
        redirect_uri=redirect_uri,
        cookie_name=cookie_name,
        cookie_key=cookie_key,
        cookie_expiry_days=cookie_expiry_days,
        allowed_emails=_split_csv(
            _configured_value(
                "GOOGLE_AUTH_ALLOWED_EMAILS",
                "GOOGLE_AUTH_ALLOWED_EMAILS",
                "google_auth_allowed_emails",
                "allowed_emails",
            )
        ),
        allowed_domains=_split_csv(
            _configured_value(
                "GOOGLE_AUTH_ALLOWED_DOMAINS",
                "GOOGLE_AUTH_ALLOWED_DOMAINS",
                "google_auth_allowed_domains",
                "allowed_domains",
            )
        ),
    )


def _is_authorized_user(user_info: dict[str, Any], config: GoogleAuthConfig) -> bool:
    """Check optional email/domain allow-list restrictions."""
    email = str(user_info.get("email", "")).lower()
    if not email:
        return False

    if config.allowed_emails and email not in config.allowed_emails:
        return False

    if config.allowed_domains:
        domain = email.rsplit("@", maxsplit=1)[-1] if "@" in email else ""
        if domain not in config.allowed_domains:
            return False

    return True


def _render_sidebar_user(user_info: dict[str, Any], authenticator: Authenticate) -> None:
    """Render signed-in user information and logout action in the sidebar."""
    name = user_info.get("name") or "Google user"
    email = user_info.get("email") or ""
    picture = user_info.get("picture")

    with st.sidebar:
        st.markdown("### Signed in")
        if picture:
            st.image(picture, width=48)
        st.caption(f"**{name}**")
        if email:
            st.caption(email)
        if st.button("Log out", use_container_width=True):
            authenticator.logout()
            st.rerun()


def require_google_auth() -> None:
    """Stop the page until the visitor signs in with Google."""
    config = _google_auth_config()
    if not config:
        st.error("Google sign-in is not configured.")
        st.info(_CONFIG_HELP)
        st.stop()

    authenticator = Authenticate(
        secret_credentials_path=config.client_secrets_path,
        redirect_uri=config.redirect_uri,
        cookie_name=config.cookie_name,
        cookie_key=config.cookie_key,
        cookie_expiry_days=config.cookie_expiry_days,
    )
    authenticator.check_authentification()

    if st.session_state.get("connected"):
        user_info = st.session_state.get("user_info") or {}
        if _is_authorized_user(user_info, config):
            _render_sidebar_user(user_info, authenticator)
            return

        authenticator.logout()
        st.error("Your Google account is not authorized to access this application.")
        st.stop()

    st.title("🔐 Sign in required")
    st.caption("Use your Google account to access the IS Steel Design Suite.")
    authenticator.login(color="blue", justify_content="left")
    st.stop()


# Backward-compatible import name for pages that have not yet been updated.
require_password = require_google_auth
