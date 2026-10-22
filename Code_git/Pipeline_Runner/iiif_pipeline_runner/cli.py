"""Command-line interface for the complete pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .runner import PipelineRunError, run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Modules 1–8 sequentially and stop on the first failure")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--from-module", type=int, dest="first")
    parser.add_argument("--to-module", type=int, dest="last")
    args = parser.parse_args()
    try:
        summary = run_pipeline(args.config, first=args.first, last=args.last)
    except PipelineRunError as exc:
        print(json.dumps(exc.summary, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(exc.return_code)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
