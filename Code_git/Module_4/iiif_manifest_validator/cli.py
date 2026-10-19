"""Command-line interface for Module 4."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iiif-manifest-validator",
        description="Fetch, cache, and structurally validate IIIF Manifests.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser(
        "run", help="Run Module 4 from a JSON configuration"
    )
    run_parser.add_argument(
        "--config", type=Path, required=True, help="Path to the JSON config"
    )
    run_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N Manifest records",
    )
    run_parser.add_argument(
        "--force-refresh",
        action="store_true",
        default=None,
        help="Ignore cached raw JSON and request every selected Manifest again",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_pipeline(
            args.config,
            limit=args.limit,
            force_refresh=args.force_refresh,
        )
        print(
            json.dumps(
                {
                    "input_manifest_count": result.input_manifest_count,
                    "processed_manifest_count": result.processed_manifest_count,
                    "status_counts": result.status_counts,
                    "valid_manifest_count": result.valid_manifest_count,
                    "canvas_count": result.canvas_count,
                    "image_body_count": result.image_body_count,
                    "image_service_count": result.image_service_count,
                    "cache_hit_count": result.cache_hit_count,
                    "normalized_manifest_count": result.normalized_manifest_count,
                    "validated_manifests_jsonl": str(
                        result.validated_manifests_jsonl
                    ),
                    "resource_inventory_jsonl": str(
                        result.resource_inventory_jsonl
                    ),
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
