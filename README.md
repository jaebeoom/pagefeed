# pagefeed

`pagefeed` generates static RSS feeds from simple public listing pages. Configuration can stay local or live in a GitHub Actions secret, while GitHub Pages serves the resulting XML from `public/`.

The project intentionally stays small: standard-library runtime only, regex-based link selection, and no live service to operate. Generated feeds should remain unofficial and point back to the original source.

## Quick Start

1. Copy `feeds.example.toml` to `feeds.toml` and edit it for your sources.
2. Run the generator locally.
3. Push the repository and let GitHub Actions publish `public/` to Pages.

Local generation:

```text
PYTHONPATH=src python3 -m pagefeed generate --config feeds.toml
```

Local tests:

```text
PYTHONPATH=src python3 -m unittest discover -s tests
```

If you want Atom self-links in the output:

```text
PAGEFEED_BASE_URL=https://<github-username>.github.io/pagefeed \
PYTHONPATH=src python3 -m pagefeed generate --config feeds.toml
```

If you want a custom user agent:

```text
PAGEFEED_USER_AGENT='pagefeed/0.1 (+https://github.com/<github-username>/pagefeed)' \
PYTHONPATH=src python3 -m pagefeed generate --config feeds.toml
```

## Deployment

Create a GitHub repository, push this project, then configure:

- `PAGEFEED_CONFIG_TOML`: required if you do not commit `feeds.toml`
- `TELEGRAM_BOT_TOKEN`: optional failure alert token
- `TELEGRAM_CHAT_ID`: optional failure alert destination

Enable Pages with `GitHub Actions` as the source, then run the `Update feeds` workflow once manually. After the workflow succeeds, each feed is available at:

```text
https://<github-username>.github.io/pagefeed/<public_path>
```

Important: keeping `feeds.toml` private hides the source list from the repository, but the generated RSS files and linked URLs are still public if the Pages site is public.

## How It Works

- `feeds.toml` defines one or more listing pages and the link patterns that count as feed items.
- The generator fetches each source page, extracts matching anchors, derives a title and optional date, then writes RSS 2.0 XML.
- `min_items` acts as a safety rail. If extraction drops below the configured threshold, generation fails before overwriting the existing feed.
- GitHub Actions runs tests, materializes the private config when needed, generates feeds, and deploys `public/`.

## Documentation

- [Configuration reference](docs/configuration.md)
- [Architecture notes](docs/architecture.md)
- [Example config](feeds.example.toml)

## Operational Notes

- Fetch only publicly accessible pages.
- Do not use cookies, login sessions, paywall bypasses, or CAPTCHA workarounds.
- Prefer opaque public feed names such as `f-a1b2c3.xml`.
- Keep feed titles and descriptions clearly unofficial.
- Use an identifying `PAGEFEED_USER_AGENT`, ideally including the public repository URL.
