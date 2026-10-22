"""Two-command interface for Module 8."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .pipeline import run_download


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Module 7 image URLs with their linked JSON records"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("download-example", "download the first successfully retrievable image"),
        ("download-all", "download every eligible image"),
    ):
        child = subparsers.add_parser(command, help=help_text)
        child.add_argument("--config", type=Path, required=True)

    args = parser.parse_args()
    try:
        summary = run_download(args.config, mode=args.command)
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
