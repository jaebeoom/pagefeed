from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from pagefeed.http import build_feed_url, resolve_user_agent
from pagefeed.models import DEFAULT_USER_AGENT


class HttpTest(unittest.TestCase):
    def test_build_feed_url_uses_explicit_base_url(self) -> None:
        self.assertEqual(
            build_feed_url("feed.xml", base_url="https://example.com/pagefeed/"),
            "https://example.com/pagefeed/feed.xml",
        )

    def test_resolve_user_agent_falls_back_when_env_is_blank(self) -> None:
        with patch.dict(os.environ, {"PAGEFEED_USER_AGENT": "   "}):
            self.assertEqual(resolve_user_agent(), DEFAULT_USER_AGENT)
