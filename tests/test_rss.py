from __future__ import annotations

import unittest
from xml.etree import ElementTree as ET

from helpers import make_feed_config
from pagefeed.rss import build_rss


class RssTest(unittest.TestCase):
    def test_builds_parseable_rss(self) -> None:
        config = make_feed_config(
            title="Test Feed",
            description="Test description",
            include_href_patterns=(),
        )

        xml_text = build_rss(config, [], "https://example.github.io/pagefeed/test.xml")
        root = ET.fromstring(xml_text)

        self.assertEqual(root.tag, "rss")
        self.assertEqual(root.attrib["version"], "2.0")
        self.assertEqual(root.findtext("channel/title"), "Test Feed")
