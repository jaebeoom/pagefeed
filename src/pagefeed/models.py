from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_USER_AGENT = "pagefeed/0.1"
ATOM_NS = "http://www.w3.org/2005/Atom"


@dataclass(frozen=True)
class FeedConfig:
    name: str
    source_url: str
    output_path: Path
    public_path: str
    title: str
    description: str
    include_href_patterns: tuple[re.Pattern[str], ...]
    max_items: int
    min_items: int


@dataclass(frozen=True)
class FeedItem:
    title: str
    url: str
    published: datetime | None


@dataclass(frozen=True)
class GenerateResult:
    output_path: Path
    item_count: int
