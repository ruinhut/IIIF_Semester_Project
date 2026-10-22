import json
from pathlib import Path

from iiif_metadata_normalizer.pipeline import run_pipeline


def _prepare(
    tmp_path: Path,
    decision: str = "exclude",
) -> Path:
    module4 = tmp_path / "module4"
    raw = module4 / "data" / "raw_manifests" / "m1.json"
    raw.parent.mkdir(parents=True)
    document = {
        "@type": "sc:Manifest",
        "@id": "https://example.org/m1",
        "label": {"@value": "Test manuscript", "@language": "en"},
        "metadata": [
            {"label": "Date", "value": "1450"},
            {"label": "Place", "value": "Lausanne"},
            {"label": "Author", "value": "A. Example"},
        ],
        "sequences": [{"canvases": [{
            "@id": "c1",
            "label": "1",
            "seeAlso": {
                "@id": "https://example.org/ocr/1",
                "label": "OCR",
                "format": "text/vnd.hocr+html",
            },
        }]}],
    }
    payload = json.dumps(document).encode()
    raw.write_bytes(payload)
    eligible = decision == "allow"
    handoff = {
        "module_3_schema_version": "2.0",
        "module_4_schema_version": "1.0",
        "module_5_schema_version": "2.0",
        "manifest_id": "m1",
        "manifest_url": "https://example.org/m1",
        "providers": [{"provider_id": "p1", "provider_name": "Provider"}],
        "raw_manifest": {
            "raw_manifest_path": "data/raw_manifests/m1.json",
            "sha256": "legacy-or-stale-value",
        },
        "rights_assessment": {
            "decision": decision,
            "decision_scope": "public_reuse",
            "category": "open_license" if eligible else "unknown",
            "display_label": {"en": "Open license" if eligible else "Unknown rights"},
            "policy_version": "test",
            "evidence": [],
            "research_status": "retained",
            "public_reuse_eligible": eligible,
            "usage_permissions": {
                "retain_url_and_metadata": True,
                "academic_analysis": True,
                "public_distribution": eligible,
                "commercial_use": eligible,
            },
        },
        "structural_validation": {"presentation_version": "2"},
    }
    manifests = tmp_path / "research.jsonl"
    manifests.write_text(json.dumps(handoff) + "\n", encoding="utf-8")
    resource = {
        "manifest_id": "m1", "manifest_url": "https://example.org/m1",
        "canvas_index": 0, "canvas_id": "c1", "canvas_label": "1",
        "body_id": "b1", "body_type": "Image", "body_format": "image/jpeg",
        "image_service_urls": ["https://example.org/iiif/x"],
        "rights_category": handoff["rights_assessment"]["category"],
        "rights_decision": decision,
        "research_status": "retained",
        "academic_analysis_allowed": True,
        "public_reuse_eligible": eligible,
        "public_distribution_allowed": eligible,
        "commercial_use_allowed": eligible,
    }
    resources = tmp_path / "resources.jsonl"
    resources.write_text(json.dumps(resource) + "\n", encoding="utf-8")
    config = {
        "research_manifests_jsonl": str(manifests),
        "research_resource_inventory_jsonl": str(resources),
        "module_4_directory": str(module4),
        "output_directory": str(tmp_path / "out"),
        "log_directory": str(tmp_path / "logs"),
        "language_priority": ["en", "und"],
        "run": {},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def test_pipeline_normalizes_research_only_record_and_resource(tmp_path):
    summary = run_pipeline(_prepare(tmp_path, decision="exclude"))
    assert summary["normalized_records"] == 1
    assert summary["normalized_resources"] == 1
    record = json.loads(
        (tmp_path / "out" / "normalized_records.jsonl").read_text().splitlines()[0]
    )
    assert record["quality"]["status"] == "partial"
    assert record["normalized_metadata"]["dates"][0]["normalization"]["start_year"] == 1450
    assert record["normalized_metadata"]["places"][0]["normalized"] == "Lausanne"
    assert record["normalized_metadata"]["rights"]["decision"] == "exclude"
    resource = json.loads(
        (tmp_path / "out" / "normalized_resources.jsonl").read_text().splitlines()[0]
    )
    assert resource["public_reuse_eligible"] is False
    assert resource["academic_analysis_allowed"] is True
    reference = json.loads(
        (tmp_path / "out" / "normalized_reference_texts.jsonl")
        .read_text().splitlines()[0]
    )
    assert reference["canvas_id"] == "c1"
    assert reference["source_url"] == "https://example.org/ocr/1"
    assert reference["alignment_scope"] == "canvas"
    assert reference["academic_analysis_allowed"] is True


def test_pipeline_ignores_legacy_handoff_checksum(tmp_path):
    summary = run_pipeline(_prepare(tmp_path))
    assert summary["failed_records"] == 0
    assert summary["normalized_records"] == 1
    record = json.loads(
        (tmp_path / "out" / "normalized_records.jsonl")
        .read_text().splitlines()[0]
    )
    assert "raw_manifest_integrity" not in record
