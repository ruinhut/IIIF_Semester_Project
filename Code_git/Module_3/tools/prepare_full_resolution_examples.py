"""Prepare readable audit samples from explicitly declared IIIF Image services.

This is an evaluation helper, not a change to the production M7 contract. It
retains the Manifest's original image ID/source ID, changes only the requested
download representation, saves service evidence, and archives earlier samples.
Run after complete_oct19_provider_completion.py, then run the generated M8
configuration. Never use it to bypass a restricted image service.
"""
import argparse
from copy import deepcopy
from datetime import datetime
import json
import math
from pathlib import Path
import sys
import time

module = Path(__file__).resolve().parents[1]
code = module.parent
sys.path.insert(0, str(module))
sys.path.insert(0, str(code / "Module_8"))
from iiif_resource_discovery.fetch import HttpFetcher
from iiif_image_downloader.iiif_service import image_api_candidates


def rows(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.evaluation_root.resolve()
    examples = root / "download_examples"
    current = rows(examples / "common_media.jsonl")
    records = rows(examples / "common_records.jsonl")
    by_record = {r["record_id"]: r for r in records}
    preferences = json.loads((root / "sample_selection.json").read_text(encoding="utf-8"))
    all_media = rows(root / "downstream/module7/output/common_media.jsonl")
    all_refs = rows(root / "downstream/module7/output/institution_reference_texts.jsonl")
    evidence = root / "image_service_checks"
    evidence.mkdir(exist_ok=True)
    fetcher = HttpFetcher(timeout_seconds=30, retries=1, max_response_bytes=8 * 1024 * 1024)
    selection, media = [], []
    for original in current:
        record = by_record[original["record_id"]]
        provider = record["source"]["providers"][0]
        sequence = preferences.get(provider["provider_id"], {}).get("canvas_sequence", original["sequence"])
        source = next(m for m in all_media if m["record_id"] == original["record_id"] and m["sequence"] == sequence)
        target = deepcopy(source)
        image = target["image"]
        assert image["info_json_url"], "No explicitly declared Image service"
        document = fetcher.fetch(image["info_json_url"])
        info = document.json()
        candidates = image_api_candidates(info, document.final_url)
        chosen = candidates[0]
        width, height = info.get("width"), info.get("height")
        if isinstance(width, int) and isinstance(height, int):
            ratio = min(1, info.get("maxWidth", width) / width, info.get("maxHeight", height) / height)
            if info.get("maxArea"):
                ratio = min(ratio, math.sqrt(info["maxArea"] / (width * height)))
            if ratio < 1:
                # Use a declared bound rather than requesting an unavailable full image.
                base = chosen.rsplit("/full/", 1)[0]
                chosen = base + f"/full/{max(1, int(width * ratio))},/0/default.jpg"
        save(evidence / (target["resource_id"] + ".json"), info)
        image["download_url"] = chosen
        media.append(target)
        selection.append({"provider_name": provider["provider_name"], "resource_id": target["resource_id"],
            "sequence": sequence, "original_manifest_image_url": source["image"]["download_url"],
            "info_json_url": document.final_url, "requested_full_resolution_url": chosen,
            "service_width": width, "service_height": height})
        time.sleep(0.6)
    identifiers = {m["resource_id"] for m in media}
    references = [r for r in all_refs if r.get("resource_id") in identifiers]
    media_path = examples / "full_resolution_common_media.jsonl"
    media_path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in media), encoding="utf-8")
    (examples / "institution_reference_texts.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in references), encoding="utf-8")
    config = json.loads((root / "module8_examples.json").read_text(encoding="utf-8"))
    config["common_media_jsonl"] = str(media_path)
    save(root / "module8_full_resolution_examples.json", config)
    save(root / "image_representation_selection.json", selection)
    old_output = examples / "module8/output"
    if old_output.exists():
        archive = root / "initial_examples" / datetime.now().strftime("%Y%m%d_%H%M%S")
        assert old_output.resolve().is_relative_to(root) and archive.resolve().is_relative_to(root)
        archive.parent.mkdir(exist_ok=True)
        old_output.rename(archive)
        print("Previous samples archived:", archive)
    print("Prepared", len(media), "service-backed images and", len(references), "reference descriptors.")


if __name__ == "__main__":
    main()
