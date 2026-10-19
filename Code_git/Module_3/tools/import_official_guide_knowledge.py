"""Generate Module 3 documentary knowledge from the official IIIF guides."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from iiif_resource_discovery.official_guide_knowledge import (  # noqa: E402
    build_knowledge_base,
    executable_provider_ids,
    read_jsonl,
    write_knowledge_base,
    write_markdown_inventory,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import official IIIF resource-guide workflows into Module 3 knowledge."
    )
    parser.add_argument("--guides-repository", type=Path, required=True)
    parser.add_argument("--provider-census", type=Path, required=True)
    parser.add_argument("--previous-results", type=Path, required=True)
    parser.add_argument("--executable-knowledge", type=Path)
    parser.add_argument("--checked-date", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    value = build_knowledge_base(
        args.guides_repository,
        provider_records=read_jsonl(args.provider_census),
        previous_results=read_jsonl(args.previous_results),
        executable_provider_ids=executable_provider_ids(args.executable_knowledge),
        checked_date=args.checked_date,
    )
    write_knowledge_base(args.output, value)
    if args.markdown_output:
        write_markdown_inventory(args.markdown_output, value)
    states: dict[str, int] = {}
    for provider in value["providers"]:
        state = provider["validation_state"]
        states[state] = states.get(state, 0) + 1
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "providers": len(value["providers"]),
                "generic_skills": len(value["generic_skills"]),
                "markdown_output": (
                    str(args.markdown_output.resolve())
                    if args.markdown_output
                    else None
                ),
                "validation_states": states,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
