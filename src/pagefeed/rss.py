from __future__ import annotations

import email.utils
import html
from collections.abc import Sequence
from datetime import UTC, datetime
from xml.etree import ElementTree as ET

from .models import ATOM_NS, FeedConfig, FeedItem


def build_rss(config: FeedConfig, items: Sequence[FeedItem], feed_url: str | None) -> str:
    """Render feed items as RSS 2.0 XML."""
    ET.register_namespace("atom", ATOM_NS)
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = config.title
    ET.SubElement(channel, "link").text = config.source_url
    ET.SubElement(channel, "description").text = config.description
    ET.SubElement(channel, "lastBuildDate").text = format_rfc822(datetime.now(tz=UTC))

    if feed_url:
        ET.SubElement(
            channel,
            f"{{{ATOM_NS}}}link",
            {
                "href": feed_url,
                "rel": "self",
                "type": "application/rss+xml",
            },
        )

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
