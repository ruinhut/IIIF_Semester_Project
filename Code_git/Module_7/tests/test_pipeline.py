import json
from pathlib import Path

from iiif_common_exporter.pipeline import run_pipeline


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _source():
    return {
        "module_6_schema_version": "1.0", "manifest_id": "m1", "quality": {"status": "partial", "missing_fields": ["date"]}, "pipeline_versions": {}, "normalization": {},
        "normalized_metadata": {
            "identifier": {"primary": "https://example.org/m1", "values": []}, "title": {"preferred": "Object", "values": []}, "description": {"preferred": None, "values": []},
            "creators": [], "dates": [], "places": [], "subjects": [], "types": [], "languages": [],
            "rights": {"category": "open_license", "decision": "allow", "display_label": {}, "policy_version": "p1", "evidence": []},
            "source": {"manifest_id": "m1", "manifest_url": "https://example.org/m1", "declared_manifest_id": "https://example.org/m1", "presentation_version": "3", "providers": [{"provider_id": "p1", "provider_name": "P"}], "discovery_evidence": []},
        },
    }


def _resource(record_id="m1", resource_id="r1"):
    return {"resource_id": resource_id, "manifest_id": record_id, "canvas_index": 0, "canvas_id": "c1", "canvas_label": "1", "body_id": "i1", "body_type": "Image", "body_format": "image/jpeg", "image_service_urls": [], "rights_category": "open_license", "rights_decision": "allow", "rights_policy_version": "p1", "manifest_url": "https://example.org/m1"}


def _prepare(tmp_path: Path, records, resources):
    records_path, resources_path = tmp_path / "records.jsonl", tmp_path / "resources.jsonl"
    _write_jsonl(records_path, records); _write_jsonl(resources_path, resources)
    profile = {"profile_version": "provisional-0.1", "record_schema_version": "iiif-time-atlas-record-0.1", "media_schema_version": "iiif-time-atlas-media-0.1"}
    for name, value in (("profile.json", profile), ("record.json", {}), ("media.json", {})):
        (tmp_path / name).write_text(json.dumps(value), encoding="utf-8")
    config = {"normalized_records_jsonl": str(records_path), "normalized_resources_jsonl": str(resources_path), "profile_json": str(tmp_path / "profile.json"), "record_schema_json": str(tmp_path / "record.json"), "media_schema_json": str(tmp_path / "media.json"), "output_directory": str(tmp_path / "out"), "log_directory": str(tmp_path / "logs")}
    path = tmp_path / "config.json"; path.write_text(json.dumps(config), encoding="utf-8"); return path


def test_pipeline_writes_linked_bundle_and_checksums(tmp_path):
    summary = run_pipeline(_prepare(tmp_path, [_source()], [_resource()]))
    assert summary["valid_records"] == 1 and summary["valid_media"] == 1
    bundle = json.loads((tmp_path / "out" / "dataset_manifest.json").read_text())
    assert len(bundle["files"]) == 6
    assert all(len(item["sha256"]) == 64 for item in bundle["files"])
    media = json.loads((tmp_path / "out" / "common_media.jsonl").read_text().splitlines()[0])
    assert media["record_id"] == "m1"


def test_pipeline_rejects_orphan_media(tmp_path):
    summary = run_pipeline(_prepare(tmp_path, [_source()], [_resource("missing")]))
    assert summary["valid_media"] == 0 and summary["rejected_media"] == 1


def test_pipeline_rejects_duplicate_record_ids(tmp_path):
    summary = run_pipeline(_prepare(tmp_path, [_source(), _source()], []))
    assert summary["valid_records"] == 0 and summary["rejected_records"] == 2
