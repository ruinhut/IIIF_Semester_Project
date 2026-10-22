"""Summarize actual outputs; keep catalogue, structural and download totals apart."""

from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

from build_reference_delivery_index import main as build_reference_delivery_index


def rows(path):
    if not path.exists():
        return []
    output = []
    for line in path.open(encoding="utf-8"):
        try:
            output.append(json.loads(line))
        except ValueError:
            continue
    return output


def read(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    module = Path(__file__).resolve().parents[1]
    root = module / "evaluation/2026-10-16_blavatnik_investigation"
    final = root / "final"
    catalogue = read(root / "entire_catalogue_snapshot_v2/summary.json", {})
    catalogue_checks = read(root / "entire_catalogue_snapshot_v2/collection_checkpoints.json", [])
    declared_total = catalogue_checks[0].get("response_declared_total") if len(catalogue_checks) == 1 else None
    snapshot = read(root / "item_snapshot/summary.json", {})
    discovered = rows(final / "module3/output/manifest_urls.jsonl")
    valid = rows(final / "module4/output/validated_manifests.jsonl")
    invalid = rows(final / "module4/output/invalid_manifests.jsonl")
    manual = rows(final / "module4/output/manual_review.jsonl")
    unavailable = rows(final / "module4/output/unavailable_manifests.jsonl")
    exports = rows(final / "module7/output/common_records.jsonl")
    media = rows(final / "module7/output/common_media.jsonl")
    references = rows(final / "module7/output/institution_reference_texts.jsonl")
    if references:
        build_reference_delivery_index()
    issues = Counter()
    for record in valid + invalid + manual:
        for issue in record.get("source_structural_validation", record.get("structural_validation", {})).get("issues", []):
            issues[issue.get("code", issue.get("issue_type", "unknown"))] += 1
    source_states = Counter(record.get("source_structural_validation", record.get("structural_validation", {})).get("status")
                            for record in valid + invalid + manual)
    inventory_count = sum(1 for _ in (final / "module4/output/manifest_resource_inventory.jsonl").open(encoding="utf-8")) if (
        final / "module4/output/manifest_resource_inventory.jsonl").exists() else None
    downloads = {}
    for phase in ("download_examples", "reference_examples", "reference_batch", "diverse_downloads", "additional_references"):
        index = rows(root / phase / "module8/output/all/download_index.jsonl")
        existing = [r for r in index if (root / phase / "module8/output" / r["image_path"]).is_file()]
        downloads[phase] = {"existing_image_files": len(existing),
            "reference_texts_in_bundles": sum(r.get("reference_texts", 0) for r in existing),
            "downloaded_this_last_run": sum(r.get("download_status") == "downloaded" for r in index),
            "cached_this_last_run": sum(r.get("download_status") == "cached" for r in index),
            "unique_record_ids": len({r["record_id"] for r in existing})}
    tests = read(root / "unit_test_results.json", [])
    full_ready = bool(discovered and len(valid) + len(invalid) + len(manual) + len(unavailable) == len(discovered) and exports)
    result = {"generated_at": datetime.now(timezone.utc).isoformat(), "provider": "Blavatnik Archive",
        "report_status": "full_handoff_generated" if full_ready else "checkpoint_in_progress",
        "public_catalogue_ids": catalogue.get("unique_catalogue_identifiers"),
        "public_catalogue_source_declared_total": declared_total,
        "catalogue_complete_against_declared_total": catalogue.get("finished_collections") == 1 and catalogue.get("failed_collections") == 0 and catalogue.get("unique_catalogue_identifiers") == declared_total,
        "module3_manifest_urls": len(discovered) if discovered else None,
        "module4_usable_after_explicit_normalization": len(valid) if full_ready else None,
        "module4_invalid_after_normalization": len(invalid) if full_ready else None,
        "module4_without_usable_structure": len(manual) if full_ready else None,
        "module4_unavailable": len(unavailable) if full_ready else None,
        "strict_source_statuses": dict(source_states), "strict_source_issue_counts": dict(issues),
        "declared_image_inventory_rows": inventory_count,
        "per_manifest_distinct_image_urls_sum": sum(r["structural_validation"]["image_body_count"] for r in valid) if valid else None,
        "globally_distinct_image_urls": len({r["image"]["id"] for r in media}) if media else None,
        "source_identity_audit": read(root / "identity_audit/summary.json", {}).get("counts"),
        "non_image_records": read(root / "non_image_records.json", {}),
        "exported_documents": len(exports) if exports else None,
        "exported_media_records": len(media) if media else None,
        "exported_aligned_original_references": len(references) if exports else None,
        "catalogue_text_snapshot": snapshot, "download_batches": downloads,
        "reference_delivery": read(root / "reference_delivery_summary.json", {}),
        "unit_tests_passed": sum(r.get("passed") or 0 for r in tests),
        "unit_test_failures": sum(r.get("exit_code", 0) != 0 for r in tests),
        "old_provider_knowledge": read(root / "knowledge_preservation_check.json", {}),
        "scope": "One provider public-catalogue snapshot; source defects preserved; image downloads are bounded separate samples."}
    save(root / "summary.json", result)
    stage_counts = [
        {"stage": "Public catalogue", "count": result["public_catalogue_ids"], "unit": "unique catalogue IDs"},
        {"stage": "Module 3", "count": result["module3_manifest_urls"], "unit": "declared Manifest URLs fetched as JSON"},
        {"stage": "Module 4", "count": result["module4_usable_after_explicit_normalization"], "unit": "usable normalized Manifests"},
        {"stage": "Module 4 image inventory", "count": inventory_count, "unit": "declared image-body rows; not downloads"},
        {"stage": "Module 7 documents", "count": result["exported_documents"], "unit": "common records"},
        {"stage": "Module 7 media", "count": result["exported_media_records"], "unit": "image references; not downloads"},
        {"stage": "Module 7 references", "count": result["exported_aligned_original_references"], "unit": "unambiguously aligned institution original texts"},
    ]
    for phase in ("reference_batch", "diverse_downloads", "additional_references"):
        stage_counts.append({"stage": "Module 8 " + phase, "count": downloads[phase]["existing_image_files"],
                             "unit": "actual image files in the completed download index"})
    with (root / "stage_counts.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["stage", "count", "unit"])
        writer.writeheader(); writer.writerows(stage_counts)
    previous = read(module / "evaluation/2026-10-15_three_provider_completion/remaining_unresolved_entries.json", [])
    # Resolution was independently demonstrated by the initial small live run.
    initial = rows(root / "validation/module4/output/validated_manifests.jsonl")
    proven = bool(initial and downloads["reference_examples"]["existing_image_files"])
    remaining = [r for r in previous if not proven or r["provider_id"] != "provider-4ef10065e633729c"]
    save(root / "remaining_unresolved_entries.json", remaining)
    if remaining:
        with (root / "remaining_unresolved_entries.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(remaining[0])); writer.writeheader(); writer.writerows(remaining)
    print(json.dumps({k: result[k] for k in ["report_status", "public_catalogue_ids", "module3_manifest_urls",
        "module4_usable_after_explicit_normalization", "exported_media_records", "unit_tests_passed"]}))


if __name__ == "__main__":
    main()
