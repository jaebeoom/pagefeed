# Architecture

`pagefeed` keeps the runtime small on purpose. The generator uses only the Python standard library and treats HTML extraction as a best-effort pass over public listing pages.

## Execution Flow

1. `pagefeed.__main__` parses the `generate` command and forwards the config path.
2. `pagefeed.config` reads `feeds.toml`, validates each `[[feeds]]` block, and produces typed `FeedConfig` objects.
3. `pagefeed.http` fetches the listing HTML with the configured user agent and builds the optional public feed URL.
4. `pagefeed.extractor` scans anchor tags, filters links through regex patterns, derives titles, and extracts simple `YYYY-MM-DD` dates when available.
5. `pagefeed.rss` renders RSS 2.0 XML with an Atom self-link when `PAGEFEED_BASE_URL` is set.
6. `pagefeed.generator` orchestrates the end-to-end write and preserves the previous XML when extraction fails validation.

## Module Layout

- `src/pagefeed/models.py`: shared dataclasses and package constants.
- `src/pagefeed/config.py`: TOML parsing, field validation, duplicate-path checks.
- `src/pagefeed/http.py`: HTTP fetch logic and environment-driven URL helpers.
- `src/pagefeed/extractor.py`: HTML parsing and item extraction heuristics.
- `src/pagefeed/rss.py`: XML rendering.
- `src/pagefeed/generator.py`: compatibility facade plus orchestration entrypoint.

## Invariants

- Runtime dependencies stay in the standard library.
- Tests do not hit the network.
- A feed is written only after extraction meets `min_items`.
- `output_path` and `public_path` must be unique across feeds.
- `public_path` is normalized to start with `/` so public URLs stay predictable.

## Extension Notes

- Prefer adding extraction heuristics in `extractor.py` before introducing heavier HTML dependencies.
- Keep config validation strict. Failing early on malformed TOML is better than silently generating broken XML.
- If a new CLI command is added, keep `pagefeed.generator` stable so tests and external imports do not need to follow internal refactors.
