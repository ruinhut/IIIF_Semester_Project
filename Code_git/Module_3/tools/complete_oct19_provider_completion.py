"""Run the five-provider sample through Modules 5-8, retaining stage evidence."""

from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def rows(path):
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-root', type=Path, help='An isolated prepared evaluation directory')
    args = parser.parse_args()
    module = Path(__file__).resolve().parents[1]
    code = module.parent
    root = args.evaluation_root.resolve() if args.evaluation_root else module / "evaluation/2026-10-19_five_provider_completion"
    providers = json.loads((root / "providers.json").read_text(encoding="utf-8"))
    expected_ids = {p["provider_id"] for p in providers}
    source = root / "validation/module4/output"
    if (root / "revalidated/module4/output/validated_manifests.jsonl").exists():
        source = root / "revalidated/module4/output"
    validated = rows(source / "validated_manifests.jsonl")
    inventory = rows(source / "manifest_resource_inventory.jsonl")
    extra = root / "akon_check/module4/output"
    if (extra / "validated_manifests.jsonl").exists():
        validated += rows(extra / "validated_manifests.jsonl")
        inventory += rows(extra / "manifest_resource_inventory.jsonl")
    validated = list({r["manifest_id"]: r for r in validated}.values())
    inventory = list({(r["manifest_id"], r["canvas_id"], r["body_id"]): r for r in inventory}.values())
    for filename, values in [("combined_validated_manifests.jsonl", validated), ("combined_resource_inventory.jsonl", inventory)]:
        (root / filename).write_text("".join(json.dumps(v, ensure_ascii=False) + "\n" for v in values), encoding="utf-8")
    valid_ids = {p["provider_id"] for row in validated for p in row["providers"]}
    if not expected_ids <= valid_ids:
        raise RuntimeError("Not all five providers have a usable Manifest; inspect Module 4 first")
    full = root / "downstream"
    examples = root / "download_examples"
    configs = {
        5: {"validated_manifests_jsonl": str(root / "combined_validated_manifests.jsonl"),
            "resource_inventory_jsonl": str(root / "combined_resource_inventory.jsonl"),
            "module_4_directory": str(root), "policy_file": str(code / "Module_5/policies/automatic-2026-09-29.json")},
        6: {"research_manifests_jsonl": str(full / "module5/output/research_manifests.jsonl"),
            "research_resource_inventory_jsonl": str(full / "module5/output/research_resource_inventory.jsonl"),
            "module_4_directory": str(root)},
        7: {"normalized_records_jsonl": str(full / "module6/output/normalized_records.jsonl"),
            "normalized_resources_jsonl": str(full / "module6/output/normalized_resources.jsonl"),
            "normalized_reference_texts_jsonl": str(full / "module6/output/normalized_reference_texts.jsonl"),
            "profile_json": str(code / "Module_7/profiles/provisional-0.1.json"),
            "record_schema_json": str(code / "Module_7/schemas/record-0.1.schema.json"),
            "media_schema_json": str(code / "Module_7/schemas/media-0.1.schema.json"),
            "ocr_profile_schema_json": str(code / "Module_7/schemas/ocr-profile-0.1.schema.json")}}
    commands = {5: "iiif_rights_filter", 6: "iiif_metadata_normalizer", 7: "iiif_common_exporter"}
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    stages = json.loads((root / "downstream_stage_results.json").read_text(encoding="utf-8")) if (root / "downstream_stage_results.json").exists() else []

    def execute(number, arguments):
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run([sys.executable, *arguments], cwd=code / f"Module_{number}", env=environment,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        stages.append({"module": number, "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
                       "arguments": arguments, "exit_code": result.returncode, "output": result.stdout})
        save(root / "downstream_stage_results.json", stages)
        print(result.stdout, flush=True)
        if result.returncode:
            raise RuntimeError(f"Module {number} failed; see downstream_stage_results.json")

    for number, config in configs.items():
        config.update(output_directory=str(full / f"module{number}/output"), log_directory=str(full / f"module{number}/log"))
        path = root / f"module{number}_validation.json"
        save(path, config)
        execute(number, ["-m", commands[number], "run", "--config", str(path)])
    output = full / "module7/output"
    records = rows(output / "common_records.jsonl")
    media = rows(output / "common_media.jsonl")
    profiles = rows(output / "ocr_document_profiles.jsonl")
    references = rows(output / "institution_reference_texts.jsonl")
    reference_ids = {r.get("resource_id") for r in references}
    selected_records, selected_media = [], []
    preferences = json.loads((root / "sample_selection.json").read_text(encoding="utf-8")) if (root / "sample_selection.json").exists() else {}
    for provider_id in [p["provider_id"] for p in providers]:
        eligible = [r for r in records if any(p["provider_id"] == provider_id for p in r["source"]["providers"])]
        preferred = preferences.get(provider_id, {}).get("manifest_url_pattern")
        if preferred:
            eligible = [r for r in eligible if re.search(preferred, r["source"]["manifest_url"])]
        eligible_ids = {r["record_id"] for r in eligible}
        eligible_media = [m for m in media if m["record_id"] in eligible_ids]
        if not eligible_media:
            raise RuntimeError("No exported media for " + provider_id)
        # Prefer a page with source-linked text, otherwise an interior image.
        reference_pages = [m for m in eligible_media if m["resource_id"] in reference_ids]
        if reference_pages:
            chosen = reference_pages[0]
        else:
            same_document = [m for m in eligible_media if m["record_id"] == eligible_media[0]["record_id"]]
            chosen = same_document[min(9, len(same_document) - 1)]
        selected_media.append(chosen)
        selected_records.append(next(r for r in eligible if r["record_id"] == chosen["record_id"]))
    selected_ids = {r["record_id"] for r in selected_records}
    resource_ids = {m["resource_id"] for m in selected_media}
    examples.mkdir(exist_ok=True)
    for name, values in [("common_records.jsonl", selected_records), ("common_media.jsonl", selected_media),
                         ("ocr_document_profiles.jsonl", [p for p in profiles if p["record_id"] in selected_ids]),
                         ("institution_reference_texts.jsonl", [r for r in references if r.get("resource_id") in resource_ids])]:
        (examples / name).write_text("".join(json.dumps(v, ensure_ascii=False) + "\n" for v in values), encoding="utf-8")
    config8 = {key: str(examples / name) for key, name in [("common_records_jsonl", "common_records.jsonl"),
        ("common_media_jsonl", "common_media.jsonl"), ("ocr_document_profiles_jsonl", "ocr_document_profiles.jsonl"),
        ("institution_reference_texts_jsonl", "institution_reference_texts.jsonl")]}
    config8.update(output_directory=str(examples / "module8/output"), log_directory=str(examples / "module8/log"),
                   request={"timeout_seconds": 40, "retries": 1, "request_delay_seconds": 0.7,
                            "max_image_bytes": 104857600, "max_reference_text_bytes": 10485760})
    path = root / "module8_examples.json"
    save(path, config8)
    execute(8, ["-m", "iiif_image_downloader", "download-all", "--config", str(path)])


if __name__ == "__main__":
    main()
