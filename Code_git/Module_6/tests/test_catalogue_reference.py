"""Prevent translated or ambiguously aligned text from becoming OCR labels."""

from hashlib import sha256
import json

from iiif_metadata_normalizer.catalogue_reference import extract_catalogue_references


def source_and_cache(tmp_path, record):
    source = {"provider_id": "p1", "source_id": "public-json-transcription",
              "manifest_identifier_pattern": r"/manifest/(?P<identifier>\d+)",
              "record_url_template": "https://example.org/catalogue/{identifier}",
              "record_path": "data", "page_records_path": "pages", "page_identifier_path": "image_id",
              "original_text_path": "transcription", "language_path": "original_language"}
    path = tmp_path / (sha256(b"https://example.org/catalogue/12").hexdigest()[:24] + ".json")
    path.write_text(json.dumps({"data": record}), encoding="utf-8")
    return source


def inputs():
    canvas = {"@id": "https://example.org/canvas/1", "label": "1", "images": [{"resource": {
        "@id": "https://example.org/image/ab123/full/full/0/default.jpg"}}]}
    return {"sequences": [{"canvases": [canvas]}]}, {"manifest_id": "m1", "manifest_url": "https://example.org/manifest/12",
        "providers": [{"provider_id": "p1"}], "rights_assessment": {}}, canvas


def test_cached_original_transcription_links_to_verified_single_image(tmp_path):
    record = {"pages": [{"image_id": "ab123"}], "transcription": "Original language text", "translation": "Other text",
              "original_language": "Russian"}
    source = source_and_cache(tmp_path, record)
    document, handoff, _ = inputs()
    audit = []
    rows = extract_catalogue_references(document, handoff, [source], tmp_path, audit)
    assert len(rows) == 1 and rows[0]["inline_text"] == "Original language text"
    assert rows[0]["language"] == "Russian" and rows[0]["canvas_id"].endswith("/canvas/1")
    assert rows[0]["text_role"] == "original_transcription"
    assert audit[0]["status"] == "original_reference_extracted"


def test_translation_alone_is_not_an_ocr_reference(tmp_path):
    source = source_and_cache(tmp_path, {"pages": [{"image_id": "ab123"}], "translation": "English translation"})
    document, handoff, _ = inputs()
    audit = []
    assert not extract_catalogue_references(document, handoff, [source], tmp_path, audit)
    assert audit[0]["status"] == "no_original_language_reference"


def test_markup_without_words_is_not_a_reference(tmp_path):
    source = source_and_cache(tmp_path, {"pages": [{"image_id": "ab123"}], "transcription": "<p><br></p>"})
    document, handoff, _ = inputs()
    audit = []
    assert not extract_catalogue_references(document, handoff, [source], tmp_path, audit)
    assert audit[0]["status"] == "no_original_language_reference"


def test_one_canvas_with_multiple_images_is_not_assumed_unambiguous(tmp_path):
    source = source_and_cache(tmp_path, {"pages": [{"image_id": "ab123"}], "transcription": "Original"})
    document, handoff, canvas = inputs()
    canvas["images"].append({"resource": {"@id": "https://example.org/image/second"}})
    audit = []
    assert not extract_catalogue_references(document, handoff, [source], tmp_path, audit)
    assert audit[0]["status"] == "skipped_ambiguous_canvas_image_alignment"


def test_multiple_pages_are_not_assigned_document_text_arbitrarily(tmp_path):
    source = source_and_cache(tmp_path, {})
    document, handoff, canvas = inputs()
    document["sequences"][0]["canvases"].append(canvas)
    audit = []
    assert not extract_catalogue_references(document, handoff, [source], tmp_path, audit)
    assert audit[0]["status"] == "skipped_ambiguous_multi_page_alignment"


def test_a_matching_label_cannot_substitute_for_a_matching_image(tmp_path):
    source = source_and_cache(tmp_path, {"pages": [{"image_id": "different"}], "transcription": "Text"})
    document, handoff, canvas = inputs()
    canvas["label"] = "different"
    audit = []
    assert not extract_catalogue_references(document, handoff, [source], tmp_path, audit)
    assert audit[0]["status"] == "catalogue_image_does_not_match_canvas"


def test_enrichment_failure_does_not_discard_original_document(tmp_path):
    source = source_and_cache(tmp_path, {})
    cache = next(tmp_path.glob("*.json"))
    cache.write_text("invalid JSON", encoding="utf-8")
    document, handoff, _ = inputs()
    audit = []
    assert not extract_catalogue_references(document, handoff, [source], tmp_path, audit)
    assert audit[0]["status"] == "catalogue_enrichment_failed"
    assert handoff["manifest_id"] == "m1"


def test_snapshot_only_mode_does_not_fetch_missing_item(tmp_path):
    source = source_and_cache(tmp_path, {})
    next(tmp_path.glob("*.json")).unlink()
    source["cache_only"] = True
    document, handoff, _ = inputs()
    audit = []
    assert not extract_catalogue_references(document, handoff, [source], tmp_path, audit)
    assert audit[0]["status"] == "not_in_selected_catalogue_snapshot"
