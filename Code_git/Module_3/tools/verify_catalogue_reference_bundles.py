"""Verify exported JSON schemas, foreign keys and exact original-text provenance."""

import argparse
import json
from pathlib import Path
import re
import sys

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Module_6"))
from iiif_metadata_normalizer.reference_text import clean_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module8-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--mode", choices=("all", "example"), default="all",
                        help="Select the downloader output index to verify")
    parser.add_argument("--allow-without-reference", action="store_true",
                        help="Check ordinary image bundles too; do not invent missing text")
    args = parser.parse_args()
    code = Path(__file__).resolve().parents[2]
    schemas = {name: Draft202012Validator(json.loads((code / "Module_7/schemas" / schema).read_text(encoding="utf-8")))
        for name, schema in (("common_record.json", "record-0.1.schema.json"),
                             ("common_media.json", "media-0.1.schema.json"),
                             ("ocr_document_profile.json", "ocr-profile-0.1.schema.json"))}
    bundles, errors, schema_files, reference_count = [], [], 0, 0
    for line in (args.module8_output / args.mode / "download_index.jsonl").read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        directory = (args.module8_output / entry["image_path"]).parent
        try:
            values = {}
            for filename, validator in schemas.items():
                value = json.loads((directory / filename).read_text(encoding="utf-8"))
                validator.validate(value)
                values[filename] = value
                schema_files += 1
            record = values["common_record.json"]
            media = values["common_media.json"]
            profile = values["ocr_document_profile.json"]
            assert record["record_id"] == media["record_id"] == profile["record_id"] == entry["record_id"]
            assert media["resource_id"] == entry["resource_id"]
            reference_path = directory / "institution_reference_texts.json"
            references = json.loads(reference_path.read_text(encoding="utf-8"))["reference_texts"] if reference_path.exists() else []
            assert references or args.allow_without_reference, "Reference batch must contain actual aligned texts"
            assert ("with_reference" if references else "without_reference") in directory.parts
            for reference in references:
                assert reference["record_id"] == record["record_id"]
                assert reference["resource_id"] == media["resource_id"]
                assert reference["canvas"]["id"] == media["canvas"]["id"]
                provenance = reference["provenance"]["catalogue_reference"]
                source = json.loads(Path(provenance["raw_json_path"]).read_text(encoding="utf-8"))["data"]
                assert len(source["pages"]) == 1
                image_id = source["pages"][0]["iIIFID"]
                assert image_id == provenance["page_identifier"]
                image_urls = [media["image"]["id"], *media["image"].get("service_urls", [])]
                assert any(re.search(r"(?<![A-Za-z0-9])" + re.escape(image_id) + r"(?![A-Za-z0-9])", url) for url in image_urls)
                expected = clean_text(source[provenance["text_field"]]).strip()
                exported = (directory / reference["download"]["plain_text_file"]).read_text(encoding="utf-8").strip()
                assert expected and expected == exported == reference["reference_text"]["inline_text"].strip()
                assert provenance["text_field"] == "originalTranscript"
                assert reference["reference_text"]["text_role"] == "original_transcription"
                reference_count += 1
            bundles.append({"record_id": entry["record_id"], "resource_id": entry["resource_id"],
                            "bundle_directory": str(directory.resolve()), "references": len(references)})
        except Exception as exc:
            errors.append({"directory": str(directory), "error_type": type(exc).__name__, "message": str(exc)})
    report = {"verified_bundles": len(bundles), "schema_validated_json_files": schema_files,
              "exact_original_text_and_image_matches": reference_count, "errors": errors, "bundles": bundles,
              "scope": "JSON schemas, IDs, Canvas/image hashes and exact source text; image decoding is checked separately."}
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k not in {"bundles"}}))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
