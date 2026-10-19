import json
from pathlib import Path

from iiif_common_exporter.pipeline import run_pipeline


def _write_jsonl(path, rows):
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def _source():
    return {
        "module_6_schema_version": "1.0",
        "manifest_id": "m1",
        "quality": {"status": "partial", "missing_fields": ["date"]},
        "pipeline_versions": {},
        "normalization": {},
        "normalized_metadata": {
            "identifier": {"primary": "https://example.org/m1", "values": []},
            "title": {"preferred": "Object", "values": []},
            "description": {"preferred": None, "values": []},
            "creators": [], "dates": [], "places": [], "subjects": [],
            "types": [], "languages": [],
            "rights": {
                "category": "unknown",
                "decision": "exclude",
                "decision_scope": "public_reuse",
                "research_status": "retained",
                "usage_permissions": {
                    "retain_url_and_metadata": True,
                    "academic_analysis": True,
                    "public_distribution": False,
                    "commercial_use": False,
                },
                "public_reuse_eligible": False,
                "display_label": {},
                "policy_version": "p2",
                "evidence": [],
            },
            "source": {
                "manifest_id": "m1",
                "manifest_url": "https://example.org/m1",
                "declared_manifest_id": "https://example.org/m1",
                "presentation_version": "3",
                "providers": [{"provider_id": "p1", "provider_name": "P"}],
                "discovery_evidence": [],
            },
        },
    }


def _resource(record_id="m1", resource_id="r1"):
    return {
        "resource_id": resource_id,
        "manifest_id": record_id,
        "canvas_index": 0,
        "canvas_id": "c1",
        "canvas_label": "1",
        "body_id": "i1",
        "body_type": "Image",
        "body_format": "image/jpeg",
        "image_service_urls": [],
        "rights_category": "unknown",
        "rights_decision": "exclude",
        "rights_decision_scope": "public_reuse",
        "research_status": "retained",
        "academic_analysis_allowed": True,
        "public_reuse_eligible": False,
        "public_distribution_allowed": False,
        "commercial_use_allowed": False,
        "rights_policy_version": "p2",
        "manifest_url": "https://example.org/m1",
    }


def _prepare(tmp_path: Path, records, resources, reference_texts=None):
    records_path = tmp_path / "records.jsonl"
    resources_path = tmp_path / "resources.jsonl"
    _write_jsonl(records_path, records)
    _write_jsonl(resources_path, resources)
    reference_texts_path = tmp_path / "reference_texts.jsonl"
    _write_jsonl(reference_texts_path, reference_texts or [])
    profile = {
        "profile_version": "provisional-0.1",
        "record_schema_version": "iiif-time-atlas-record-0.1",
        "media_schema_version": "iiif-time-atlas-media-0.1",
        "ocr_profile_schema_version": "iiif-ocr-profile-0.1",
    }
    for name, value in (
        ("profile.json", profile), ("record.json", {}), ("media.json", {}),
        ("ocr.json", {}),
    ):
        (tmp_path / name).write_text(json.dumps(value), encoding="utf-8")
    config = {
        "normalized_records_jsonl": str(records_path),
        "normalized_resources_jsonl": str(resources_path),
        "normalized_reference_texts_jsonl": str(reference_texts_path),
        "profile_json": str(tmp_path / "profile.json"),
        "record_schema_json": str(tmp_path / "record.json"),
        "media_schema_json": str(tmp_path / "media.json"),
        "ocr_profile_schema_json": str(tmp_path / "ocr.json"),
        "output_directory": str(tmp_path / "out"),
        "log_directory": str(tmp_path / "logs"),
        "ocr_profile": {
            "max_ground_truth_records": 2,
            "pages_per_record": 1,
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_pipeline_writes_linked_research_bundle_and_checksums(tmp_path):
    reference = {
        "reference_text_id": "t1",
        "manifest_id": "m1",
        "manifest_url": "https://example.org/m1",
        "canvas_index": 0,
        "canvas_id": "c1",
        "canvas_label": "1",
        "alignment_scope": "canvas",
        "source_kind": "canvas_seeAlso",
        "source_url": "https://example.org/ocr/1",
        "inline_text": None,
        "format": "text/vnd.hocr+html",
        "type": "Text",
        "label": "OCR",
        "language": "de",
        "profile": "https://example.org/hocr",
        "motivation": [],
        "providers": [{"provider_id": "p1", "provider_name": "P"}],
        "rights_category": "unknown",
        "research_status": "retained",
        "academic_analysis_allowed": True,
        "module_6_schema_version": "1.0",
    }
    summary = run_pipeline(
        _prepare(tmp_path, [_source()], [_resource()], [reference])
    )
    assert summary["valid_records"] == 1
    assert summary["valid_media"] == 1
    bundle = json.loads(
        (tmp_path / "out" / "dataset_manifest.json").read_text()
    )
    assert len(bundle["files"]) == 13
    assert all(len(item["sha256"]) == 64 for item in bundle["files"])
    assert bundle["ocr_profile_schema_version"] == "iiif-ocr-profile-0.1"
    assert bundle["counts"]["ocr_profiles"] == 1
    assert bundle["counts"]["ocr_ground_truth_candidates"] == 1
    assert bundle["counts"]["institution_reference_texts"] == 1
    media = json.loads(
        (tmp_path / "out" / "common_media.jsonl").read_text().splitlines()[0]
    )
    assert media["record_id"] == "m1"
    assert media["rights"]["research_status"] == "retained"
    assert media["rights"]["public_reuse_eligible"] is False
    ocr_summary = json.loads(
        (tmp_path / "out" / "ocr_dataset_summary.json").read_text()
    )
    assert ocr_summary["record_count"] == 1
    assert ocr_summary["scan_quality"]["unassessed_records"] == 1
    candidates = (
        tmp_path / "out" / "ocr_ground_truth_candidates.jsonl"
    ).read_text().splitlines()
    assert len(candidates) == 1
    reference_output = json.loads(
        (tmp_path / "out" / "institution_reference_texts.jsonl")
        .read_text().splitlines()[0]
    )
    assert reference_output["resource_id"] == "r1"
    assert reference_output["status"] == "institution_provided_ocr_reference"


def test_pipeline_rejects_orphan_media(tmp_path):
    summary = run_pipeline(
        _prepare(tmp_path, [_source()], [_resource("missing")])
    )
    assert summary["valid_media"] == 0
    assert summary["rejected_media"] == 1


def test_pipeline_rejects_duplicate_record_ids(tmp_path):
    summary = run_pipeline(_prepare(tmp_path, [_source(), _source()], []))
    assert summary["valid_records"] == 0
    assert summary["rejected_records"] == 2
