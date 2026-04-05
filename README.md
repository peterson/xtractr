# xtrc8

Extraction toolkit for LLM-compiled knowledge bases. Pulls web articles, PDFs, arxiv papers, and Twitter/X bookmarks into a structured `raw/` directory for onward processing by an LLM agent.

## Background

Inspired by [Andrej Karpathy's LLM Knowledge Bases](https://x.com/karpathy/status/2039805659525644595) pattern (April 2026):

> *TLDR: raw data from a given number of sources is collected, then compiled by an LLM
> into a .md wiki, then operated on by various CLIs by the LLM to do Q&A and to
> incrementally enhance the wiki, and all of it viewable in Obsidian.*

Karpathy's [idea file](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) describes a three-layer architecture: **raw sources → compiled wiki → schema**, with three core operations: **ingest, query, lint**. As he noted in a [follow-up](https://x.com/karpathy/status/2040470801506541998), in the era of LLM agents you share the idea rather than the code — each person's agent builds a version tailored to their needs.

xtrc8 handles the first layer: **getting raw sources into `raw/`**. It's the ingest tooling that feeds your LLM compile passes. You bring your own wiki structure, compile logic, and LLM agent — xtrc8 just makes sure high-quality source material lands in the right place.

## How it fits together

A typical knowledge base using this pattern looks like:

```
my-kb/
├── raw/                  # ← xtrc8 writes here
│   ├── papers/           # PDFs + markdown summaries (arxiv, direct PDF links)
│   ├── refs/             # Web articles, GitHub READMEs, gists
│   ├── tweets/           # Tweet exports with media
│   ├── standards/        # Your own additions (standards, specs, etc.)
│   └── datasheets/       # Your own additions
│
├── wiki/                 # ← Your LLM agent compiles raw/ into this
│   ├── concepts/         # One article per concept
│   ├── domains/          # Domain overview articles
│   └── ...
│
└── .tweets-cache.db      # xtrc8's local cache (gitignored)
```

**xtrc8 fills `raw/`.** Everything downstream — compiling wiki articles, maintaining indexes, running queries — is the job of your LLM agent (Claude Code, Cursor, etc.) with whatever standing instructions you write.

The pipeline in practice:

1. **Bookmark interesting content on X** — papers, threads, repos, articles
2. **`xtrc8 tweets sync --all`** — pulls bookmarks into local cache
3. **`xtrc8 tweets select`** — TUI to browse and pick which tweets to export
4. **`xtrc8 extract`** — auto-resolves t.co links, clips any papers/gists/repos found
5. **`xtrc8 clip <url>`** — manually clip a specific article or PDF
6. **Your LLM agent** reads `raw/`, compiles into `wiki/`, answers queries

Tweets act as a discovery mechanism. When you bookmark a tweet linking to an arxiv paper, xtrc8 follows the link, downloads the PDF, and converts it to searchable markdown — the paper becomes a first-class source in `raw/papers/`, not just a tweet.

## Install

```bash
uv add git+https://github.com/peterson/xtrc8
# or for local development
uv add --editable ../xtrc8
```

Playwright (required for Twitter features) needs a one-time browser install:

```bash
uv run playwright install chromium
```

## Quick start

```bash
# Clip a web article → raw/refs/
xtrc8 clip https://example.com/some-article --output-dir ./raw

# Clip an arxiv paper → downloads PDF + markdown summary to raw/papers/
xtrc8 clip https://arxiv.org/abs/2301.00001 --output-dir ./raw

# Clip a local PDF
xtrc8 clip paper.pdf --output-dir ./raw

# Set up Twitter auth, sync bookmarks, launch selector
xtrc8 tweets auth
xtrc8 tweets sync --all
xtrc8 tweets select
```

## Tools

### clip — Web, PDF, and arxiv extraction

Fetches content and converts to markdown with YAML frontmatter (title, author, date, source URL). PDFs are converted via pymupdf4llm with the original PDF kept alongside — the PDF is the source of truth for equations and figures, the markdown is a searchable index.

```bash
xtrc8 clip <url-or-file> [--output-dir DIR] [--to refs|papers|datasheets|misc]
```

| Source type | Detection | Output |
|-------------|-----------|--------|
| Web article | Any HTTP URL | Markdown via trafilatura |
| arxiv | `arxiv.org/abs/` or `arxiv.org/pdf/` URLs | PDF download + markdown summary |
| PDF URL | URLs ending in `.pdf` | PDF download + markdown summary |
| Local PDF | File path ending in `.pdf` | Markdown summary + PDF copy |

The `--to` flag controls which subdirectory content lands in (`refs`, `papers`, `datasheets`, `misc`). Auto-detected if omitted: PDFs and arxiv go to `papers/`, web articles go to `refs/`.

As a library:

```python
from pathlib import Path
from xtrc8.clip import clip_web, clip_pdf, clip_arxiv, clip_pdf_url

clip_web("https://example.com/article", dest_dir=Path("raw/refs"))
clip_pdf(Path("paper.pdf"), dest_dir=Path("raw/papers"))
clip_arxiv("2301.00001", dest_dir=Path("raw/papers"))
clip_pdf_url("https://example.com/report.pdf", dest_dir=Path("raw/papers"))
```

### tweets — Twitter/X bookmark sync and export

Syncs your X bookmarks into a local SQLite cache using Playwright to intercept the GraphQL API responses in a headless browser. No paid API access required — just your browser cookies.

Includes a TUI for browsing cached tweets by folder, selecting which ones to export, and auto-syncing in the background.

#### Auth setup

Cookies are stored in the SQLite database (no separate credentials file).

```bash
xtrc8 tweets auth
```

You'll be prompted for `auth_token` and `ct0`. To get these: open x.com in your browser, DevTools (F12) → Application → Cookies → `https://x.com`, copy the values.

#### Sync bookmarks

```bash
# Sync main (unfiled) bookmarks
xtrc8 tweets sync

# Sync everything — main + all bookmark folders
xtrc8 tweets sync --all

# Sync a specific folder
xtrc8 tweets sync --folder "Research"

# Sync all + auto-export tweets from configured folders
xtrc8 tweets sync --auto

# Full backfill — fetch up to 500, disable duplicate early-stop
xtrc8 tweets sync --count 500 --no-early-stop
```

Synced tweets are cached locally in `.tweets-cache.db`. Sync is incremental — stops early after 20 consecutive known tweets.

#### Browse and export

```bash
xtrc8 tweets select
```

Split-pane TUI:

- **Left pane** — bookmark folders. SPACE toggles auto-import (persisted). Tweets in marked folders are pre-selected on the right.
- **Right pane** — tweet list with date, author, preview. SPACE toggles individual tweets.
- **Bottom** — full preview of highlighted tweet.
- **Status bar** — animated spinner while background sync is running.

| Key | Action |
|-----|--------|
| `Tab` | Switch between folders and tweets panes |
| `Space` | Toggle selection (folder auto-ingest or tweet) |
| `a` / `n` | Select all / none |
| `i` | Import selected tweets to output directory |
| `u` | Un-import highlighted tweet |
| `f` | Cycle filter: all → folders → staged → imported |
| `q` | Quit (warns if staged tweets not imported) |

The TUI syncs new bookmarks in the background every 10 minutes.

#### Export format

Exported tweets are markdown files with frontmatter:

```yaml
---
author: @handle
date: 2025-03-15
url: https://x.com/handle/status/123
type: tweet
lang: en
---
```

Non-English tweets are auto-translated (via Google Translate) with both translation and original included. Media (images) are downloaded locally into a `media/` subdirectory.

#### Other commands

```bash
xtrc8 tweets status    # Cache stats: total, ingested, by folder, top authors
xtrc8 tweets folders   # List bookmark folders and auto-ingest settings
```

#### Custom paths

All commands accept `--db` and `--output-dir`:

```bash
xtrc8 tweets --db ./my-cache.db --output-dir ./raw/tweets sync --all
```

As a library:

```python
from pathlib import Path
from xtrc8.tweets import get_db, export_tweet, cmd_sync_cli

db = get_db(Path("tweets.db"))
# ... query tweets, export, etc.
```

### extract — Auto-clip links from tweets

The glue between tweets and real sources. Scans imported tweets for URLs, resolves t.co shortlinks, and auto-clips papers, gists, and GitHub repos into your `raw/` tree. Also scrapes author reply threads for links (authors often drop paper links in their first reply).

This is what turns a bookmarked tweet into a first-class source: a tweet linking to an arxiv paper results in the PDF landing in `raw/papers/` with a structured markdown summary.

```bash
# Preview what would be clipped
xtrc8 extract --dry-run

# Run full extraction (resolve links + clip)
xtrc8 extract

# Skip reply thread scraping (faster)
xtrc8 extract --skip-replies

# Custom paths
xtrc8 extract --db ./tweets.db --output-dir ./raw
```

Link types detected and clipped:

| Type | Detection | Action |
|------|-----------|--------|
| arxiv | `arxiv.org` URLs | Download PDF + markdown summary → `papers/` |
| PDF | URLs ending in `.pdf` | Download + markdown summary → `papers/` |
| GitHub gist | `gist.github.com` URLs | Fetch via API, save as markdown → `refs/` |
| GitHub repo | `github.com/owner/repo` URLs | Clip README via trafilatura → `refs/` |

A `_repos.md` index is auto-maintained with all GitHub repos found.

As a library:

```python
from pathlib import Path
from xtrc8.extract import run_extract

clipped = run_extract(
    db_path=Path("tweets.db"),
    output_dir=Path("raw"),
    dry_run=False,
    skip_replies=True,
)
print(f"Clipped {clipped} items")
```

## Short aliases

If installed as a package, short CLI aliases are available:

| Alias | Equivalent |
|-------|-----------|
| `xc` | `xtrc8 clip` |
| `xt` | `xtrc8 tweets` |
| `xe` | `xtrc8 extract` |

## Dependencies

- **trafilatura** — web article extraction
- **pymupdf** + **pymupdf4llm** — PDF text extraction and markdown conversion
- **httpx** — HTTP client for downloads and API calls
- **playwright** — browser automation for X bookmark scraping
- **textual** — TUI framework for tweet selector
- **rich** — terminal formatting
- **deep-translator** — auto-translation of non-English tweets

## Security notes

xtrc8 is designed as a single-user local CLI tool. Keep these limitations in mind if you adapt it for other contexts:

- **Plaintext cookie storage** — X session cookies (`auth_token`, `ct0`) are stored unencrypted in the SQLite database. The DB file is gitignored by default, but anyone with read access to it gets your X session. If the DB could be shared or synced, consider OS keychain integration instead.
- **No URL filtering** — `clip` and `extract` will fetch any URL they're given, including internal/private IPs (e.g. `169.254.169.254`, `localhost`). This is fine when you're the one supplying URLs, but would be an SSRF risk if URLs came from untrusted input in a server context.
