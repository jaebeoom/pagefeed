from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from .models import FeedConfig, FeedItem


TITLE_NOISE_LABELS = frozenset({"read more", "read more ->", "read more \u2192"})


@dataclass
class _Anchor:
    href: str
    parts: list[str]
    span_parts: list[list[str]]


class ListingParser(HTMLParser):
    """Collect anchor text so item extraction can stay independent from HTML shape."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[_Anchor] = []
        self._anchor: _Anchor | None = None
        self._span_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._anchor = _Anchor(href=href, parts=[], span_parts=[])
        elif tag == "span" and self._anchor is not None:
            self._span_depth += 1
            if self._span_depth == 1:
                self._anchor.span_parts.append([])

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self._anchor is not None and self._span_depth:
            self._span_depth -= 1
        elif tag == "a" and self._anchor is not None:
            self.anchors.append(self._anchor)
            self._anchor = None
            self._span_depth = 0

    def handle_data(self, data: str) -> None:
        if self._anchor is None:
            return

        text = " ".join(data.split())
        if not text:
            return

        self._anchor.parts.append(text)
        if self._span_depth and self._anchor.span_parts:
            self._anchor.span_parts[-1].append(text)


def extract_items(page_html: str, config: FeedConfig) -> list[FeedItem]:
    seen: set[str] = set()
    items: list[FeedItem] = []
    for anchor in parse_anchors(page_html):
        absolute_url = urljoin(config.source_url, anchor.href)
        if absolute_url in seen:
            continue
        if not anchor_matches_config(anchor, absolute_url, config):
            continue

        item = feed_item_from_anchor(anchor, absolute_url)
        if item is None:
            continue

        seen.add(absolute_url)
        items.append(item)
        if len(items) >= config.max_items:
            break

    return items


def parse_anchors(page_html: str) -> list[_Anchor]:
    parser = ListingParser()
    parser.feed(page_html)
    parser.close()
    return parser.anchors


def anchor_matches_config(anchor: _Anchor, absolute_url: str, config: FeedConfig) -> bool:
    return href_matches(
        anchor.href,
        absolute_url,
        config.include_href_patterns,
    ) and not href_matches(anchor.href, absolute_url, config.exclude_href_patterns)


def feed_item_from_anchor(anchor: _Anchor, absolute_url: str) -> FeedItem | None:
    title = extract_title(anchor)
    if not title:
        return None

    return FeedItem(
        title=title,
        url=absolute_url,
        published=extract_date(anchor),
    )


def href_matches(
    raw_href: str,
    absolute_url: str,
    patterns: Iterable[re.Pattern[str]],
) -> bool:
    return any(pattern.search(raw_href) or pattern.search(absolute_url) for pattern in patterns)


def extract_title(anchor: _Anchor) -> str:
    category_labels = category_label_candidates(anchor.href)
    for candidate in iter_title_candidates(anchor):
        if candidate and not is_title_noise(candidate, category_labels):
            return candidate
    return ""


def iter_title_candidates(anchor: _Anchor) -> Iterator[str]:
    for span_parts in anchor.span_parts:
        yield clean_title_text(" ".join(span_parts))

    for part in anchor.parts:
        yield clean_title_text(part)

    yield clean_title_text(" ".join(anchor.parts).strip())


def clean_title_text(text: str) -> str:
    normalized = " ".join(text.split()).strip()
    return re.sub(r"\s*[0-9]{4}-[0-9]{2}-[0-9]{2}.*$", "", normalized).strip()


def is_title_noise(text: str, category_labels: set[str]) -> bool:
    normalized = normalize_label(text)
    return normalized in category_labels or normalized in TITLE_NOISE_LABELS


def category_label_candidates(href: str) -> set[str]:
    path = urlparse(href).path
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        return set()

    category = segments[0]
    labels = {normalize_label(category), normalize_label(category.replace("-", " "))}
    if category.endswith("s"):
        labels.add(normalize_label(category[:-1]))
    return labels


def normalize_label(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def extract_date(anchor: _Anchor) -> datetime | None:
    text = " ".join(anchor.parts)
    match = re.search(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", text)
    if not match:
        return None

    year, month, day = (int(part) for part in match.groups())
    try:
        return datetime(year, month, day, tzinfo=UTC)
    except ValueError:
        return None
