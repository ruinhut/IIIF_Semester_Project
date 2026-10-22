from pathlib import Path

import pytest

from iiif_image_downloader.fetch import DownloadError, ImageFetcher
from tests.http_test_server import PNG_1X1, running_server


def test_downloads_and_detects_image_bytes(tmp_path: Path):
    with running_server() as base:
        target = tmp_path / "image.part"
        result = ImageFetcher(retries=0).download(f"{base}/image.png", target)
    assert target.read_bytes() == PNG_1X1
    assert result.detected_format == "png"
    assert result.extension == ".png"
    assert len(result.sha256) == 64


def test_accepts_known_image_bytes_with_octet_stream_type(tmp_path: Path):
    with running_server() as base:
        result = ImageFetcher(retries=0).download(
            f"{base}/mislabelled", tmp_path / "image.part"
        )
    assert result.detected_format == "png"


def test_rejects_json_or_html_saved_as_an_image(tmp_path: Path):
    target = tmp_path / "image.part"
    with running_server() as base, pytest.raises(
        DownloadError, match="not a supported raster image"
    ):
        ImageFetcher(retries=0).download(f"{base}/text", target)
    assert not target.exists()


def test_enforces_image_size_limit(tmp_path: Path):
    with running_server() as base, pytest.raises(DownloadError) as caught:
        ImageFetcher(retries=0, max_image_bytes=32).download(
            f"{base}/large", tmp_path / "image.part"
        )
    assert caught.value.error_type == "image_too_large"
