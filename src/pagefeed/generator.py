from __future__ import annotations

from pathlib import Path

from .config import load_config
from .extractor import extract_items
from .http import build_feed_url as _build_feed_url, fetch_text
from .models import FeedConfig, FeedItem, GenerateResult
from .rss import build_rss


def generate_from_config(config_path: Path) -> list[GenerateResult]:
    """Generate every configured feed and return output summaries."""
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


def validate_items(config: FeedConfig, items: list[FeedItem]) -> None:
    if len(items) < config.min_items:
        raise RuntimeError(
            f"{config.name}: extracted {len(items)} item(s), "
            f"expected at least {config.min_items}. "
            "The source page structure or link patterns may have changed."
        )


def build_feed_url(config: FeedConfig) -> str | None:
    """Build the public feed URL for compatibility with the original API."""
    return _build_feed_url(config.public_path)


__all__ = [
    "FeedConfig",
    "FeedItem",
    "GenerateResult",
    "build_feed_url",
    "build_rss",
    "extract_items",
    "fetch_text",
    "generate_from_config",
    "load_config",
    "validate_items",
]
