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
    atlas = subparsers.add_parser("atlas", help="Export existing M7 data as offline Time Atlas RDE envelopes")
    atlas.add_argument("--input-directory", type=Path, required=True)
    atlas.add_argument("--output-directory", type=Path, required=True, help="New or empty output directory")
    atlas.add_argument("--profile", type=Path, help="Atlas dataset identity and optional spatial annotations")
    args = parser.parse_args()
    if args.command == "atlas":
        from .atlas import export_atlas
        try:
            result = export_atlas(args.input_directory, args.output_directory, profile_path=args.profile)
        except (OSError, ValueError) as exc:
            parser.exit(1, f"error: {exc}\n")
    else:
        result = run_pipeline(args.config)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
