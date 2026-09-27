from iiif_common_exporter.mapper import map_media, map_record


def _source():
    return {
        "module_6_schema_version": "1.0", "manifest_id": "m1",
        "quality": {"status": "complete"}, "pipeline_versions": {"module_5": "1.0"},
        "normalization": {"normalized_at": "2026-01-01T00:00:00+00:00"},
        "normalized_metadata": {
            "identifier": {"primary": "https://example.org/m1", "values": []},
            "title": {"preferred": "Object", "values": []},
            "description": {"preferred": None, "values": []},
            "creators": [], "dates": [{"value": "1450", "normalization": {"normalized": "1450", "start_year": 1450, "end_year": 1450, "precision": "year", "approximate": False}}],
            "places": [{"value": "Lausanne", "normalized": "Lausanne"}], "subjects": [], "types": [], "languages": [],
            "rights": {"category": "open_license", "decision": "allow", "display_label": {"en": "Open"}, "policy_version": "p1", "evidence": [{"decisive": True, "raw_value": "CC BY"}, {"decisive": False}]},
            "source": {"manifest_id": "m1", "manifest_url": "https://example.org/m1", "declared_manifest_id": "https://example.org/m1", "presentation_version": "3", "providers": [{"provider_id": "p1", "provider_name": "P"}], "discovery_evidence": []},
        },
    }


def test_map_record_preserves_required_project_fields():
    row = map_record(_source(), media_count=2, exported_at="now")
    assert row["object"]["identifier"] == "https://example.org/m1"
    assert row["object"]["dates"][0]["start_year"] == 1450
    assert row["object"]["places"][0]["normalized"] == "Lausanne"
    assert row["rights"]["decision"] == "allow"
    assert row["source"]["providers"][0]["provider_id"] == "p1"
    assert len(row["rights"]["statements"]) == 1


def test_map_media_uses_manifest_as_foreign_key():
    row = map_media({"resource_id": "r1", "manifest_id": "m1", "canvas_index": 0, "canvas_id": "c1", "canvas_label": "1", "body_id": "i1", "body_type": "Image", "body_format": "image/jpeg", "image_service_urls": [], "rights_category": "open_license", "rights_decision": "allow", "rights_policy_version": "p1", "manifest_url": "https://example.org/m1"})
    assert row["record_id"] == "m1"
    assert row["image"]["id"] == "i1"
