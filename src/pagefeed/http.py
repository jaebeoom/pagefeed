from __future__ import annotations

import os
import urllib.request

from .models import DEFAULT_USER_AGENT


def fetch_text(url: str, *, timeout: int = 30) -> str:
    """Fetch HTML text using the configured user agent."""
    request = urllib.request.Request(url, headers={"User-Agent": resolve_user_agent()})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def build_feed_url(public_path: str, *, base_url: str | None = None) -> str | None:
    """Build the public feed URL used for the Atom self-link."""
    resolved_base_url = (
        base_url if base_url is not None else os.environ.get("PAGEFEED_BASE_URL", "")
    ).strip().rstrip("/")
    if not resolved_base_url:
        return None

    normalized_public_path = public_path if public_path.startswith("/") else "/" + public_path
    return resolved_base_url + normalized_public_path


def resolve_user_agent() -> str:
    configured_user_agent = os.environ.get("PAGEFEED_USER_AGENT", "").strip()
    return configured_user_agent or DEFAULT_USER_AGENT
