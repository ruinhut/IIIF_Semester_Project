from iiif_common_exporter.mapper import map_media, map_record


def _source():
    return {
        "module_6_schema_version": "1.0",
        "manifest_id": "m1",
        "quality": {"status": "complete"},
        "pipeline_versions": {"module_5": "2.0"},
        "normalization": {"normalized_at": "2026-01-01T00:00:00+00:00"},
        "normalized_metadata": {
            "identifier": {"primary": "https://example.org/m1", "values": []},
            "title": {"preferred": "Object", "values": []},
            "description": {"preferred": None, "values": []},
            "creators": [],
            "dates": [{
                "value": "1450",
                "normalization": {
                    "normalized": "1450", "start_year": 1450,
                    "end_year": 1450, "precision": "year",
                    "approximate": False,
                },
            }],
            "places": [{"value": "Lausanne", "normalized": "Lausanne"}],
            "subjects": [], "types": [], "languages": [],
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
                "display_label": {"en": "Unknown rights"},
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


def test_map_record_preserves_research_only_rights_fields():
    row = map_record(_source(), media_count=2, exported_at="now")
    assert row["object"]["identifier"] == "https://example.org/m1"
    assert row["object"]["dates"][0]["start_year"] == 1450
    assert row["object"]["places"][0]["normalized"] == "Lausanne"
    assert row["rights"]["decision"] == "exclude"
    assert row["rights"]["decision_scope"] == "public_reuse"
    assert row["rights"]["research_status"] == "retained"
    assert row["rights"]["usage_permissions"]["academic_analysis"] is True
    assert row["rights"]["public_reuse_eligible"] is False
    assert row["source"]["providers"][0]["provider_id"] == "p1"


def test_map_media_preserves_research_only_restrictions():
    row = map_media({
        "resource_id": "r1", "manifest_id": "m1", "canvas_index": 0,
        "canvas_id": "c1", "canvas_label": "1", "body_id": "i1",
        "body_type": "Image", "body_format": "image/jpeg",
        "image_service_urls": [], "rights_category": "unknown",
        "rights_decision": "exclude", "rights_decision_scope": "public_reuse",
        "research_status": "retained", "academic_analysis_allowed": True,
        "public_reuse_eligible": False, "public_distribution_allowed": False,
        "commercial_use_allowed": False, "rights_policy_version": "p2",
        "manifest_url": "https://example.org/m1",
    })
    assert row["record_id"] == "m1"
    assert row["image"]["id"] == "i1"
    assert row["rights"]["research_status"] == "retained"
    assert row["rights"]["academic_analysis_allowed"] is True
    assert row["rights"]["public_reuse_eligible"] is False


def test_map_media_turns_iiif_service_base_into_downloadable_image_url():
    service = "https://images.example.org/iiif/2/book-page.tif"
    row = map_media({
        "resource_id": "r1", "manifest_id": "m1", "canvas_index": 0,
        "canvas_id": "https://example.org/c1", "canvas_label": "1",
        "body_id": service, "body_type": "Image", "body_format": "image/jpeg",
        "image_service_urls": [service], "rights_category": "unknown",
        "rights_decision": "exclude", "rights_decision_scope": "public_reuse",
        "research_status": "retained", "academic_analysis_allowed": True,
        "public_reuse_eligible": False, "public_distribution_allowed": False,
        "commercial_use_allowed": False, "rights_policy_version": "p2",
        "manifest_url": "https://example.org/m1",
    })
    assert row["image"]["source_id"] == service
    assert row["image"]["id"] == f"{service}/full/full/0/default.jpg"
    assert row["image"]["download_url"] == row["image"]["id"]
    assert row["image"]["info_json_url"] == f"{service}/info.json"
