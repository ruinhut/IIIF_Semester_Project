"""Check temporal honesty, rights retention, joins and official SDK compatibility."""

from copy import deepcopy
import json
from pathlib import Path
from uuid import UUID

import pytest

from iiif_common_exporter.atlas import DEFAULT_PROFILE, export_atlas


@pytest.fixture
def sample(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    record = {
        "schema_version": "iiif-time-atlas-record-0.1", "record_id": "r1", "media_count": 1,
        "object": {"identifier": "https://museum.example/manifest/1", "title": "Old book", "places": [],
                   "dates": [{"start_year": 1694, "end_year": 1694, "raw": "1694", "approximate": False}]},
        "source": {"manifest_url": "https://museum.example/manifest/1", "providers": []},
        "rights": {"category": "unknown", "decision": "exclude", "decision_scope": "public_reuse", "statements": [],
                   "research_status": "retained", "public_reuse_eligible": False,
                   "usage_permissions": {"academic_analysis": True, "public_distribution": False, "commercial_use": False}},
    }
    media = {"schema_version": "iiif-time-atlas-media-0.1", "record_id": "r1", "resource_id": "image1",
             "sequence": 0, "canvas": {"id": "canvas1"}, "image": {"download_url": "https://museum.example/image.jpg"}}
    reference = {"reference_text_id": "text1", "record_id": "r1", "resource_id": "image1", "canvas": {"id": "canvas1"},
                 "reference_text": {"id": "https://museum.example/page.hocr"}}

    def write(records=None, images=None, refs=None):
        for name, rows in [("common_records.jsonl", records if records is not None else [record]),
                           ("common_media.jsonl", images if images is not None else [media]),
                           ("institution_reference_texts.jsonl", refs if refs is not None else [reference]),
                           ("ocr_document_profiles.jsonl", [{"record_id": "r1", "languages": []}])]:
            (source / name).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    write()
    return source, record, media, reference, write


def load_entity(output, name):
    return json.loads((output / "rde" / f"{name}.json").read_text(encoding="utf-8"))["rde_objects"][0]


def test_preserves_research_rights_image_reference_and_input_files(tmp_path, sample):
    source, record, _, reference, _ = sample
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    output = tmp_path / "atlas"
    result = export_atlas(source, output)
    hr = load_entity(output, "historical_records")
    assert UUID(hr["id"]).version == 5
    assert hr["start_time"] == "1694-01-01T00:00:00Z"
    assert hr["metadata"]["common_record"] == record
    assert hr["metadata"]["rights"]["usage_permissions"]["public_distribution"] is False
    assert hr["metadata"]["institution_reference_texts"] == [reference]
    assert hr["metadata"]["media"][0]["resource_id"] == "image1"
    assert result["historical_records"] == result["staged_records"] == 1
    assert result["observations"] == 0
    assert result["spatial_index_configured"] is False
    assert result["uploaded"] is result["published"] is False
    assert before == {p.name: p.read_bytes() for p in source.iterdir()}
    # Streaming backends need headers before the potentially very large payload.
    line = (output / "rde/collection.jsonl").read_text(encoding="utf-8").splitlines()[0]
    assert line.index('"type_in_file"') < line.index('"rde_objects"')


@pytest.mark.parametrize("dates", [[], [{"start_year": -10, "end_year": 10}],
    [{"start_year": True, "end_year": 1300}], [{"start_year": 0, "end_year": 1300}],
    [{"start_year": 1900, "end_year": 1800}],
    [{"start_year": 1200, "end_year": 1250}, {"start_year": 1500, "end_year": 1600}]])
def test_missing_invalid_or_conflicting_dates_remain_in_staging(tmp_path, sample, dates):
    source, record, _, _, write = sample
    record["object"]["dates"] = dates
    write()
    output = tmp_path / "atlas"
    report = export_atlas(source, output)
    assert report["historical_records"] == 0
    assert report["staged_records"] == report["pending_date_records"] == 1
    assert not (output / "rde/historical_records.json").exists()
    staged = json.loads((output / "staging/records.jsonl").read_text(encoding="utf-8"))
    assert staged["common_record"]["object"]["dates"] == dates
    assert len(staged["media"]) == len(staged["institution_reference_texts"]) == 1


def test_overlapping_dates_preserved_and_ids_stable_across_reruns(tmp_path, sample):
    source, record, _, _, write = sample
    record["object"]["dates"] = [{"start_year": 1275, "end_year": 1325}, {"start_year": 1301, "end_year": 1400}]
    write()
    export_atlas(source, tmp_path / "one")
    export_atlas(source, tmp_path / "two")
    first, second = [load_entity(tmp_path / name, "historical_records") for name in ["one", "two"]]
    assert first["id"] == second["id"]
    assert first["start_time"].startswith("1275-") and first["end_time"].startswith("1325-")
    assert first["metadata"]["temporal_mapping"]["original_dates"] == record["object"]["dates"]


@pytest.mark.parametrize("failure", ["orphan_media", "wrong_canvas", "wrong_reference_record", "duplicate_media", "duplicate_records", "count_mismatch"])
def test_rejects_broken_joins_and_duplicate_ids(tmp_path, sample, failure):
    source, record, media, reference, write = sample
    images, records = [media], [record]
    if failure == "orphan_media": media["record_id"] = "absent"
    if failure == "wrong_canvas": reference["canvas"]["id"] = "different"
    if failure == "wrong_reference_record": reference["record_id"] = "absent"
    if failure == "duplicate_media": images.append(deepcopy(media))
    if failure == "duplicate_records": records.append(deepcopy(record))
    if failure == "count_mismatch": record["media_count"] = 9
    write(records, images)
    with pytest.raises(ValueError):
        export_atlas(source, tmp_path / "atlas")
    assert not (tmp_path / "atlas").exists()


def spatial_profile(tmp_path, coordinates=None):
    points = tmp_path / "points.jsonl"
    points.write_text(json.dumps({"annotation_id": "place1", "record_id": "r1",
        "geometry": {"type": "Point", "coordinates": coordinates or [6.57, 46.52]},
        "relationship": "synthetic_unit_test_location", "source_url": "https://museum.example/evidence",
        "evidence": "Synthetic fixture only; not a real geolocation of the demonstration book."}) + "\n", encoding="utf-8")
    value = json.loads(DEFAULT_PROFILE.read_text(encoding="utf-8"))
    value["spatial_annotations_jsonl"] = "points.jsonl"
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_explicit_spatial_evidence_builds_referentially_closed_collection(tmp_path, sample):
    source = sample[0]
    output = tmp_path / "atlas"
    result = export_atlas(source, output, profile_path=spatial_profile(tmp_path))
    hr = load_entity(output, "historical_records")
    obs = load_entity(output, "observations")
    area = load_entity(output, "areas")
    dataset = load_entity(output, "dataset")
    assert obs["historical_record"] == hr["id"]
    assert hr["has_observations"] == [obs["id"]]
    assert dataset["has_areas"] == [area["id"]]
    assert result["self_contained_collection"] is True
    assert result["observations"] == result["local_areas"] == 1


@pytest.mark.parametrize("point", [[181, 45], [6, 91], [True, 45], ["6", 45], [float("nan"), 45]])
def test_rejects_invalid_spatial_coordinates(tmp_path, sample, point):
    with pytest.raises(ValueError):
        export_atlas(sample[0], tmp_path / "atlas", profile_path=spatial_profile(tmp_path, point))


def test_does_not_overwrite_previous_exports(tmp_path, sample):
    output = tmp_path / "atlas"
    export_atlas(sample[0], output)
    with pytest.raises(ValueError, match="not empty"):
        export_atlas(sample[0], output)


def test_official_sdk_roundtrip_and_strict_spatial_validation(tmp_path, sample):
    pytest.importorskip("timeatlas", reason="Optional SDK check requires Python 3.12 and time-atlas-python 0.3.0")
    from timeatlas import RDECollection
    output = tmp_path / "atlas"
    export_atlas(sample[0], output, profile_path=spatial_profile(tmp_path))
    collection = RDECollection.read_rde_from_files(str(output / "rde"))
    assert len(collection.rdes) == 4
    assert collection.validate_data(mode="strict") is True
    hr = next(r for r in collection.rdes if r.get_type() == "historical_record")
    assert hr.to_dict()["metadata"]["rights"]["public_reuse_eligible"] is False


def test_official_sdk_reports_real_missing_spatial_index(tmp_path, sample):
    pytest.importorskip("timeatlas", reason="Optional SDK check requires Python 3.12")
    from timeatlas import RDECollection
    output = tmp_path / "atlas"
    export_atlas(sample[0], output)
    collection = RDECollection.read_rde_from_files(str(output / "rde"))
    with pytest.warns(UserWarning), pytest.raises(ValueError, match="no observation or Geometry extent"):
        collection.validate_data(mode="strict")
