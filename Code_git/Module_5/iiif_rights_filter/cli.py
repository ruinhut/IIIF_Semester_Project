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
        description=(
            "Extract IIIF rights evidence, retain all records for research, "
            "and identify the public-reuse-eligible subset."
        ),
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
        print(json.dumps({
            "input_manifest_count": result.input_manifest_count,
            "processed_manifest_count": result.processed_manifest_count,
            "decision_counts": result.decision_counts,
            "category_counts": result.category_counts,
            "research_resource_count": result.research_resource_count,
            "reuse_eligible_resource_count": result.reuse_eligible_resource_count,
            "research_manifests_jsonl": str(result.research_manifests_jsonl),
            "reuse_eligible_manifests_jsonl": str(result.reuse_eligible_manifests_jsonl),
            "research_only_manifests_jsonl": str(result.research_only_manifests_jsonl),
            "research_resource_inventory_jsonl": str(result.research_resource_inventory_jsonl),
            "reuse_eligible_resource_inventory_jsonl": str(
                result.reuse_eligible_resource_inventory_jsonl
            ),
            "log_file": str(result.log_txt),
        }, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
