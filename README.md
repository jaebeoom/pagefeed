# pagefeed

Generate static RSS feeds from simple webpage listing pages.

The feed configuration is intentionally local or secret-backed, so a public repository does not need to expose the configured source pages.

GitHub Actions writes feeds into `public/` and deploys them through GitHub Pages. RSS readers then fetch static XML files instead of depending on a live scraping service.

This project is an unofficial feed generator. Generated feeds should link to original sources and should not republish full article content, images, or other substantial source material without permission.

## Setup

1. Create a GitHub repository named `pagefeed`.
2. Push this project to that repository.
3. In GitHub, create a repository secret named `PAGEFEED_CONFIG_TOML` containing your private `feeds.toml` content.
4. Optional but recommended: create `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` repository secrets for failure alerts.
5. In GitHub, enable Pages with source set to `GitHub Actions`.
6. Run the `Update feeds` workflow manually once, or wait for the hourly schedule.

After deployment, subscribe to each feed by its configured `public_path`:

```text
https://<github-username>.github.io/pagefeed/f-000001.xml
```

Important: hiding `feeds.toml` keeps the source list out of the repository, but public RSS XML still exposes item URLs. If the GitHub Pages site is public, the generated feeds are public too.

## First Deployment

Create the GitHub repository, then connect and push this local repository:

```text
git remote add origin git@github.com:<github-username>/pagefeed.git
git push -u origin main
```

Add repository secrets in:

```text
Settings -> Secrets and variables -> Actions -> Repository secrets
```

Required:

```text
PAGEFEED_CONFIG_TOML
```

Put your full local `feeds.toml` content in `PAGEFEED_CONFIG_TOML`.

Optional failure alerts:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

Enable Pages in:

```text
Settings -> Pages -> Build and deployment -> Source -> GitHub Actions
```

Then run the first build manually:

```text
Actions -> Update feeds -> Run workflow
```

The workflow does not run on every push. It runs only on manual dispatch and the hourly schedule, so initial setup can be completed before the first feed generation attempt.

After the workflow succeeds, open the deployed feed URL:

```text
https://<github-username>.github.io/pagefeed/<public_path>
```

For example:

```text
https://<github-username>.github.io/pagefeed/f-000001.xml
```

## Local Use

Create a local config from the example:

```text
cp feeds.example.toml feeds.toml
```

Then edit `feeds.toml`. It is ignored by Git.

Optional local agent instructions can be created from the example:

```text
cp AGENTS.example.md AGENTS.md
```

Generate feeds:

```text
PYTHONPATH=src python3 -m pagefeed generate --config feeds.toml
```

Use `PAGEFEED_BASE_URL` to set the feed self URL:

```text
PYTHONPATH=src PAGEFEED_BASE_URL=https://<github-username>.github.io/pagefeed python3 -m pagefeed generate --config feeds.toml
```

Use `PAGEFEED_USER_AGENT` to identify your deployed project when fetching source pages:

```text
PYTHONPATH=src PAGEFEED_USER_AGENT="pagefeed/0.1 (+https://github.com/<github-username>/pagefeed)" python3 -m pagefeed generate --config feeds.toml
```

Run tests:

```text
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Configuration

Feeds live in `feeds.toml` locally, or in the GitHub repository secret `PAGEFEED_CONFIG_TOML` in Actions.

Each feed can define:

- `source_url`: listing page to fetch
- `output_path`: generated XML path
- `public_path`: path under the published site
- `title`: RSS channel title
- `description`: RSS channel description
- `include_href_patterns`: regular expressions for anchors that should become feed items
- `max_items`: maximum items to include
- `min_items`: minimum items required before writing XML

Multiple feeds are supported by adding more `[[feeds]]` tables. Each feed should write to a distinct `output_path`.

Prefer opaque output names such as `public/f-a1b2c3.xml` instead of names that reveal the source site. This does not make the feed private, but it avoids exposing the source through the URL alone.

The extractor is intentionally conservative. It is designed for simple index pages where each item appears as an anchor link. A feed can point at a higher-level listing page when `include_href_patterns` narrows the matches to article URLs. For card-style listings, title extraction skips category, date, and read-more labels before falling back to anchor text.

Keep generated feeds limited to titles, links, dates, and minimal metadata. Do not add full-content scraping unless you have permission from the source site.

## Operational Policy

- Fetch only publicly accessible pages.
- Do not use cookies, login sessions, paywall bypasses, CAPTCHA bypasses, or IP-block workarounds.
- Check source-site terms and `robots.txt` before adding a feed when they are available.
- Stop or remove a feed if the source site asks you to stop.
- Keep feed titles and descriptions clearly unofficial.
- Use an identifying `PAGEFEED_USER_AGENT`, ideally including the public repository URL.

## Failure Detection

Set `min_items` for every feed. If extraction returns fewer items than expected, generation fails before writing XML. In GitHub Actions this prevents deploying an empty or broken feed, so the previous working Pages artifact remains in place.

For example:

```toml
min_items = 1
```

The workflow includes a failure notification job. If `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are configured, failed or cancelled build/deploy runs send a Telegram message with only the Actions run URL:

```text
pagefeed failed. Check: https://github.com/<owner>/<repo>/actions/runs/<run-id>
```

The alert intentionally does not include source URLs or feed item links.
