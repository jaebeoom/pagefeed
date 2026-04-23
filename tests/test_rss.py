from __future__ import annotations

import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from pagefeed.models import FeedConfig
from pagefeed.rss import build_rss


class RssTest(unittest.TestCase):
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
