from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from pagefeed.generator import generate_from_config, validate_items
from pagefeed.models import FeedConfig, GenerateResult


class GeneratorTest(unittest.TestCase):
    def test_generate_from_config_writes_feed_and_returns_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_path = tmp_path / "public" / "nested" / "feed.xml"
            config_path = tmp_path / "feeds.toml"
            config_path.write_text(
                f"""
                [[feeds]]
                name = "test"
                source_url = "https://example.com/posts/"
                output_path = "{output_path}"
                public_path = "/nested/feed.xml"
                title = "Test Feed"
                description = "Test description"
                include_href_patterns = ["^/posts/.+/$"]
                max_items = 50
                min_items = 1
                """,
                encoding="utf-8",
            )
            html = """
            <a href="/posts/first/">
              <span>First Post</span>
              <span>2026-04-19</span>
            </a>
            """

            with (
                patch.dict(os.environ, {"PAGEFEED_BASE_URL": ""}),
                patch("pagefeed.generator.fetch_text", return_value=html),
            ):
                results = generate_from_config(config_path)

            self.assertEqual(results, [GenerateResult(output_path, 1)])
            root = ET.fromstring(output_path.read_text(encoding="utf-8"))
            self.assertEqual(root.findtext("channel/item/title"), "First Post")

    def test_validate_items_fails_when_extraction_drops_below_minimum(self) -> None:
        config = FeedConfig(
            name="test",
            source_url="https://example.com/posts/",
            output_path=Path("public/test.xml"),
            public_path="/test.xml",
            title="Test Feed",
            description="Test description",
            include_href_patterns=(),
            max_items=50,
            min_items=1,
        )

        with self.assertRaisesRegex(RuntimeError, "extracted 0 item"):
            validate_items(config, [])

    def test_generate_fails_before_overwriting_existing_feed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_path = tmp_path / "feed.xml"
            output_path.write_text("existing feed", encoding="utf-8")
            config_path = tmp_path / "feeds.toml"
            config_path.write_text(
                f"""
                [[feeds]]
                name = "test"
                source_url = "https://example.com/posts/"
                output_path = "{output_path}"
                public_path = "/feed.xml"
                title = "Test Feed"
                description = "Test description"
                include_href_patterns = ["^/posts/.+/$"]
                max_items = 50
                min_items = 1
                """,
                encoding="utf-8",
            )

            with patch("pagefeed.generator.fetch_text", return_value='<a href="/about/">About</a>'):
                with self.assertRaisesRegex(RuntimeError, "extracted 0 item"):
                    generate_from_config(config_path)

            self.assertEqual(output_path.read_text(encoding="utf-8"), "existing feed")
