"""Command-line interface for Module 2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    """Describe the Module 2 command and its arguments."""

    parser = argparse.ArgumentParser(
        prog="iiif-entry-validator",
        description="Check accessibility and response properties of IIIF candidate entry points.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Run Module 2 from a JSON configuration")
    run_parser.add_argument("--config", type=Path, required=True, help="Path to the JSON config")
    run_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Check every endpoint for only the first N providers",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the requested command and return a conventional process code."""

    args = build_parser().parse_args(argv)
    try:
        result = run_pipeline(args.config, limit=args.limit)
        print(
            json.dumps(
                {
                    "input_provider_count": result.input_count,
                    "input_endpoint_count": result.input_endpoint_count,
                    "checked_count": result.checked_count,
                    "unique_request_count": result.unique_request_count,
                    "providers_with_reachable_endpoint": result.providers_with_reachable_endpoint,
                    "providers_with_json_endpoint": result.providers_with_json_endpoint,
                    "result_counts": result.result_counts,
                    "checked_jsonl": str(result.checked_jsonl),
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
