"""Check standards-based Image API URL resolution independently of providers."""

import pytest

from iiif_image_downloader.iiif_service import image_api_candidates


def test_v2_uses_declared_image_server_instead_of_stale_body_host():
    info = {"@context": "http://iiif.io/api/image/2/context.json", "@id": "https://images.example.org/item",
            "width": 500, "height": 900}
    assert image_api_candidates(info, "https://stale.example.org/item/info.json")[0] == "https://images.example.org/item/full/full/0/default.jpg"


def test_manifest_is_not_accepted_as_image_service_information():
    with pytest.raises(ValueError, match="Image API"):
        image_api_candidates({"@context": "http://iiif.io/api/presentation/3/context.json", "type": "Manifest"}, "https://example.org/info.json")
