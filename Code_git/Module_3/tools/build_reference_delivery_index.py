"""Reconcile every exported reference page against real downloads and failures."""

from collections import Counter, defaultdict
import csv
import json
from pathlib import Path


def rows(path):
    return [json.loads(line) for line in path.open(encoding="utf-8")] if path.exists() else []


def main():
    root = Path(__file__).resolve().parents[1] / "evaluation/2026-10-16_blavatnik_investigation"
    references = rows(root / "final/module7/output/institution_reference_texts.jsonl")
    delivered, failed = {}, {}
    for phase in ["reference_examples", "reference_batch", "diverse_downloads", "additional_references"]:
        output = root / phase / "module8/output"
        for row in rows(output / "all/download_index.jsonl"):
            if not row.get("reference_texts"):
                continue
            image = output / row["image_path"]
            texts = image.parent / "institution_reference_texts.json"
            if image.is_file() and texts.is_file():
                delivered[row["resource_id"]] = {**row, "absolute_image_path": str(image.resolve()),
                                               "absolute_reference_index": str(texts.resolve())}
        for row in rows(output / "all/failed_downloads.jsonl"):
            failed[row["resource_id"]] = row
    by_page = {}
    for row in references:
        by_page.setdefault(row["resource_id"], row)
    entries, states, hashes, urls = [], Counter(), defaultdict(list), set()
    for resource_id, reference in by_page.items():
        success, failure = delivered.get(resource_id), failed.get(resource_id)
        status = "downloaded_with_reference" if success else "image_failed" if failure else "not_yet_attempted"
        states[status] += 1
        if success:
            hashes[success["sha256"]].append(resource_id)
            urls.add(success["final_url"])
        entries.append({"record_id": reference["record_id"], "resource_id": resource_id,
            "manifest_url": reference["provenance"]["source_manifest_url"], "canvas_url": reference["canvas"]["id"],
            "institution_reference_url": reference["reference_text"]["id"],
            "institution_reference_language": reference["reference_text"].get("language"), "status": status,
            "image_path": success["absolute_image_path"] if success else "",
            "institution_reference_index_path": success["absolute_reference_index"] if success else "",
            "image_sha256": success["sha256"] if success else "",
            "error_type": failure.get("error_type") if failure and not success else "",
            "http_status": failure.get("status_code") if failure and not success else ""})
    with (root / "reference_delivery_index.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(entries[0])); writer.writeheader(); writer.writerows(entries)
    result = {"exported_reference_rows": len(references), "unique_aligned_page_candidates": len(by_page),
        "delivery_statuses": dict(states), "distinct_delivered_image_urls": len(urls),
        "distinct_delivered_file_hashes": len(hashes),
        "identical_file_groups": [ids for ids in hashes.values() if len(ids) > 1],
        "note": "Original source failures remain in the denominator. Hashes audit duplicate downloaded files; they never reject new Manifests."}
    (root / "reference_delivery_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "identical_file_groups"}), flush=True)


if __name__ == "__main__":
    main()
