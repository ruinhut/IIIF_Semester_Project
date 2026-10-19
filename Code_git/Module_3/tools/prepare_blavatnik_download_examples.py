"""Prepare linked downstream samples from validated Blavatnik Manifests."""

import json
from pathlib import Path


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    module = Path(__file__).resolve().parents[1]
    code = module.parent
    root = module / "evaluation/2026-10-16_blavatnik_investigation"
    output = root / "download_examples"
    output.mkdir(exist_ok=True)
    source = root / "validation/module4/output"
    manifests = read_rows(source / "validated_manifests.jsonl")
    inventory = read_rows(source / "manifest_resource_inventory.jsonl")
    selected = {}
    resources = []
    for manifest in manifests:
        provider_id = manifest["manifest_id"]
        if len(selected) >= 10:
            continue
        candidates = [row for row in inventory if row["manifest_id"] == manifest["manifest_id"]]
        if candidates:
            selected[provider_id] = manifest
            # Prefer an interior page when present; covers often contain no text.
            resources.append(candidates[min(9, len(candidates) - 1)])
    if not selected:
        raise RuntimeError(f"Need image-bearing objects from at least one validated Manifest; found {len(selected)}")
    for filename, rows in (("selected_manifests.jsonl", selected.values()), ("selected_images.jsonl", resources)):
        (output / filename).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    configs = {
        5: {"validated_manifests_jsonl": str(output / "selected_manifests.jsonl"),
            "resource_inventory_jsonl": str(output / "selected_images.jsonl"), "module_4_directory": str(root),
            "policy_file": str(code / "Module_5/policies/automatic-2026-09-29.json")},
        6: {"research_manifests_jsonl": str(output / "module5/output/research_manifests.jsonl"),
            "research_resource_inventory_jsonl": str(output / "module5/output/research_resource_inventory.jsonl"),
            "module_4_directory": str(root)},
        7: {"normalized_records_jsonl": str(output / "module6/output/normalized_records.jsonl"),
            "normalized_resources_jsonl": str(output / "module6/output/normalized_resources.jsonl"),
            "normalized_reference_texts_jsonl": str(output / "module6/output/normalized_reference_texts.jsonl"),
            "profile_json": str(code / "Module_7/profiles/provisional-0.1.json"),
            "record_schema_json": str(code / "Module_7/schemas/record-0.1.schema.json"),
            "media_schema_json": str(code / "Module_7/schemas/media-0.1.schema.json"),
            "ocr_profile_schema_json": str(code / "Module_7/schemas/ocr-profile-0.1.schema.json")},
        8: {"common_records_jsonl": str(output / "module7/output/common_records.jsonl"),
            "common_media_jsonl": str(output / "module7/output/common_media.jsonl"),
            "ocr_document_profiles_jsonl": str(output / "module7/output/ocr_document_profiles.jsonl"),
            "institution_reference_texts_jsonl": str(output / "module7/output/institution_reference_texts.jsonl"),
            "require_reference_text": False,
            "request": {"timeout_seconds": 40, "retries": 1, "request_delay_seconds": 0.25,
                        "max_image_bytes": 100 * 1024 * 1024, "max_reference_text_bytes": 10 * 1024 * 1024}},
    }
    for number, config in configs.items():
        config.update(output_directory=str(output / f"module{number}/output"), log_directory=str(output / f"module{number}/log"))
        (root / f"module{number}_examples.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print("Prepared up to ten validated objects and one image per object for the real downstream modules.")


if __name__ == "__main__":
    main()
