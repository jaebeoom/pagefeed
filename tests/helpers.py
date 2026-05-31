from __future__ import annotations

import re
from pathlib import Path

from pagefeed.models import FeedConfig


def make_feed_config(
    *,
    name: str = "test",
    source_url: str = "https://example.com/posts/",
    output_path: Path = Path("public/test.xml"),
    public_path: str = "/test.xml",
    title: str = "Test",
    description: str = "Test feed",
    include_href_patterns: tuple[re.Pattern[str], ...] | None = None,
    max_items: int = 50,
    min_items: int = 1,
    exclude_href_patterns: tuple[re.Pattern[str], ...] = (),
) -> FeedConfig:
    patterns = include_href_patterns
    if patterns is None:
        patterns = (re.compile(r"^/posts/.+/$"),)

    return FeedConfig(
        name=name,
        source_url=source_url,
        output_path=output_path,
        public_path=public_path,
        title=title,
        description=description,
        include_href_patterns=patterns,
        max_items=max_items,
        min_items=min_items,
        exclude_href_patterns=exclude_href_patterns,
    )
