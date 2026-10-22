from iiif_common_exporter.ocr_profiler import (
    build_ocr_profile,
    select_ground_truth_candidates,
    summarize_ocr_profiles,
)


def _source_record():
    return {
        "raw_metadata": [
            {
                "label": "Script Type",
                "json_path": "$.metadata[0]",
                "values": [{
                    "value": "Northern Textualis",
                    "json_path": "$.metadata[0].value",
                }],
            },
            {
                "label": "Document Type",
                "json_path": "$.metadata[1]",
                "values": [{
                    "value": "Manuscript fragment",
                    "json_path": "$.metadata[1].value",
                }],
            },
        ]
    }


def _common_record(record_id="m1"):
    return {
        "record_id": record_id,
        "object": {
            "title": "Fragment",
            "languages": [{"raw": "Latin", "code": "la"}],
            "dates": [{
                "raw": "1401-1500",
                "start_year": 1401,
                "end_year": 1500,
            }],
            "types": [{"value": "Parchment", "source_label": "Material"}],
        },
        "rights": {
            "research_status": "retained",
            "usage_permissions": {"academic_analysis": True},
            "public_reuse_eligible": False,
        },
        "source": {
            "manifest_url": f"https://example.org/{record_id}/manifest",
            "providers": [{"provider_name": "Example Library"}],
        },
        "media_count": 5,
    }


def _media(record_id="m1", sequence=0):
    return {
        "resource_id": f"r-{record_id}-{sequence}",
        "record_id": record_id,
        "sequence": sequence,
        "canvas": {"id": f"https://example.org/c{sequence}", "label": str(sequence)},
        "image": {
            "id": f"https://example.org/i{sequence}.jpg",
            "source_id": f"https://example.org/i{sequence}.jpg",
            "download_url": f"https://example.org/i{sequence}.jpg",
            "info_json_url": None,
            "service_urls": [],
        },
        "rights": {
            "academic_analysis_allowed": True,
            "public_reuse_eligible": False,
            "public_distribution_allowed": False,
        },
    }


def test_build_profile_extracts_script_language_date_and_handwriting():
    row = build_ocr_profile(_source_record(), _common_record())
    assert row["languages"] == [{"raw": "Latin", "code": "la"}]
    assert row["date_profile"]["primary_century_label"] == "15th century"
    assert row["scripts"][0]["value"] == "Northern Textualis"
    assert row["production_method"]["category"] == "handwritten"
    assert row["scan_quality"]["flags"]["bleed_through"] == "unknown"
    assert row["metadata_coverage"]["scan_quality_assessed"] is False


def test_summary_reports_counts_and_unknown_scan_quality():
    row = build_ocr_profile(_source_record(), _common_record())
    summary = summarize_ocr_profiles([row])
    assert summary["language_distribution"]["record_counts"] == {"la": 1}
    assert summary["language_distribution"]["media_weighted_counts"] == {"la": 5}
    assert summary["primary_century_distribution"]["record_counts"] == {
        "15th century": 1
    }
    assert summary["production_method_distribution"]["record_counts"] == {
        "handwritten": 1
    }
    assert summary["scan_quality"]["unassessed_records"] == 1


def test_candidate_selection_uses_evenly_spaced_pages():
    profile = build_ocr_profile(_source_record(), _common_record())
    media = [_media(sequence=index) for index in range(5)]
    rows = select_ground_truth_candidates(
        [profile], media, max_records=1, pages_per_record=3
    )
    assert [row["sequence"] for row in rows] == [0, 2, 4]
    assert all(row["manifest_url"].endswith("/m1/manifest") for row in rows)
    assert all(
        row["candidate_status"] == "metadata_supported_ocr_candidate"
        for row in rows
    )
    assert all(row["image_download_url"].endswith(".jpg") for row in rows)


