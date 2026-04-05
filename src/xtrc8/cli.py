#!/usr/bin/env python3
"""
xtrc8 — Unified CLI entry point.

Usage:
    xtrc8 clip <url-or-file> [--output-dir DIR] [--to refs|papers|datasheets]
    xtrc8 tweets <subcommand> [options]
    xtrc8 extract [--dry-run] [--skip-replies]
"""

import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: xtrc8 <command> [args...]")
        print()
        print("Commands:")
        print("  clip      Clip web articles, PDFs, and arxiv papers")
        print("  tweets    Twitter/X bookmark sync, export, and TUI")
        print("  extract   Resolve and clip links found in tweets")
        sys.exit(1)

    command = sys.argv[1]
    # Remove the command name so submodule parsers see the right argv
    sys.argv = [f"xtrc8 {command}"] + sys.argv[2:]

    if command == "clip":
        from .clip import main as clip_main
        clip_main()
    elif command == "tweets":
        from .tweets import main as tweets_main
        tweets_main()
    elif command == "extract":
        from .extract import main as extract_main
        extract_main()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
