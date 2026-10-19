"""Run the isolated full-catalogue handoff after audited discovery completes."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--refresh-references", action="store_true",
                        help="Rerun Modules 6 and 7 against the now larger explicit item snapshot")
    args = parser.parse_args()
    module = Path(__file__).resolve().parents[1]
    code = module.parent
    root = module / "evaluation/2026-10-16_blavatnik_investigation"
    final = root / "final"
    discovered = final / "module3/output/manifest_urls.jsonl"
    while not discovered.exists():
        if not args.wait:
            raise RuntimeError("Audited final discovery has not completed")
        if datetime.now(timezone.utc).hour >= 19:
            raise RuntimeError("Discovery did not complete before the downstream checkpoint deadline")
        print("Waiting for final audited Module 3 output", flush=True)
        time.sleep(30)
    history_path = final / "downstream_stage_results.json"
    stages = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    def command(arguments, cwd=None):
        start = datetime.now(timezone.utc).isoformat()
        result = subprocess.run([sys.executable, *map(str, arguments)], cwd=cwd, env=environment,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        event = {"started_at": start, "finished_at": datetime.now(timezone.utc).isoformat(),
                 "arguments": list(map(str, arguments)), "cwd": str(cwd), "exit_code": result.returncode,
                 "output": result.stdout}
        stages.append(event)
        save(final / "downstream_stage_results.json", stages)
        print(result.stdout, flush=True)
        if result.returncode:
            raise RuntimeError("Downstream stage failed; see downstream_stage_results.json")

    for n in (5, 6, 7):
        config = json.loads((root / f"module{n}_examples.json").read_text(encoding="utf-8"))
        config.update(output_directory=str(final / f"module{n}/output"), log_directory=str(final / f"module{n}/log"))
        if n == 5:
            config.update(validated_manifests_jsonl=str(final / "module4/output/validated_manifests.jsonl"),
                          resource_inventory_jsonl=str(final / "module4/output/manifest_resource_inventory.jsonl"))
        elif n == 6:
            config.update(research_manifests_jsonl=str(final / "module5/output/research_manifests.jsonl"),
                          research_resource_inventory_jsonl=str(final / "module5/output/research_resource_inventory.jsonl"),
                          catalogue_reference_cache_directory=str(root / "item_snapshot/cache"))
            sources = json.loads((code / "Module_6/config/provider_reference_sources.json").read_text(encoding="utf-8"))
            for source in sources["sources"]:
                source["cache_only"] = True
            save(root / "catalogue_reference_sources_snapshot_only.json", sources)
            config["provider_reference_sources"] = str(root / "catalogue_reference_sources_snapshot_only.json")
        else:
            for field, filename in (("normalized_records_jsonl", "normalized_records.jsonl"),
                                    ("normalized_resources_jsonl", "normalized_resources.jsonl"),
                                    ("normalized_reference_texts_jsonl", "normalized_reference_texts.jsonl")):
                config[field] = str(final / "module6/output" / filename)
        save(root / f"module{n}_final.json", config)
    # Prepare the full Module 8 contract, but do not start a 50,000-image job.
    download_config = json.loads((root / "module8_examples.json").read_text(encoding="utf-8"))
    for field, filename in (("common_records_jsonl", "common_records.jsonl"),
                            ("common_media_jsonl", "common_media.jsonl"),
                            ("ocr_document_profiles_jsonl", "ocr_document_profiles.jsonl"),
                            ("institution_reference_texts_jsonl", "institution_reference_texts.jsonl")):
        download_config[field] = str(final / "module7/output" / filename)
    download_config.update(output_directory=str(final / "module8/output"), log_directory=str(final / "module8/log"))
    save(root / "module8_final.json", download_config)
    if not args.refresh_references:
        command([module / "tools/import_discovery_snapshot_to_module4.py", "--input", discovered,
                 "--trace", final / "module3/requests.jsonl", "--raw-directory", final / "module4/raw_manifests"])
        command(["-m", "iiif_manifest_validator", "run", "--config", root / "module4_final.json"], code / "Module_4")
        command(["-m", "iiif_rights_filter", "run", "--config", root / "module5_final.json"], code / "Module_5")
    command(["-m", "iiif_metadata_normalizer", "run", "--config", root / "module6_final.json"], code / "Module_6")
    command(["-m", "iiif_common_exporter", "run", "--config", root / "module7_final.json"], code / "Module_7")


if __name__ == "__main__":
    main()
