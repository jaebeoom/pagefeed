from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pagefeed.config import load_config


class ConfigTest(unittest.TestCase):
    def test_load_config_normalizes_public_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "feeds.toml"
            config_path.write_text(
                """
                [[feeds]]
                name = "test"
                source_url = "https://example.com/posts/"
                output_path = "public/test.xml"
                public_path = "test.xml"
                title = "Test Feed"
                description = "Test description"
                include_href_patterns = ["^/posts/.+/$"]
                """,
                encoding="utf-8",
            )

            [config] = load_config(config_path)

        self.assertEqual(config.public_path, "/test.xml")

    def test_load_config_compiles_optional_exclude_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "feeds.toml"
            config_path.write_text(
                """
                [[feeds]]
                name = "test"
                source_url = "https://example.com/"
                output_path = "public/test.xml"
                title = "Test Feed"
                description = "Test description"
                include_href_patterns = ["^/[a-z0-9-]+/.+/$"]
                exclude_href_patterns = ["^/art-gallery/"]
                """,
                encoding="utf-8",
            )

            [config] = load_config(config_path)

        self.assertEqual(len(config.exclude_href_patterns), 1)
        self.assertTrue(config.exclude_href_patterns[0].search("/art-gallery/2026/05/30/01/"))

    def test_load_config_rejects_invalid_exclude_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "feeds.toml"
            config_path.write_text(
                """
                [[feeds]]
                name = "test"
                source_url = "https://example.com/"
                output_path = "public/test.xml"
                title = "Test Feed"
                description = "Test description"
                include_href_patterns = ["^/[a-z0-9-]+/.+/$"]
                exclude_href_patterns = ["["]
                """,
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "exclude_href_patterns\\[1\\]"):
                load_config(config_path)

    def test_load_config_rejects_invalid_min_max_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "feeds.toml"
            config_path.write_text(
                """
                [[feeds]]
                name = "test"
                source_url = "https://example.com/posts/"
                output_path = "public/test.xml"
                title = "Test Feed"
                description = "Test description"
                include_href_patterns = ["^/posts/.+/$"]
                min_items = 5
                max_items = 3
                """,
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "min_items must be less than or equal to max_items"):
                load_config(config_path)

    def test_load_config_rejects_duplicate_output_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "feeds.toml"
            config_path.write_text(
                """
                [[feeds]]
                name = "first"
                source_url = "https://example.com/posts/"
                output_path = "public/test.xml"
                title = "First"
                description = "First feed"
                include_href_patterns = ["^/posts/.+/$"]

                [[feeds]]
                name = "second"
                source_url = "https://example.com/notes/"
                output_path = "public/test.xml"
                title = "Second"
                description = "Second feed"
                include_href_patterns = ["^/notes/.+/$"]
                """,
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "output_path must be unique"):
                load_config(config_path)
