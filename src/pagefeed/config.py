from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .models import FeedConfig


def load_config(config_path: Path) -> list[FeedConfig]:
    """Load and validate feed configuration from a TOML file."""
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    feeds = data.get("feeds")
    if not isinstance(feeds, list) or not feeds:
        raise ValueError("config must contain at least one [[feeds]] entry")

    configs: list[FeedConfig] = []
    seen_output_paths: set[Path] = set()
    seen_public_paths: set[str] = set()
    for index, raw_feed in enumerate(feeds, start=1):
        section = f"feeds[{index}]"
        if not isinstance(raw_feed, Mapping):
            raise ValueError(f"{section} must be a TOML table")

        output_path = Path(_require_string(raw_feed, "output_path", section))
        config = FeedConfig(
            name=_require_string(raw_feed, "name", section),
            source_url=_require_string(raw_feed, "source_url", section),
            output_path=output_path,
            public_path=_normalize_public_path(
                _optional_string(raw_feed, "public_path", section) or f"/{output_path.name}"
            ),
            title=_require_string(raw_feed, "title", section),
            description=_require_string(raw_feed, "description", section),
            include_href_patterns=_compile_include_patterns(raw_feed, section),
            max_items=_parse_positive_int(raw_feed, "max_items", section, default=50),
            min_items=_parse_positive_int(raw_feed, "min_items", section, default=1),
            exclude_href_patterns=_compile_optional_patterns(
                raw_feed, "exclude_href_patterns", section
            ),
        )
        _validate_unique_paths(config, section, seen_output_paths, seen_public_paths)
        if config.min_items > config.max_items:
            raise ValueError(f"{section}.min_items must be less than or equal to max_items")

        configs.append(config)

    return configs


def _require_string(raw_feed: Mapping[str, Any], key: str, section: str) -> str:
    value = raw_feed.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{section}.{key} must be a non-empty string")
    return value.strip()


def _optional_string(raw_feed: Mapping[str, Any], key: str, section: str) -> str | None:
    value = raw_feed.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{section}.{key} must be a non-empty string when provided")
    return value.strip()


def _compile_include_patterns(
    raw_feed: Mapping[str, Any], section: str
) -> tuple[re.Pattern[str], ...]:
    return _compile_patterns(raw_feed, "include_href_patterns", section, required=True)


def _compile_optional_patterns(
    raw_feed: Mapping[str, Any], key: str, section: str
) -> tuple[re.Pattern[str], ...]:
    return _compile_patterns(raw_feed, key, section, required=False)


def _compile_patterns(
    raw_feed: Mapping[str, Any],
    key: str,
    section: str,
    *,
    required: bool,
) -> tuple[re.Pattern[str], ...]:
    raw_patterns = raw_feed.get(key)
    if raw_patterns is None and not required:
        return ()
    if not isinstance(raw_patterns, list) or not raw_patterns:
        suffix = "" if required else " when provided"
        raise ValueError(f"{section}.{key} must contain at least one regex pattern{suffix}")

    patterns: list[re.Pattern[str]] = []
    for index, raw_pattern in enumerate(raw_patterns, start=1):
        if not isinstance(raw_pattern, str) or not raw_pattern.strip():
            raise ValueError(f"{section}.{key}[{index}] must be a non-empty string")
        try:
            patterns.append(re.compile(raw_pattern))
        except re.error as exc:
            raise ValueError(f"{section}.{key}[{index}] is not a valid regex: {exc}") from exc

    return tuple(patterns)


def _parse_positive_int(
    raw_feed: Mapping[str, Any],
    key: str,
    section: str,
    *,
    default: int,
) -> int:
    value = raw_feed.get(key, default)
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{section}.{key} must be a positive integer")
    return value


def _normalize_public_path(public_path: str) -> str:
    if public_path.startswith("/"):
        return public_path
    return "/" + public_path


def _validate_unique_paths(
    config: FeedConfig,
    section: str,
    seen_output_paths: set[Path],
    seen_public_paths: set[str],
) -> None:
    if config.output_path in seen_output_paths:
        raise ValueError(f"{section}.output_path must be unique across feeds")
    if config.public_path in seen_public_paths:
        raise ValueError(f"{section}.public_path must be unique across feeds")

    seen_output_paths.add(config.output_path)
    seen_public_paths.add(config.public_path)
