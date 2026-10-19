import json
from pathlib import Path

import pytest

from iiif_image_downloader.pipeline import run_download
from tests.http_test_server import running_server


def _write_jsonl(path: Path, rows):
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def _record(record_id):
    return {
        "record_id": record_id,
        "object": {"title": f"Title {record_id}"},
        "source": {"manifest_url": f"https://example.org/{record_id}"},
    }


def _profile(record_id):
    return {
        "record_id": record_id,
        "title": f"Title {record_id}",
        "production_method": {"category": "printed"},
    }


def _media(base, *, record_id, resource_id, path, sequence=0):
    return {
        "record_id": record_id,
        "resource_id": resource_id,
        "sequence": sequence,
        "canvas": {"id": f"https://example.org/{resource_id}/canvas"},
        "image": {"download_url": f"{base}{path}"},
        "rights": {
            "academic_analysis_allowed": True,
            "public_reuse_eligible": False,
        },
    }


def _config(tmp_path, records, media, profiles, references=None, require_reference=False):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    _write_jsonl(inputs / "records.jsonl", records)
    _write_jsonl(inputs / "media.jsonl", media)
    _write_jsonl(inputs / "profiles.jsonl", profiles)
    _write_jsonl(inputs / "references.jsonl", references or [])
    value = {
        "common_records_jsonl": str(inputs / "records.jsonl"),
        "common_media_jsonl": str(inputs / "media.jsonl"),
        "ocr_document_profiles_jsonl": str(inputs / "profiles.jsonl"),
        "institution_reference_texts_jsonl": str(inputs / "references.jsonl"),
        "require_reference_text": require_reference,
        "output_directory": str(tmp_path / "output"),
        "log_directory": str(tmp_path / "log"),
        "request_delay_seconds": 0,
        "request": {
            "timeout_seconds": 2,
            "retries": 0,
            "backoff_seconds": 0,
            "request_delay_seconds": 0,
            "max_image_bytes": 1024,
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _image_bundle_directories(mode_root: Path):
    return [
        path.parent
        for path in mode_root.rglob("image.*")
        if path.suffix != ".part"
    ]


def test_example_mode_skips_failure_then_writes_one_portable_bundle(tmp_path):
    with running_server() as base:
        records = [_record("m1")]
        profiles = [_profile("m1")]
        media = [
            _media(base, record_id="m1", resource_id="bad", path="/text"),
            _media(base, record_id="m1", resource_id="good", path="/image.png", sequence=1),
        ]
        summary = run_download(
            _config(tmp_path, records, media, profiles),
            mode="download-example",
        )
    assert summary["downloaded_images"] == 1
    assert summary["failed_images"] == 1
    bundles = _image_bundle_directories(tmp_path / "output" / "example")
    assert len(bundles) == 1
    assert "without_reference" in bundles[0].parts
    assert {path.name for path in bundles[0].iterdir()} == {
        "image.png",
        "common_record.json",
        "common_media.json",
        "ocr_document_profile.json",
    }


def test_all_mode_downloads_every_retrievable_image(tmp_path):
    with running_server() as base:
        records = [_record("m1"), _record("m2")]
        profiles = [_profile("m1"), _profile("m2")]
        media = [
            _media(base, record_id="m1", resource_id="r1", path="/image.png"),
            _media(base, record_id="m2", resource_id="r2", path="/image.jpg"),
            _media(base, record_id="m2", resource_id="r3", path="/missing", sequence=1),
        ]
        config = _config(tmp_path, records, media, profiles)
        first = run_download(config, mode="download-all")
        second = run_download(config, mode="download-all")
    assert first["downloaded_images"] == 2
    assert first["failed_images"] == 1
    assert second["cached_images"] == 2
    assert len(_image_bundle_directories(tmp_path / "output" / "all")) == 2
    index_rows = (
        tmp_path / "output" / "all" / "download_index.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    assert len(index_rows) == 2


def test_stale_image_uses_declared_service_and_cache_keeps_verified_url(tmp_path):
    with running_server() as base:
        media = _media(base, record_id="m1", resource_id="r1", path="/missing")
        media["image"].update(info_json_url=base + "/service/info.json", service_urls=[base + "/service"])
        config = _config(tmp_path, [_record("m1")], [media], [_profile("m1")])
        first = run_download(config, mode="download-all")
        second = run_download(config, mode="download-all")
    assert first["downloaded_images"] == 1 and first["failed_images"] == 0
    assert second["cached_images"] == 1
    bundle = _image_bundle_directories(tmp_path / "output/all")[0]
    linked = json.loads((bundle / "common_media.json").read_text(encoding="utf-8"))
    assert linked["image"]["download_url"] == base + "/service/full/max/0/default.jpg"
    assert linked["image"]["source_id"] == base + "/missing"
    assert linked["image"]["format"] == "image/jpeg"


@pytest.mark.parametrize("mode", ["download-all", "download-example"])
def test_cached_index_paths_remain_relative_to_configured_output_root(tmp_path, mode):
    """A second run must still locate images and JSONs using the same index base."""
    with running_server() as base:
        media = _media(base, record_id="m1", resource_id="r1", path="/image.png")
        config = _config(tmp_path, [_record("m1")], [media], [_profile("m1")])
        first = run_download(config, mode=mode)
        mode_root = Path(first["output_directory"])
        first_entry = json.loads((mode_root / "download_index.jsonl").read_text(encoding="utf-8"))
        second = run_download(config, mode=mode)
        second_entry = json.loads((mode_root / "download_index.jsonl").read_text(encoding="utf-8"))
    assert second["cached_images"] == 1
    assert second_entry["image_path"] == first_entry["image_path"]
    assert second_entry["bundle_directory"] == first_entry["bundle_directory"]
    output_root = tmp_path / "output"
    assert (output_root / second_entry["image_path"]).is_file()
    directory = output_root / second_entry["bundle_directory"]
    for name in ("common_record.json", "common_media.json", "ocr_document_profile.json"):
        assert (directory / name).is_file()


def test_restricted_image_is_not_retried_through_another_service(tmp_path):
    with running_server() as base:
        restricted = _media(base, record_id="m1", resource_id="bad", path="/restricted")
        restricted["image"].update(info_json_url=base + "/service/info.json")
        good = _media(base, record_id="m1", resource_id="good", path="/image.png", sequence=1)
        summary = run_download(_config(tmp_path, [_record("m1")], [restricted, good], [_profile("m1")]), mode="download-all")
    assert summary["downloaded_images"] == 1 and summary["failed_images"] == 1
    failed = json.loads((tmp_path / "output/all/failed_downloads.jsonl").read_text(encoding="utf-8"))
    assert failed["status_code"] == 403


def test_example_mode_downloads_page_image_and_institution_hocr(tmp_path):
    with running_server() as base:
        records = [_record("m1")]
        profiles = [_profile("m1")]
        media = [
            _media(base, record_id="m1", resource_id="r1", path="/image.png")
        ]
        references = [{
            "schema_version": "iiif-ocr-reference-0.1",
            "reference_text_id": "t1",
            "record_id": "m1",
            "resource_id": "r1",
            "sequence": 0,
            "canvas": {"id": "https://example.org/r1/canvas", "label": "1"},
            "reference_text": {
                "id": f"{base}/ocr/1",
                "inline_text": None,
                "format": "text/vnd.hocr+html",
                "type": "Text",
                "label": "OCR",
                "language": "en",
                "profile": None,
                "motivation": [],
                "source_kind": "canvas_seeAlso",
                "alignment_scope": "canvas",
            },
            "status": "institution_provided_ocr_reference",
            "quality_note": "provider supplied",
            "provenance": {"provider_names": ["P"]},
            "rights": {"academic_analysis_allowed": True},
        }]
        summary = run_download(
            _config(
                tmp_path, records, media, profiles, references,
                require_reference=True,
            ),
            mode="download-example",
        )
    assert summary["downloaded_images"] == 1
    assert summary["downloaded_reference_texts"] == 1
    bundle = _image_bundle_directories(tmp_path / "output" / "example")[0]
    assert "with_reference" in bundle.parts
    assert (bundle / "institution_reference_001.hocr.html").is_file()
    assert (bundle / "institution_reference_001.txt").read_text().strip() == "Reference text"
    linked = json.loads(
        (bundle / "institution_reference_texts.json").read_text()
    )
    assert linked["reference_texts"][0]["resource_id"] == "r1"


def test_failed_reference_is_separated_from_reference_training_bundles(tmp_path):
    with running_server() as base:
        records = [_record("m1")]
        profiles = [_profile("m1")]
        media = [
            _media(base, record_id="m1", resource_id="r1", path="/image.png")
        ]
        references = [{
            "reference_text_id": "missing",
            "record_id": "m1",
            "resource_id": "r1",
            "reference_text": {
                "id": f"{base}/missing",
                "format": "text/plain",
            },
        }]
        summary = run_download(
            _config(tmp_path, records, media, profiles, references),
            mode="download-example",
        )
    bundle = _image_bundle_directories(tmp_path / "output" / "example")[0]
    assert "reference_failed" in bundle.parts
    assert summary["downloaded_images"] == 1
    assert summary["downloaded_reference_texts"] == 0
    assert summary["reference_text_failures"] == 1
    assert not (bundle / "institution_reference_texts.json").exists()
