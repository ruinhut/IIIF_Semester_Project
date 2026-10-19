"""Select further page-aligned references without repeating the initial cohorts."""

import argparse
import json
from pathlib import Path


def rows(path):
    return [json.loads(line) for line in path.open(encoding="utf-8")] if path.exists() else []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=150)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "evaluation/2026-10-16_blavatnik_investigation"
    source = root / "final/module7/output"
    output = root / "additional_references"
    output.mkdir(exist_ok=True)
    initial = rows(root / "reference_batch/candidate_manifests.jsonl")
    initial_record_ids = {r["manifest_id"] for r in initial}
    diverse = rows(root / "diverse_downloads/module8/output/all/download_index.jsonl")
    delivered_reference_ids = {r["resource_id"] for r in diverse if r.get("reference_texts")}
    all_references = rows(source / "institution_reference_texts.jsonl")
    references = [r for r in all_references if r["record_id"] not in initial_record_ids and r.get("resource_id") not in delivered_reference_ids]
    by_resource = {}
    for row in references:
        by_resource.setdefault(row["resource_id"], []).append(row)
    selected_ids = set(list(by_resource)[:args.limit])
    references = [r for r in references if r["resource_id"] in selected_ids]
    record_ids = {r["record_id"] for r in references}
    selected = {"common_records.jsonl": [r for r in rows(source / "common_records.jsonl") if r["record_id"] in record_ids],
        "common_media.jsonl": [r for r in rows(source / "common_media.jsonl") if r["resource_id"] in selected_ids],
        "ocr_document_profiles.jsonl": [r for r in rows(source / "ocr_document_profiles.jsonl") if r["record_id"] in record_ids],
        "institution_reference_texts.jsonl": references}
    for name, data in selected.items():
        (output / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in data), encoding="utf-8")
    (output / "selection.json").write_text(json.dumps({"all_exported_aligned_references": len(all_references),
        "remaining_unique_page_candidates": len(by_resource), "selected_pages": len(selected_ids), "limit": args.limit,
        "rule": "Exclude the original 99 attempted documents, including the recorded source 404, and already delivered reference pages in the diverse cohort. Retain those earlier attempts in combined statistics."}, indent=2), encoding="utf-8")
    config = json.loads((root / "module8_reference.json").read_text())
    for field, name in (("common_records_jsonl", "common_records.jsonl"), ("common_media_jsonl", "common_media.jsonl"),
                        ("ocr_document_profiles_jsonl", "ocr_document_profiles.jsonl"),
                        ("institution_reference_texts_jsonl", "institution_reference_texts.jsonl")):
        config[field] = str(output / name)
    config.update(output_directory=str(output / "module8/output"), log_directory=str(output / "module8/log"), require_reference_text=True)
    (root / "module8_additional_references.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(json.dumps({"selected_pages": len(selected_ids), "remaining_candidates": len(by_resource)}), flush=True)


if __name__ == "__main__":
    main()
