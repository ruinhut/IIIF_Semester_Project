"""Command-line interface for Module 7."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and export IIIF records in the common profile")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
