from __future__ import annotations

import re
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from pagefeed.generator import FeedConfig, build_rss, extract_items, generate_from_config, validate_items


class GeneratorTest(unittest.TestCase):
    def test_extracts_matching_post_links(self) -> None:
        html = """
        <section>
          <ul>
            <li>
              <a href="/posts/2026/04/19/03/">
                <span>Example Post</span>
                <span>2026-04-19 · #03</span>
              </a>
            </li>
            <li><a href="/about/"><span>About</span></a></li>
          </ul>
        </section>
        """
        config = FeedConfig(
            name="test",
            source_url="https://example.com/posts/",
            output_path=Path("public/test.xml"),
            public_path="/test.xml",
            title="Test",
            description="Test feed",
            include_href_patterns=(
                re.compile(r"^/posts/[0-9]{4}/[0-9]{2}/[0-9]{2}/[0-9]{2}/$"),
            ),
            max_items=50,
            min_items=1,
        )

        items = extract_items(html, config)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Example Post")
        self.assertEqual(
            items[0].url,
            "https://example.com/posts/2026/04/19/03/",
        )
        self.assertEqual(items[0].published, datetime(2026, 4, 19, tzinfo=UTC))

    def test_builds_parseable_rss(self) -> None:
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

        xml_text = build_rss(config, [], "https://example.github.io/pagefeed/test.xml")
        root = ET.fromstring(xml_text)

        self.assertEqual(root.tag, "rss")
        self.assertEqual(root.attrib["version"], "2.0")
        self.assertEqual(root.findtext("channel/title"), "Test Feed")

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


if __name__ == "__main__":
    unittest.main()
