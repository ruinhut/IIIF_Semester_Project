from iiif_common_exporter.models import (
    MEDIA_SCHEMA_VERSION,
    OCR_PROFILE_SCHEMA_VERSION,
    RECORD_SCHEMA_VERSION,
)
from iiif_common_exporter.validator import validate_media, validate_record


def _record(decision="exclude"):
    eligible = decision == "allow"
    return {
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_id": "m1",
        "object": {"identifier": "https://example.org/m1", "dates": []},
        "rights": {
            "category": "open_license" if eligible else "unknown",
            "decision": decision,
            "decision_scope": "public_reuse",
            "research_status": "retained",
            "usage_permissions": {
                "retain_url_and_metadata": True,
                "academic_analysis": True,
                "public_distribution": eligible,
                "commercial_use": eligible,
            },
            "public_reuse_eligible": eligible,
            "policy_version": "p2",
            "statements": [],
        },
        "source": {
            "manifest_id": "m1",
            "manifest_url": "https://example.org/m1",
            "providers": [{"provider_id": "p1"}],
        },
        "media_count": 1,
        "quality": {},
        "provenance": {},
    }


def _media(decision="exclude"):
    eligible = decision == "allow"
    return {
        "schema_version": MEDIA_SCHEMA_VERSION,
        "resource_id": "r1",
        "record_id": "m1",
        "sequence": 0,
        "canvas": {"id": "c1", "label": "1"},
        "image": {
            "id": "i1", "type": "Image",
            "format": "image/jpeg", "service_urls": [],
        },
        "rights": {
            "category": "open_license" if eligible else "unknown",
            "decision": decision,
            "decision_scope": "public_reuse",
            "research_status": "retained",
            "academic_analysis_allowed": True,
            "public_reuse_eligible": eligible,
            "public_distribution_allowed": eligible,
            "commercial_use_allowed": eligible,
            "policy_version": "p2",
        },
        "source_manifest_url": "https://example.org/m1",
    }


def test_research_only_record_has_no_issues():
    assert validate_record(_record("exclude")) == []


def test_reuse_eligible_record_has_no_issues():
    assert validate_record(_record("allow")) == []


def test_record_rejects_inconsistent_public_reuse_flags():
    row = _record("exclude")
    row["rights"]["usage_permissions"]["public_distribution"] = True
    assert any(
        item["path"] == "$.rights.usage_permissions.public_distribution"
        for item in validate_record(row)
    )


def test_record_requires_provider_and_http_manifest_url():
    row = _record()
    row["source"]["providers"] = []
    row["source"]["manifest_url"] = "file.json"
    paths = {item["path"] for item in validate_record(row)}
    assert {"$.source.providers", "$.source.manifest_url"} <= paths


def test_record_checks_date_order():
    row = _record()
    row["object"]["dates"] = [{"start_year": 1500, "end_year": 1400}]
    assert any(item["code"] == "range" for item in validate_record(row))


def test_research_only_media_has_no_issues():
    assert validate_media(_media("exclude")) == []


def test_media_requires_image_reference():
    row = _media()
    row["image"]["id"] = None
    assert any(item["path"] == "$.image" for item in validate_media(row))


def test_media_rejects_negative_sequence():
    row = _media()
    row["sequence"] = -1
    assert any(item["path"] == "$.sequence" for item in validate_media(row))


def test_record_schema_is_valid_json_schema():
    import json
    from pathlib import Path
    from jsonschema import Draft202012Validator
    schema = json.loads(
        (Path(__file__).parents[1] / "schemas" / "record-0.1.schema.json").read_text()
    )
    Draft202012Validator.check_schema(schema)


def test_media_schema_is_valid_json_schema():
    import json
    from pathlib import Path
    from jsonschema import Draft202012Validator
    schema = json.loads(
        (Path(__file__).parents[1] / "schemas" / "media-0.1.schema.json").read_text()
    )
    Draft202012Validator.check_schema(schema)


def test_ocr_profile_schema_is_valid_json_schema():
    import json
    from pathlib import Path
    from jsonschema import Draft202012Validator
    schema = json.loads(
        (Path(__file__).parents[1] / "schemas" / "ocr-profile-0.1.schema.json").read_text()
    )
    Draft202012Validator.check_schema(schema)
    assert schema["properties"]["schema_version"]["const"] == OCR_PROFILE_SCHEMA_VERSION
