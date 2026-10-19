"""Command-line boundary for Module 1.

This file translates shell arguments into calls to the pipeline or selector.
The actual harvesting, normalization, filtering, and storage logic lives in
the other package files so it can also be reused from Python code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import ProviderRecord
from .pipeline import run_pipeline
from .selector import SelectionCriteria, select_providers
from .store import read_jsonl, write_jsonl


def build_parser() -> argparse.ArgumentParser:
    """Describe the available commands and their command-line arguments."""

    parser = argparse.ArgumentParser(
        prog="iiif-provider-census",
        description="Build and select a census of IIIF providers.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run census and selection from a JSON config")
    run_parser.add_argument("--config", type=Path, required=True, help="Path to the JSON config")
    run_parser.add_argument(
        "--institution",
        action="append",
        required=True,
        help='Exact institution name to select, or "all"; repeat to select multiple institutions',
    )

    select_parser = subparsers.add_parser("select", help="Select providers from an existing JSONL census")
    select_parser.add_argument("--input", type=Path, required=True, help="providers.jsonl")
    select_parser.add_argument("--output", type=Path, required=True, help="output JSONL path")
    select_parser.add_argument("--criteria", type=Path, required=True, help="selection criteria JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one CLI command and return a conventional process exit code."""

    args = build_parser().parse_args(argv)
    try:
        if args.command == "run":
            # The run command performs the complete Module 1 workflow.
            result = run_pipeline(args.config, institution_selection=args.institution)
            print(
                json.dumps(
                    {
                        "all_provider_count": result.all_provider_count,
                        "all_endpoint_count": result.all_endpoint_count,
                        "selected_provider_count": result.selected_provider_count,
                        "selected_endpoint_count": result.selected_endpoint_count,
                        "output_directory": str(result.output_directory),
                        "log_file": str(result.log_txt),
                    },
                    ensure_ascii=False,
                )
            )
            return 0

        # The select command reuses a previously generated census and therefore
        # does not access the Registry again.
        criteria_value = json.loads(args.criteria.read_text(encoding="utf-8-sig"))
        criteria = SelectionCriteria.from_mapping(criteria_value)
        records: list[ProviderRecord] = read_jsonl(args.input)
        selected = select_providers(records, criteria)
        write_jsonl(args.output, selected)
        print(json.dumps({"selected_provider_count": len(selected)}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
