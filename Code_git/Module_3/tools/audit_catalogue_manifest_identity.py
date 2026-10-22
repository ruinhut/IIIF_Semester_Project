"""Cross-check catalogue identity against fetched Manifest metadata, without repairs."""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Module_6"))
from iiif_metadata_normalizer.reference_text import clean_text


def normalized(value):
    values = value if isinstance(value, list) else [value]
    return " ".join(clean_text(str(v or "")) for v in values).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--manifest-input", type=Path, required=True)
    parser.add_argument("--raw-directory", type=Path, required=True)
    parser.add_argument("--identifier-pattern", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalogue = {r["identifier"]: r for r in (json.loads(l) for l in args.catalogue.open(encoding="utf-8"))}
    pattern = re.compile(args.identifier_pattern)
    counts, result, suspicious = Counter(), [], []
    for line in args.manifest_input.open(encoding="utf-8"):
        row = json.loads(line)
        match = pattern.search(row["manifest_url"])
        if not match:
            raise ValueError("Manifest URL did not match the reviewed identifier pattern")
        identifier = match.group("identifier")
        entry = catalogue[identifier]["record"]["generalInfo"]
        raw = args.raw_directory / (row["manifest_id"] + ".json")
        manifest = json.loads(raw.read_bytes())
        metadata = {str(item.get("label", "")).strip().casefold(): item.get("value")
                    for item in manifest.get("metadata", []) if isinstance(item, dict)}
        title_match = normalized(entry.get("title")) == normalized(metadata.get("title"))
        code_match = normalized(entry.get("itemCode")) == normalized(metadata.get("asset code"))
        detail = {"identifier": identifier, "item_type": entry.get("itemType"), "title_match": title_match,
                  "asset_code_match": code_match, "source_missing_id": not (manifest.get("id") or manifest.get("@id")),
                  "source_missing_label": not manifest.get("label"), "manifest_url": row["manifest_url"]}
        counts["checked"] += 1
        for key in ("title_match", "asset_code_match", "source_missing_id", "source_missing_label"):
            counts[key] += bool(detail[key])
        if not title_match or not code_match:
            suspicious.append({**detail, "catalogue_title": entry.get("title"), "manifest_title": metadata.get("title"),
                               "catalogue_asset_code": entry.get("itemCode"), "manifest_asset_code": metadata.get("asset code")})
        result.append(detail)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "identity_checks.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result[0])); writer.writeheader(); writer.writerows(result)
    summary = {"counts": dict(counts), "metadata_differences": suspicious,
               "scope": "Source identity/field audit, not a complete IIIF conformance certification."}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"counts": dict(counts), "metadata_differences": len(suspicious)}), flush=True)


if __name__ == "__main__":
    main()