def test_candidate_selection_prioritizes_diverse_records():
    manuscript = build_ocr_profile(_source_record(), _common_record("m1"))
    printed_source = {
        "raw_metadata": [{
            "label": "Format",
            "values": [{"value": "Printed newspaper", "json_path": "$.metadata[0].value"}],
        }]
    }
    printed_common = _common_record("m2")
    printed_common["object"]["languages"] = [{"raw": "German", "code": "de"}]
    printed = build_ocr_profile(printed_source, printed_common)
    rows = select_ground_truth_candidates(
        [manuscript, printed], [_media("m1"), _media("m2")],
        max_records=2, pages_per_record=1,
    )
    assert {row["record_id"] for row in rows} == {"m1", "m2"}
    assert {row["production_method"]["category"] for row in rows} == {
        "handwritten", "printed"
    }


def test_generic_object_identifier_does_not_imply_visual_material():
    source = {
        "raw_metadata": [{
            "label": "Digital Object Identifier",
            "values": [{"value": "book-123", "json_path": "$.metadata[0].value"}],
        }]
    }
    row = build_ocr_profile(source, _common_record())
    assert row["production_method"]["category"] == "unknown"
    assert row["historical_typography"]["reported_features"] == []


def test_description_label_is_not_misread_as_script():
    source = {
        "raw_metadata": [{
            "label": "Catalogue Description",
            "values": [{
                "value": "Full catalogue record in a manuscript catalogue",
                "json_path": "$.metadata[0].value",
            }],
        }]
    }
    row = build_ocr_profile(source, _common_record())
    assert row["scripts"] == []


def test_hand_description_extracts_controlled_script_name():
    source = {
        "raw_metadata": [{
            "label": "Hand",
            "values": [{
                "value": "Written in French textura with later corrections.",
                "json_path": "$.metadata[0].value",
            }],
        }]
    }
    row = build_ocr_profile(source, _common_record())
    assert [item["value"] for item in row["scripts"]] == ["French textura"]


def test_controlled_script_spelling_is_canonicalized():
    source = {
        "raw_metadata": [{
            "label": "Script Type",
            "values": [{
                "value": "Carolingian Minuscule",
                "json_path": "$.metadata[0].value",
            }],
        }]
    }
    row = build_ocr_profile(source, _common_record())
    assert [item["value"] for item in row["scripts"]] == [
        "Carolingian minuscule"
    ]


def test_profile_ignores_record_created_date_and_groups_language_aliases():
    source = _source_record()
    source["normalized_metadata"] = {
        "languages": [
            {"value": "Latin", "code": "la"},
            {"value": "Latein", "code": None},
        ]
    }
    common = _common_record()
    common["object"]["dates"].append({
        "raw": "2026-01-01",
        "start_year": 2026,
        "end_year": 2026,
        "source_label": "Record Created",
    })
    row = build_ocr_profile(source, common)
    assert row["languages"] == [{"raw": "Latin", "code": "la"}]
    assert row["date_profile"]["end_year"] == 1500


def test_reference_to_printed_catalogue_does_not_make_manuscript_mixed():
    source = {
        "raw_metadata": [
            {
                "label": "Description",
                "values": [{
                    "value": "A seventh-century manuscript fragment.",
                    "json_path": "$.metadata[0].value",
                }],
            },
            {
                "label": "Record Origin",
                "values": [{
                    "value": "Description abbreviated from a printed catalogue.",
                    "json_path": "$.metadata[1].value",
                }],
            },
        ]
    }
    row = build_ocr_profile(source, _common_record())
    assert row["production_method"]["category"] == "handwritten"


def test_collection_name_alone_does_not_determine_production_method():
    source = {
        "raw_metadata": [{
            "label": "Collection",
            "values": [{
                "value": "Hebrew Manuscripts and Printed Books",
                "json_path": "$.metadata[0].value",
            }],
        }]
    }
    row = build_ocr_profile(source, _common_record())
    assert row["production_method"]["category"] == "unknown"
