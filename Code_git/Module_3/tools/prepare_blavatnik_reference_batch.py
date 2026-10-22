"""Prepare an auditable bounded image/transcription batch from real item JSON."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from iiif_resource_discovery.models import stable_manifest_id


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    module = Path(__file__).resolve().parents[1]
    code = module.parent
    root = module / "evaluation/2026-10-16_blavatnik_investigation"
    batch = root / "reference_batch"
    provider = json.loads((root / "provider.json").read_text(encoding="utf-8"))
    available = {}
    for line in (root / "item_snapshot/requests.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("has_original_transcript") and row.get("catalogue_page_count") == 1:
            available[row["identifier"]] = row
    # Keep the first observed items of each reported language in the sample.
    by_language = {}
    for row in available.values():
        by_language.setdefault(str(row.get("original_language")), []).append(row)
    chosen = []
    while any(by_language.values()) and len(chosen) < args.limit:
        for group in by_language.values():
            if group and len(chosen) < args.limit:
                chosen.append(group.pop(0))
    batch.mkdir(parents=True, exist_ok=True)
    handoffs = []
    for row in chosen:
        url = f'https://www.blavatnikarchive.org/api/data/es/iiif-manifest/{row["identifier"]}?type=mirador&site=BAF'
        handoffs.append({
            "module_3_schema_version": "2.1", "manifest_id": stable_manifest_id(url), "manifest_url": url,
            "resource_type": "Manifest", "providers": [{"provider_id": provider["provider_id"], "provider_name": provider["name"]}],
            "discovery_evidence": [{"discovery_method": "catalogue_reference_candidate_pending_module4_validation",
                "source_url": row["url"], "provider_id": provider["provider_id"], "provider_name": provider["name"]}],
        })
    (batch / "candidate_manifests.jsonl").write_text("".join(json.dumps(r) + "\n" for r in handoffs), encoding="utf-8")
    save(batch / "selection.json", {"available_single_page_text_candidates": len(available), "selected": len(chosen),
        "limit": args.limit, "selection": "Round robin by institution-reported original language; deterministic order within language.",
        "note": "Candidate selection only; Module 4 and Module 6 must still verify structure and actual image alignment.",
        "items": chosen})
    config4 = json.loads((root / "module4_final.json").read_text())
    config4.update(input_jsonl=str(batch / "candidate_manifests.jsonl"),
                   raw_manifest_directory=str(batch / "module4/raw_manifests"),
                   output_directory=str(batch / "module4/output"), log_directory=str(batch / "module4/log"))
    save(root / "module4_reference_batch.json", config4)
    for n in (5, 6, 7, 8):
        config = json.loads((root / f"module{n}_examples.json").read_text(encoding="utf-8"))
        config.update(output_directory=str(batch / f"module{n}/output"), log_directory=str(batch / f"module{n}/log"))
        if n == 5:
            config.update(validated_manifests_jsonl=str(batch / "module4/output/validated_manifests.jsonl"),
                          resource_inventory_jsonl=str(batch / "module4/output/manifest_resource_inventory.jsonl"))
        elif n == 6:
            sources = json.loads((code / "Module_6/config/provider_reference_sources.json").read_text(encoding="utf-8"))
            for source in sources["sources"]:
                source["cache_only"] = True
            save(root / "catalogue_reference_sources_snapshot_only.json", sources)
            config.update(research_manifests_jsonl=str(batch / "module5/output/research_manifests.jsonl"),
                          research_resource_inventory_jsonl=str(batch / "module5/output/research_resource_inventory.jsonl"),
                          provider_reference_sources=str(root / "catalogue_reference_sources_snapshot_only.json"),
                          catalogue_reference_cache_directory=str(root / "item_snapshot/cache"))
        elif n == 7:
            for field, filename in (("normalized_records_jsonl", "normalized_records.jsonl"),
                                    ("normalized_resources_jsonl", "normalized_resources.jsonl"),
                                    ("normalized_reference_texts_jsonl", "normalized_reference_texts.jsonl")):
                config[field] = str(batch / "module6/output" / filename)
        else:
            for field, filename in (("common_records_jsonl", "common_records.jsonl"),
                                    ("common_media_jsonl", "common_media.jsonl"),
                                    ("ocr_document_profiles_jsonl", "ocr_document_profiles.jsonl"),
                                    ("institution_reference_texts_jsonl", "institution_reference_texts.jsonl")):
                config[field] = str(batch / "module7/output" / filename)
            config["require_reference_text"] = True
        save(root / f"module{n}_reference_batch.json", config)
    print(json.dumps({"available_candidates": len(available), "selected": len(chosen)}))


if __name__ == "__main__":
    main()
