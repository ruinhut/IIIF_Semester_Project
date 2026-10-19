"""Decode downloaded images and compare pixel dimensions with source declarations.

This optional QA utility needs Pillow; it is not a runtime downloader dependency.
It does not edit, resize or replace the stored image files.
"""

import argparse
import json
from pathlib import Path

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module8-output", type=Path, required=True)
    parser.add_argument("--raw-manifest-directory", type=Path, required=True)
    parser.add_argument("--additional-raw-manifest-directory", type=Path, action="append", default=[],
                        help="Also search separately retained follow-up validation caches")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--mode", choices=("all", "example"), default="all",
                        help="Select the downloader output index to verify")
    args = parser.parse_args()
    checks, errors = [], []
    for line in (args.module8_output / args.mode / "download_index.jsonl").open(encoding="utf-8"):
        entry = json.loads(line)
        image_path = args.module8_output / entry["image_path"]
        try:
            with Image.open(image_path) as image:
                image.verify()
            with Image.open(image_path) as image:
                image.load()
                dimensions, image_format = image.size, image.format
            media = json.loads((image_path.parent / "common_media.json").read_text(encoding="utf-8"))
            raw_path = next((directory / (entry["record_id"] + ".json")
                             for directory in [args.raw_manifest_directory, *args.additional_raw_manifest_directory]
                             if (directory / (entry["record_id"] + ".json")).is_file()), None)
            if raw_path is None:
                raise FileNotFoundError("No source Manifest cache for " + entry["record_id"])
            manifest = json.loads(raw_path.read_bytes())
            canvases = manifest.get("items", []) if "items" in manifest else [c for s in manifest.get("sequences", []) for c in s.get("canvases", [])]
            canvas = next(c for c in canvases if c.get("id", c.get("@id")) == media["canvas"]["id"])
            bodies = [a.get("resource", {}) for a in canvas.get("images", [])]
            bodies += [a.get("body", {}) for p in canvas.get("items", []) for a in p.get("items", [])]
            body = next((b for b in bodies if isinstance(b, dict) and b.get("id", b.get("@id")) == media["image"]["id"]), {})
            declared = (body.get("width", canvas.get("width")), body.get("height", canvas.get("height")))
            checks.append({"record_id": entry["record_id"], "resource_id": entry["resource_id"],
                           "image_path": str(image_path.resolve()), "format": image_format,
                           "width": dimensions[0], "height": dimensions[1], "declared_dimensions": declared,
                           "dimensions_match": dimensions == declared, "bytes": image_path.stat().st_size})
        except Exception as exc:
            errors.append({"path": str(image_path), "error_type": type(exc).__name__, "message": str(exc)})
    result = {"decoded_images": len(checks), "decode_errors": errors,
              "dimension_mismatches": [r for r in checks if not r["dimensions_match"]], "images": checks}
    args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "images"}), flush=True)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
