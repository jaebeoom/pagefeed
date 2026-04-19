# AGENTS.md

## Project Scope

`pagefeed` generates static RSS feeds from simple webpage listing pages.

## Environment

- Python target is 3.12.
- Use only standard-library runtime dependencies by default.
- Do not add network-dependent tests.
- Do not read `.env` files. Use explicit environment variables documented in `README.md`.

## Run And Test

- Generate feeds locally:

```text
PYTHONPATH=src python3 -m pagefeed generate --config feeds.toml
```

- Run tests:

```text
PYTHONPATH=src python3 -m unittest discover -s tests
```

If a virtual environment is needed later, create it with:

```text
uv venv venv
```

and keep dependencies in `pyproject.toml`.
