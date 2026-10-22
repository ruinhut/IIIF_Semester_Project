import pytest

from iiif_metadata_normalizer.models import Module5ResearchRecord, stable_resource_id


def _handoff(decision="exclude", research_status="retained"):
    return {
        "module_5_schema_version": "2.0",
        "manifest_id": "m1",
        "manifest_url": "https://example.org/manifest",
        "raw_manifest": {"raw_manifest_path": "raw.json"},
        "rights_assessment": {
            "decision": decision,
            "decision_scope": "public_reuse",
            "research_status": research_status,
            "usage_permissions": {
                "retain_url_and_metadata": True,
                "academic_analysis": True,
                "public_distribution": decision == "allow",
                "commercial_use": decision == "allow",
            },
        },
    }


def test_module_5_record_accepts_research_only_manifest():
    record = Module5ResearchRecord.from_mapping(_handoff("exclude"))
    assert record.manifest_id == "m1"


def test_module_5_record_accepts_reuse_eligible_manifest():
    assert Module5ResearchRecord.from_mapping(_handoff("allow")).manifest_id == "m1"


def test_module_5_record_rejects_non_retained_manifest():
    with pytest.raises(ValueError, match="research-retained"):
        Module5ResearchRecord.from_mapping(_handoff("exclude", "discarded"))


def test_resource_id_is_stable_and_content_sensitive():
    row = {
        "manifest_id": "m1", "canvas_index": 0, "canvas_id": "c1",
        "body_id": "b1", "image_service_urls": [],
    }
    assert stable_resource_id(row) == stable_resource_id(dict(row))
    assert stable_resource_id(row) != stable_resource_id({**row, "body_id": "b2"})
