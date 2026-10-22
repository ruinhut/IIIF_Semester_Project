"""Select a non-random, type-balanced download check from real Module 7 outputs."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re


def rows(path):
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "evaluation/2026-10-16_blavatnik_investigation"
    source = root / "final/module7/output"
    destination = root / "diverse_downloads"
    destination.mkdir(exist_ok=True)
    catalogue = {r["identifier"]: r["record"]["generalInfo"] for r in rows(root / "entire_catalogue_snapshot_v2/catalogue_records.jsonl")}
    records = rows(source / "common_records.jsonl")
    media = rows(source / "common_media.jsonl")
    profiles = rows(source / "ocr_document_profiles.jsonl")
    references = rows(source / "institution_reference_texts.jsonl")
    media_by_record, groups = defaultdict(list), defaultdict(list)
    for row in media:
        media_by_record[row["record_id"]].append(row)
    for row in records:
        identifier = re.search(r"/iiif-manifest/(\d+)", row["source"]["manifest_url"]).group(1)
        groups[catalogue[identifier]["itemType"]].append(row)
    selected_records, selected_media, seen_urls, selection = [], [], set(), []
    while any(groups.values()) and len(selected_records) < args.limit:
        for kind in sorted(groups):
            if not groups[kind] or len(selected_records) >= args.limit:
                continue
            record = groups[kind].pop(0)
            available = sorted(media_by_record[record["record_id"]], key=lambda row: row["sequence"])
            preferred = min(9, len(available) - 1)
            candidates = available[preferred:] + available[:preferred]
            page = next((r for r in candidates if r["image"]["id"] not in seen_urls), None)
            if page is None:
                continue
            seen_urls.add(page["image"]["id"])
            selected_records.append(record); selected_media.append(page)
            selection.append({"item_type": kind, "record_id": record["record_id"], "resource_id": page["resource_id"],
                              "manifest_url": record["source"]["manifest_url"], "image_url": page["image"]["id"]})
    record_ids = {r["record_id"] for r in selected_records}
    resource_ids = {r["resource_id"] for r in selected_media}
    files = {"common_records.jsonl": selected_records, "common_media.jsonl": selected_media,
             "ocr_document_profiles.jsonl": [r for r in profiles if r["record_id"] in record_ids],
             "institution_reference_texts.jsonl": [r for r in references if r.get("resource_id") in resource_ids]}
    for name, data in files.items():
        (destination / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in data), encoding="utf-8")
    (destination / "selection.json").write_text(json.dumps({"selected": len(selection), "item_types": len({r["item_type"] for r in selection}),
        "method": "Non-random round robin by catalogue item type, one declared image per record and distinct image URLs. Prefer page 10 when present.",
        "scope": "A method/heterogeneity check, not an unbiased estimate of full-catalogue image availability.",
        "records": selection}, indent=2), encoding="utf-8")
    config = json.loads((root / "module8_examples.json").read_text())
    for field, name in (("common_records_jsonl", "common_records.jsonl"), ("common_media_jsonl", "common_media.jsonl"),
                        ("ocr_document_profiles_jsonl", "ocr_document_profiles.jsonl"),
                        ("institution_reference_texts_jsonl", "institution_reference_texts.jsonl")):
        config[field] = str(destination / name)
    config.update(output_directory=str(destination / "module8/output"), log_directory=str(destination / "module8/log"))
    (root / "module8_diverse.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(json.dumps({"selected_images": len(selection), "item_types": len({r["item_type"] for r in selection})}), flush=True)


if __name__ == "__main__":
    main()
