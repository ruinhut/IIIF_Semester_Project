"""Run fresh live Module 1-8 cases and verify reference/image ownership.

This is a bounded integration test with explicit real Manifest seeds, not a
provider-discovery benchmark or a complete institutional harvest. Production
configuration and earlier datasets are never overwritten.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator

CODE = Path(__file__).resolve().parents[2]
PACKAGES = ["iiif_provider_census", "iiif_entry_validator", "iiif_resource_discovery",
            "iiif_manifest_validator", "iiif_rights_filter", "iiif_metadata_normalizer",
            "iiif_common_exporter", "iiif_image_downloader"]
CASES = [
    ("bsb_hocr", "Bavarian State Library", "https://www.digitale-sammlungen.de/",
     "https://api.digitale-sammlungen.de/iiif/presentation/v2/bsb12188327/manifest", True),
    ("fromthepage_transcription", "FromThePage", "https://fromthepage.com/",
     "https://fromthepage.com/iiif/123/manifest", True),
    ("epfl_without_reference", "EPFL Plume", "https://plume.epfl.ch/",
     "https://plume.epfl.ch/iiif/3/44/manifest", False),
]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rows(path):
    if not path.is_file():
        raise AssertionError(f"Missing expected exchange file: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prepare(root):
    template_root = CODE / "Pipeline_Runner/configs/fragmentarium"
    for slug, name, homepage, manifest, has_reference in CASES:
        case = root / slug
        config_dir = case / "configs"
        seed = case / "inputs/providers.json"
        save(seed, {"source": {"source_type": "manual", "source_url": manifest},
                    "providers": [{"name": name, "institution_url": homepage,
                                   "discovery_endpoint": manifest, "discovery_type": "manifest"}]})
        save(config_dir / "empty_knowledge.json", {"knowledge_base_version": "1.0", "providers": []})
        configs = {}
        for number in range(1, 9):
            template = template_root / f"module_{number}.json"
            value = json.loads(template.read_text(encoding="utf-8-sig"))
            # Resolve the existing template's paths before relocating it.
            for key, item in list(value.items()):
                if isinstance(item, str) and key not in {"schema_version"}:
                    value[key] = str((template.parent / item).resolve())
            value["output_directory"] = str(case / f"module_{number}/output")
            value["log_directory"] = str(case / f"module_{number}/log")
            if "network" in value:
                value["network"].update(timeout_seconds=30, retries=1, max_response_bytes=67108864)
            if "run" in value:
                value["run"]["max_records"] = None
            configs[number] = value
        configs[1].update(registry_sources=[], manual_sources=[str(seed)])
        configs[2]["input_jsonl"] = str(case / "module_1/output/selected_providers.jsonl")
        configs[3].update(input_jsonl=str(case / "module_2/output/checked_entry_points.jsonl"),
                          curated_endpoints=str(config_dir / "empty_knowledge.json"),
                          knowledge_base=str(config_dir / "empty_knowledge.json"))
        configs[3]["limits"]["max_manifests_per_provider"] = 1
        configs[4].update(input_jsonl=str(case / "module_3/output/manifest_urls.jsonl"),
                          raw_manifest_directory=str(case / "module_4/raw_manifests"))
        configs[4]["run"].update(force_refresh=True, max_records=1)
        for number in (5, 6):
            configs[number]["module_4_directory"] = str(config_dir)
        configs[5].update(validated_manifests_jsonl=str(case / "module_4/output/validated_manifests.jsonl"),
                          resource_inventory_jsonl=str(case / "module_4/output/manifest_resource_inventory.jsonl"))
        configs[6].update(research_manifests_jsonl=str(case / "module_5/output/research_manifests.jsonl"),
                          research_resource_inventory_jsonl=str(case / "module_5/output/research_resource_inventory.jsonl"))
        for key, filename in [("normalized_records_jsonl", "normalized_records.jsonl"),
                              ("normalized_resources_jsonl", "normalized_resources.jsonl"),
                              ("normalized_reference_texts_jsonl", "normalized_reference_texts.jsonl")]:
            configs[7][key] = str(case / "module_6/output" / filename)
        for key in ["common_records", "common_media", "ocr_document_profiles", "institution_reference_texts"]:
            configs[8][key + "_jsonl"] = str(case / "module_7/output" / (key + ".jsonl"))
        configs[8].update(require_reference_text=has_reference, overwrite_existing=True)
        configs[8]["request"].update(timeout_seconds=30, retries=1)
        for number, value in configs.items():
            save(config_dir / f"module_{number}.json", value)
        save(case / "pipeline.json", {"log_directory": str(case / "pipeline_logs"), "modules": [
            {"number": n, "name": f"Module {n}", "directory": str(CODE / f"Module_{n}"),
             "package": package, "config": str(config_dir / f"module_{n}.json"),
             "command": "download-example" if n == 8 else "run",
             "arguments": ["--institution", "all"] if n == 1 else []}
            for n, package in enumerate(PACKAGES, 1)]})


def verify(case, has_reference, pixel_python):
    record_rows = rows(case / "module_7/output/common_records.jsonl")
    media = rows(case / "module_7/output/common_media.jsonl")
    profiles = rows(case / "module_7/output/ocr_document_profiles.jsonl")
    refs = rows(case / "module_7/output/institution_reference_texts.jsonl")
    for dataset, schema in [(record_rows, "record-0.1.schema.json"),
                            (media, "media-0.1.schema.json"),
                            (profiles, "ocr-profile-0.1.schema.json")]:
        validator = Draft202012Validator(json.loads((CODE / "Module_7/schemas" / schema).read_text(encoding="utf-8")))
        for row in dataset:
            validator.validate(row)
    records = {r["record_id"] for r in record_rows}
    resources = {r["resource_id"]: r for r in media}
    assert records and media and len(profiles) == len(record_rows)
    assert len(resources) == len(media), "Duplicate resource IDs"
    assert len(records) == len(record_rows), "Duplicate document IDs"
    assert {r["record_id"] for r in profiles} == records
    input_refs = rows(case / "module_6/output/normalized_reference_texts.jsonl")
    assert {r["reference_text_id"] for r in input_refs} == {r["reference_text_id"] for r in refs}, "Reference rows lost between Modules 6 and 7"
    assert all(r["record_id"] in records for r in media + profiles + refs)
    paired = [r for r in refs if r.get("resource_id")]
    for ref in paired:
        page = resources[ref["resource_id"]]
        assert ref["record_id"] == page["record_id"]
        assert ref["canvas"]["id"] == page["canvas"]["id"]
    output = case / "module_8/output"
    index = rows(output / "example/download_index.jsonl")
    assert len(index) == 1
    download_summary = json.loads((output / "example/download_summary.json").read_text(encoding="utf-8"))
    assert download_summary["failed_images"] == 0
    assert download_summary["reference_text_failures"] == 0
    assert download_summary["cached_images"] == 0, "Acceptance requires fresh downloads"
    expected = "with_reference" if has_reference else "without_reference"
    assert index[0]["output_category"] == expected
    assert bool(index[0]["reference_texts"]) == has_reference
    for category in ("with_reference", "without_reference", "reference_failed"):
        bundles = list((output / "example" / category).rglob("common_media.json"))
        assert len(bundles) == (1 if category == expected else 0), (category, bundles)
    for number, files in {3: ["unresolved_providers.jsonl"],
                          4: ["invalid_manifests.jsonl", "unavailable_manifests.jsonl"],
                          6: ["failed_records.jsonl"],
                          7: ["rejected_records.jsonl", "rejected_media.jsonl", "rejected_reference_texts.jsonl"]}.items():
        assert all(not rows(case / f"module_{number}/output" / f) for f in files)
    logs = sorted((case / "pipeline_logs").glob("*.json"), key=lambda p: p.stat().st_mtime)
    latest = json.loads(logs[-1].read_text(encoding="utf-8"))
    assert latest["status"] == "completed" and latest["modules_run"] == list(range(1, 9))
    assert all(r["return_code"] == 0 for r in latest["module_results"])
    for tool, arguments, python in [
        ("verify_linked_download_bundles.py", ["--output-root", str(output)], sys.executable),
        ("verify_downloaded_pixels.py", ["--module8-output", str(output),
          "--raw-manifest-directory", str(case / "module_4/raw_manifests")], pixel_python),
    ]:
        subprocess.run([str(python), str(CODE / "Module_3/tools" / tool), *arguments,
                        "--mode", "example", "--report", str(case / tool.replace(".py", ".json"))], check=True)
    return {"case": case.name, "modules_completed": 8,
            "schema_validated_export_rows": len(record_rows) + len(media) + len(profiles),
            "common_records": len(record_rows), "common_media": len(media),
            "ocr_profiles": len(profiles), "declared_reference_rows": len(refs),
            "page_linked_reference_rows": len(paired), "downloaded_images": len(index),
            "downloaded_reference_variants": index[0]["reference_texts"], "category": expected,
            "bundle_directory": str(output / index[0]["bundle_directory"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--pixel-python", type=Path, default=Path(sys.executable))
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    root = (args.output_root or CODE / "Pipeline_Runner/data" /
            ("full_acceptance_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not args.verify_only:
        prepare(root)
    print(f"Acceptance output: {root}", flush=True)
    if args.prepare_only:
        return
    results = []
    for slug, _, _, _, has_reference in CASES:
        case = root / slug
        if not args.verify_only:
            print(f"\nLive full-chain case: {slug}", flush=True)
            result = subprocess.run([sys.executable, "-m", "iiif_pipeline_runner", "--config",
                                     str(case / "pipeline.json")], cwd=CODE / "Pipeline_Runner",
                                    capture_output=True, text=True, encoding="utf-8")
            (case / "pipeline_console.txt").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
            if result.returncode:
                print(result.stderr, flush=True)
                raise RuntimeError(f"Full-chain case failed: {slug}; see pipeline_console.txt")
        result = verify(case, has_reference, args.pixel_python)
        results.append(result)
        save(root / "acceptance_results.json", results)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    with (root / "acceptance_results.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    inventory = []
    for slug, *_ in CASES:
        for number in range(1, 9):
            config = json.loads((root / slug / f"configs/module_{number}.json").read_text(encoding="utf-8"))
            inputs = {k: v for k, v in config.items() if k.endswith("_jsonl") or k in {"registry_sources", "manual_sources"}}
            output = root / slug / f"module_{number}/output"
            pattern = "example/*.jsonl" if number == 8 else "*.jsonl"
            for path in sorted(output.glob(pattern)):
                inventory.append({"case": slug, "module": number,
                                  "inputs": json.dumps(inputs, ensure_ascii=False),
                                  "output_file": str(path), "rows": len(rows(path)),
                                  "log_directory": str(root / slug / f"module_{number}/log")})
    with (root / "module_input_output_inventory.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(inventory[0]))
        writer.writeheader()
        writer.writerows(inventory)
    print("PASS: three live full chains, linked JSON schemas, pixel decoding and reference routing.", flush=True)


if __name__ == "__main__":
    main()
