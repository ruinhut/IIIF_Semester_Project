"""Command-line interface for Module 5."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iiif-rights-filter",
        description="Extract and policy-filter rights evidence from IIIF Manifests.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser(
        "run", help="Run Module 5 from a JSON configuration"
    )
    run_parser.add_argument(
        "--config", type=Path, required=True, help="Path to the JSON config"
    )
    run_parser.add_argument(
        "--limit", type=int, default=None, help="Process only the first N Manifests"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_pipeline(args.config, limit=args.limit)
        print(
            json.dumps(
                {
                    "input_manifest_count": result.input_manifest_count,
                    "processed_manifest_count": result.processed_manifest_count,
                    "decision_counts": result.decision_counts,
                    "category_counts": result.category_counts,
                    "allowed_resource_count": result.allowed_resource_count,
                    "rights_assessed_jsonl": str(result.rights_assessed_jsonl),
                    "allowed_manifests_jsonl": str(result.allowed_manifests_jsonl),
                    "excluded_manifests_jsonl": str(result.excluded_manifests_jsonl),
                    "log_file": str(result.log_txt),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
