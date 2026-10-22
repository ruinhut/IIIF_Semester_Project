"""Prepare the two-provider live evaluation from the current Module 2 output."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
MODULE_3 = HERE.parents[1]
INPUT = MODULE_3.parent / "Module_2" / "data" / "output" / "checked_entry_points.jsonl"
OUTPUT = HERE / "input.jsonl"
PROVIDER_IDS = {
    "provider-f2683615336e129a",  # EPFL Plume: development investigation
    "provider-691126b502b5821e",  # Art Institute: held-out transfer
}


def main() -> None:
    selected: list[dict[str, object]] = []
    with INPUT.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("provider_id") in PROVIDER_IDS:
                selected.append(row)
    found = {str(row.get("provider_id")) for row in selected}
    missing = PROVIDER_IDS - found
    if missing:
        raise RuntimeError(f"Providers missing from Module 2 output: {sorted(missing)}")
    OUTPUT.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in selected
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(selected)} endpoint records for {len(found)} providers to {OUTPUT}")


if __name__ == "__main__":
    main()
