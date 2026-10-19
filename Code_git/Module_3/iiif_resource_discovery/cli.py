"""Command-line interface for Module 3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    """Describe the Module 3 command and its arguments."""

    parser = argparse.ArgumentParser(
        prog="iiif-resource-discovery",
        description="Resolve IIIF machine endpoints and discover Manifest URLs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Run Module 3 from a JSON configuration")
    run_parser.add_argument("--config", type=Path, required=True, help="Path to the JSON config")
    run_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N providers for a bounded smoke run",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one Module 3 command and return a conventional process code."""

    args = build_parser().parse_args(argv)
    try:
        result = run_pipeline(args.config, limit=args.limit)
        print(
            json.dumps(
                {
                    "input_provider_count": result.input_provider_count,
                    "input_endpoint_count": result.input_endpoint_count,
                    "processed_provider_count": result.processed_provider_count,
                    "provider_status_counts": result.provider_status_counts,
                    "unique_manifest_count": result.unique_manifest_count,
                    "knowledge_skill_run_count": result.knowledge_skill_run_count,
                    "knowledge_resolved_provider_count": result.knowledge_resolved_provider_count,
                    "manifest_urls_jsonl": str(result.manifest_urls_jsonl),
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
