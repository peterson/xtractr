# xtrc8 — Standing Instructions for Claude Code

## What this repo is

xtrc8 is a standalone Python toolkit for extracting and archiving web content:
- **clip** — Fetch web articles (via trafilatura), ingest PDFs and arxiv papers,
  clip videos from YouTube/Vimeo/etc (via yt-dlp). Outputs markdown with frontmatter.
  **Note:** PDFs are placed on disk with a minimal placeholder stub — the actual
  summary is produced later by a human/LLM reading the PDF and writing a structured
  summary (see `raw/papers/*.md` in consuming repos for the paper template).
- **tweets** — Sync Twitter/X bookmarks via Playwright, browse with a Textual TUI,
  export to markdown with media download and translation.
- **extract** — Resolve t.co shortened URLs from tweets, auto-clip papers, gists,
  and GitHub repos found in bookmarks.

All paths are parametric — no hardcoded project structure. Designed to be used both
as a library (`from xtrc8.clip import clip_web`) and as a CLI (`xtrc8 clip <url>`).

## Package layout

```
src/xtrc8/
  __init__.py     — version
  util.py         — slugify and shared helpers
  cli.py          — unified CLI dispatcher
  clip.py         — web/PDF/arxiv clipping
  tweets.py       — X bookmark sync, TUI, export
  extract.py      — tweet link resolution and auto-clipping
```

## Design principles

- **No global state** — all functions take explicit path parameters
- **Library-first** — CLI is a thin wrapper around importable functions
- **Minimal coupling** — each module can be used independently
- Playwright is used for X scraping (not twikit — it's unreliable)

## Dependencies

Core: trafilatura, pymupdf, httpx, rich, yt-dlp, faster-whisper (optional)
Twitter: playwright, textual, deep-translator

## Running

```bash
uv run xtrc8 clip <url>
uv run xtrc8 tweets sync --all
uv run xtrc8 tweets select
uv run xtrc8 extract --dry-run
```

Or via short aliases: `xc`, `xt`, `xe`.
