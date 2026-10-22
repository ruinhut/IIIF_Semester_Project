import pytest

from iiif_image_downloader.models import build_download_items


def _record(record_id="m1"):
    return {"record_id": record_id, "object": {"title": "Example"}}


def _profile(record_id="m1"):
    return {"record_id": record_id, "production_method": {"category": "printed"}}


def _media(record_id="m1", resource_id="r1", allowed=True):
    return {
        "record_id": record_id,
        "resource_id": resource_id,
        "sequence": 0,
        "image": {"download_url": "https://example.org/image.jpg"},
        "rights": {"academic_analysis_allowed": allowed},
    }


def test_links_each_media_row_to_record_and_ocr_profile():
    items, skipped = build_download_items(
        [_record()], [_media()], [_profile()],
        require_academic_analysis_allowed=True,
    )
    assert len(items) == 1
    assert not skipped
    assert items[0].record["record_id"] == "m1"
    assert items[0].ocr_profile["record_id"] == "m1"


def test_skips_media_without_academic_analysis_permission():
    items, skipped = build_download_items(
        [_record()], [_media(allowed=False)], [_profile()],
        require_academic_analysis_allowed=True,
    )
    assert not items
    assert skipped[0]["reason"] == "academic_analysis_not_allowed"


def test_rejects_orphan_media_before_network_access():
    with pytest.raises(ValueError, match="missing OCR profile"):
        build_download_items(
            [_record()], [_media()], [],
            require_academic_analysis_allowed=True,
        )


def test_can_require_an_institution_reference_text():
    items, skipped = build_download_items(
        [_record()], [_media()], [_profile()], [],
        require_academic_analysis_allowed=True,
        require_reference_text=True,
    )
    assert not items
    assert skipped[0]["reason"] == "missing_institution_reference_text"
