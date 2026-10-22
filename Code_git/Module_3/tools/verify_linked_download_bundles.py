"""Check real portable download paths, schemas, IDs and saved reference files."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from jsonschema import Draft202012Validator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--mode", choices=["all", "example"], default="all")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    code = Path(__file__).resolve().parents[2]
    schemas = {name: Draft202012Validator(json.loads((code / "Module_7/schemas" / schema).read_text(encoding="utf-8")))
               for name, schema in [("common_record.json", "record-0.1.schema.json"),
                                    ("common_media.json", "media-0.1.schema.json"),
                                    ("ocr_document_profile.json", "ocr-profile-0.1.schema.json")]}
    successes, errors, providers = [], [], set()
    for line in (args.output_root / args.mode / "download_index.jsonl").open(encoding="utf-8"):
        entry = json.loads(line)
        try:
            image = args.output_root / entry["image_path"]
            directory = args.output_root / entry["bundle_directory"]
            assert image.is_file() and image.parent == directory
            assert sha256(image.read_bytes()).hexdigest() == entry["sha256"]
            values = {}
            for name, schema in schemas.items():
                values[name] = json.loads((directory / name).read_text(encoding="utf-8"))
                schema.validate(values[name])
                assert values[name]["record_id"] == entry["record_id"]
            media = values["common_media.json"]
            assert media["resource_id"] == entry["resource_id"]
            assert media["image"]["download_url"] == entry["final_url"]
            refs = directory / "institution_reference_texts.json"
            reference_rows = json.loads(refs.read_text(encoding="utf-8"))["reference_texts"] if refs.exists() else []
            assert len(reference_rows) == entry["reference_texts"]
            for ref in reference_rows:
                assert ref["resource_id"] == entry["resource_id"]
                assert ref["record_id"] == entry["record_id"]
                assert ref["canvas"]["id"] == media["canvas"]["id"]
                path = directory / ref["download"]["plain_text_file"]
                assert path.read_text(encoding="utf-8").strip()
            category = "with_reference" if reference_rows else "without_reference"
            assert category in directory.parts
            names = values["common_record.json"]["source"]["providers"]
            providers.update(p["provider_id"] for p in names)
            successes.append({"record_id": entry["record_id"], "resource_id": entry["resource_id"],
                              "providers": names, "image_path": str(image.resolve()), "reference_files": len(reference_rows)})
        except Exception as exc:
            errors.append({"resource_id": entry["resource_id"], "error": type(exc).__name__, "message": str(exc)})
    result = {"verified_bundles": len(successes), "schema_validated_json_files": 3 * len(successes),
              "provider_ids": sorted(providers), "errors": errors, "bundles": successes,
              "scope": "File integrity, schemas and page ownership; transcription accuracy and completeness are not certified."}
    args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "bundles"}))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
