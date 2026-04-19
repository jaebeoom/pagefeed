from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .generator import generate_from_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pagefeed")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="generate configured RSS feeds")
    generate.add_argument(
        "--config",
        default="feeds.toml",
        type=Path,
        help="path to feeds.toml",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        results = generate_from_config(args.config)
        for result in results:
            print(f"wrote {result.output_path} ({result.item_count} items)")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
