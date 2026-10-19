"""Command-line interface for Module 6."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and normalize IIIF Manifest metadata")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run the Module 6 pipeline")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.command == "run":
        print(json.dumps(run_pipeline(args.config, limit=args.limit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
