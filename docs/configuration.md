# Configuration

`feeds.toml` contains one or more `[[feeds]]` tables.

## Feed Fields

- `name`: human-readable identifier used in error messages.
- `source_url`: public listing page to fetch.
- `output_path`: XML file written by the generator. Relative paths are resolved from the current working directory.
- `public_path`: public URL path under the deployed site. If omitted, defaults to `/<output filename>`.
- `title`: RSS channel title.
- `description`: RSS channel description.
- `include_href_patterns`: one or more regular expressions matched against both the raw anchor `href` and the resolved absolute URL.
- `exclude_href_patterns`: optional regular expressions matched after includes; matching links are skipped.
- `max_items`: optional positive integer, default `50`.
- `min_items`: optional positive integer, default `1`.

## Validation Rules

- At least one `[[feeds]]` block is required.
- Every string field must be non-empty.
- `include_href_patterns` must contain at least one valid regex.
- `exclude_href_patterns`, if provided, must contain at least one valid regex.
- `min_items` must be less than or equal to `max_items`.
- `output_path` values must be unique across feeds.
- `public_path` values must be unique across feeds.

## Environment Variables

- `PAGEFEED_BASE_URL`: optional deployment base URL used to emit the Atom self-link, for example `https://<user>.github.io/pagefeed`.
- `PAGEFEED_USER_AGENT`: optional HTTP user agent. Blank values fall back to `pagefeed/0.1`.
- `PAGEFEED_CONFIG_TOML`: GitHub Actions secret used by the workflow to materialize a private config file.
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`: optional GitHub Actions secrets for failure alerts.

## Operational Guidance

- Prefer opaque `public_path` values such as `/f-a1b2c3.xml`.
- Set `min_items` for every feed so layout changes fail fast.
- Keep feeds limited to links and metadata unless you have explicit permission to republish content.
- Use a descriptive `PAGEFEED_USER_AGENT`, ideally including the public repository URL.
