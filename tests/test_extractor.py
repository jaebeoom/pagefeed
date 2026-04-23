from __future__ import annotations

import re
import unittest
from datetime import UTC, datetime
from pathlib import Path

from pagefeed.extractor import extract_items
from pagefeed.models import FeedConfig


class ExtractorTest(unittest.TestCase):
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
        self.assertEqual(items[0].url, "https://example.com/posts/2026/04/19/03/")
        self.assertEqual(items[0].published, datetime(2026, 4, 19, tzinfo=UTC))

    def test_extracts_titles_from_homepage_card_links(self) -> None:
        html = """
        <a href="/essays/2026/04/21/01/">
          <span>essays</span>
          <span>2026-04-21</span>
          <h2>About Stateless Systems</h2>
          <p>About Stateless Systems begins with a longer summary.</p>
          <span>Read more -></span>
        </a>
        """
        config = FeedConfig(
            name="test",
            source_url="https://example.com/",
            output_path=Path("public/test.xml"),
            public_path="/test.xml",
            title="Test",
            description="Test feed",
            include_href_patterns=(
                re.compile(r"^/[a-z0-9-]+/[0-9]{4}/[0-9]{2}/[0-9]{2}/[0-9]{2}/$"),
            ),
            max_items=50,
            min_items=1,
        )

        items = extract_items(html, config)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "About Stateless Systems")

    def test_invalid_date_text_does_not_abort_extraction(self) -> None:
        html = """
        <a href="/posts/2026/02/31/01/">
          <span>Impossible Date</span>
          <span>2026-02-31</span>
        </a>
        """
        config = FeedConfig(
            name="test",
            source_url="https://example.com/posts/",
            output_path=Path("public/test.xml"),
            public_path="/test.xml",
            title="Test",
            description="Test feed",
            include_href_patterns=(re.compile(r"^/posts/.+/$"),),
            max_items=50,
            min_items=1,
        )

        items = extract_items(html, config)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Impossible Date")
        self.assertIsNone(items[0].published)
