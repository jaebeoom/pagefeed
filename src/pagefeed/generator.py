from __future__ import annotations

import email.utils
import html
import os
import re
import tomllib
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET


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


@dataclass
class _Anchor:
    href: str
    parts: list[str]
    span_parts: list[list[str]]


class ListingParser(HTMLParser):
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


def generate_from_config(config_path: Path) -> list[GenerateResult]:
    configs = load_config(config_path)
    results: list[GenerateResult] = []

    for config in configs:
        page_html = fetch_text(config.source_url)
        items = extract_items(page_html, config)
        validate_items(config, items)
        feed_url = build_feed_url(config)
        xml_text = build_rss(config, items, feed_url)
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        config.output_path.write_text(xml_text, encoding="utf-8")
        results.append(GenerateResult(config.output_path, len(items)))

    return results


def load_config(config_path: Path) -> list[FeedConfig]:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    feeds = data.get("feeds")
    if not isinstance(feeds, list) or not feeds:
        raise ValueError("config must contain at least one [[feeds]] entry")

    configs: list[FeedConfig] = []
    for raw_feed in feeds:
        patterns = tuple(re.compile(pattern) for pattern in raw_feed["include_href_patterns"])
        configs.append(
            FeedConfig(
                name=raw_feed["name"],
                source_url=raw_feed["source_url"],
                output_path=Path(raw_feed["output_path"]),
                public_path=raw_feed.get("public_path", "/" + Path(raw_feed["output_path"]).name),
                title=raw_feed["title"],
                description=raw_feed["description"],
                include_href_patterns=patterns,
                max_items=int(raw_feed.get("max_items", 50)),
                min_items=int(raw_feed.get("min_items", 1)),
            )
        )

    return configs


def fetch_text(url: str) -> str:
    user_agent = os.environ.get("PAGEFEED_USER_AGENT", DEFAULT_USER_AGENT).strip()
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_items(page_html: str, config: FeedConfig) -> list[FeedItem]:
    parser = ListingParser()
    parser.feed(page_html)

    seen: set[str] = set()
    items: list[FeedItem] = []
    for anchor in parser.anchors:
        absolute_url = urljoin(config.source_url, anchor.href)
        if absolute_url in seen:
            continue
        if not href_matches(anchor.href, absolute_url, config.include_href_patterns):
            continue

        title = extract_title(anchor)
        if not title:
            continue

        seen.add(absolute_url)
        items.append(
            FeedItem(
                title=title,
                url=absolute_url,
                published=extract_date(anchor),
            )
        )

        if len(items) >= config.max_items:
            break

    return items


def validate_items(config: FeedConfig, items: list[FeedItem]) -> None:
    if len(items) < config.min_items:
        raise RuntimeError(
            f"{config.name}: extracted {len(items)} item(s), "
            f"expected at least {config.min_items}. "
            "The source page structure or link patterns may have changed."
        )


def href_matches(
    raw_href: str,
    absolute_url: str,
    patterns: Iterable[re.Pattern[str]],
) -> bool:
    return any(pattern.search(raw_href) or pattern.search(absolute_url) for pattern in patterns)


def extract_title(anchor: _Anchor) -> str:
    category_labels = category_label_candidates(anchor.href)

    for span_parts in anchor.span_parts:
        span_text = clean_title_text(" ".join(span_parts))
        if span_text and not is_title_noise(span_text, category_labels):
            return span_text

    for part in anchor.parts:
        part_text = clean_title_text(part)
        if part_text and not is_title_noise(part_text, category_labels):
            return part_text

    text = " ".join(anchor.parts).strip()
    return clean_title_text(text)


def clean_title_text(text: str) -> str:
    normalized = " ".join(text.split()).strip()
    return re.sub(r"\s*[0-9]{4}-[0-9]{2}-[0-9]{2}.*$", "", normalized).strip()


def is_title_noise(text: str, category_labels: set[str]) -> bool:
    normalized = normalize_label(text)
    return normalized in category_labels or normalized in {"read more", "read more ->", "read more \u2192"}


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
    return datetime.combine(date(year, month, day), time.min, tzinfo=UTC)


def build_feed_url(config: FeedConfig) -> str | None:
    base_url = os.environ.get("PAGEFEED_BASE_URL", "").strip().rstrip("/")
    if not base_url:
        return None
    return base_url + config.public_path


def build_rss(config: FeedConfig, items: list[FeedItem], feed_url: str | None) -> str:
    ET.register_namespace("atom", ATOM_NS)
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = config.title
    ET.SubElement(channel, "link").text = config.source_url
    ET.SubElement(channel, "description").text = config.description
    ET.SubElement(channel, "lastBuildDate").text = format_rfc822(datetime.now(tz=UTC))

    if feed_url:
        ET.SubElement(channel, f"{{{ATOM_NS}}}link", {
            "href": feed_url,
            "rel": "self",
            "type": "application/rss+xml",
        })

    for item in items:
        element = ET.SubElement(channel, "item")
        ET.SubElement(element, "title").text = html.unescape(item.title)
        ET.SubElement(element, "link").text = item.url
        ET.SubElement(element, "guid", isPermaLink="true").text = item.url
        if item.published:
            ET.SubElement(element, "pubDate").text = format_rfc822(item.published)

    ET.indent(rss, space="  ")
    return ET.tostring(rss, encoding="unicode", xml_declaration=True)


def format_rfc822(value: datetime) -> str:
    return email.utils.format_datetime(value)
