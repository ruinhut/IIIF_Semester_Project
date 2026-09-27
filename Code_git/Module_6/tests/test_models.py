import pytest

from iiif_metadata_normalizer.models import Module5AllowedRecord, stable_resource_id


def _handoff(decision="allow"):
    return {
        "module_5_schema_version": "1.0",
        "manifest_id": "m1", "manifest_url": "https://example.org/manifest",
        "raw_manifest": {"raw_manifest_path": "raw.json"},
        "rights_assessment": {"decision": decision},
    }


def test_module_5_record_accepts_allowed_manifest():
    assert Module5AllowedRecord.from_mapping(_handoff()).manifest_id == "m1"


def test_module_5_record_rejects_excluded_manifest():
    with pytest.raises(ValueError, match="allow"):
        Module5AllowedRecord.from_mapping(_handoff("exclude"))


def test_resource_id_is_stable_and_content_sensitive():
    row = {"manifest_id": "m1", "canvas_index": 0, "canvas_id": "c1", "body_id": "b1", "image_service_urls": []}
    assert stable_resource_id(row) == stable_resource_id(dict(row))
    assert stable_resource_id(row) != stable_resource_id({**row, "body_id": "b2"})
