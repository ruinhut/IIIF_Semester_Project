"""Read our export with the official SDK and run strict offline validation.

Use Python >=3.12 with time-atlas-python==0.3.0. This script never creates an
API client, uploads files, or publishes research-only resources.
"""

from __future__ import annotations

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import warnings


def validate_bundle(bundle: Path) -> dict:
    """Check SDK deserialization, preserved payload and collection references."""
    from timeatlas import RDECollection

    bundle = bundle.resolve()
    exported = json.loads((bundle / "atlas_export_report.json").read_text(encoding="utf-8"))
    directory = bundle / "rde"
    expected = []
    envelopes = []
    for path in sorted(directory.glob("*.json")):
        envelope = json.loads(path.read_text(encoding="utf-8"))
        expected.extend(envelope["rde_objects"])
        envelopes.append(envelope)
    if not expected:
        raise ValueError("The export has no RDE entities; inspect staging and date readiness")
    # Cross-check the single-file package as well; order differences are harmless.
    packaged = [json.loads(line) for line in (directory / "collection.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if {e["name"]: e for e in packaged} != {e["name"]: e for e in envelopes}:
        raise ValueError("JSONL package does not match the per-type JSON files")
    collection = RDECollection.read_rde_from_files(str(directory))
    actual = {obj.id: obj.to_dict() for obj in collection.rdes}
    if len(actual) != len(expected):
        raise ValueError("Official SDK skipped an entity or encountered duplicate IDs")
    for row in expected:
        restored = actual[row["id"]]
        for key in ("id", "rde_type", "start_time", "end_time", "dataset", "metadata", "has_observations", "historical_record"):
            if key in row and restored.get(key) != row[key]:
                raise ValueError(f"Official SDK round trip changed {row['id']} field {key}")
    errors = []
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        try:
            collection.validate_data(mode="strict")
        except ValueError as exc:
            errors.append(str(exc))
    return {
        "sdk": "time-atlas-python", "sdk_version": version("time-atlas-python"),
        "target_commit": exported["target_commit"], "bundle": str(bundle),
        "entities_read": len(expected), "round_trip_payload_preserved": True,
        "strict_collection_valid": not errors, "errors": errors,
        "warnings": [str(item.message) for item in captured],
        "external_area_verification_required": exported["external_area_verification_required"],
        "team_schema_certified": False, "server_import_tested": False,
        "uploaded": False, "published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Optional saved validation report")
    parser.add_argument("--allow-staging", action="store_true", help="Return success after a readable staging bundle even if strict spatial validation fails")
    args = parser.parse_args()
    try:
        result = validate_bundle(args.bundle)
    except (OSError, ValueError, ImportError) as exc:
        parser.exit(1, f"error: {exc}\n")
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(content)
    return 0 if result["strict_collection_valid"] or args.allow_staging else 2


if __name__ == "__main__":
    raise SystemExit(main())
