"""Tests for reusable Module 3 discovery skills."""

from iiif_resource_discovery.fetch import HttpFetcher
from iiif_resource_discovery.skills import execute_omeka_s_probe, execute_skill

from http_test_server import LocalHttpServer


def _fetcher() -> HttpFetcher:
    return HttpFetcher(
        timeout_seconds=1,
        retries=0,
        backoff_seconds=0,
        sleeper=lambda _seconds: None,
    )


def test_paginated_identifier_skill_filters_and_validates_manifests():
    with LocalHttpServer() as server:
        result = execute_skill(
            {
                "skill_id": "omeka-style",
                "type": "paginated_json_identifiers_to_manifest_templates",
                "api_url": f"{server.base_url}/api-items",
                "records_path": "$",
                "identifier_path": "o:id",
                "required_nonempty_paths": ["o:media"],
                "filters": [],
                "pagination": {
                    "page_parameter": "page",
                    "page_size_parameter": "per_page",
                    "page_size": 2,
                    "max_pages": 5,
                },
                "max_identifiers": 10,
                "manifest_url_templates": [
                    f"{server.base_url}/templated/{{identifier}}/manifest"
                ],
                "request_delay_seconds": 0,
            },
            _fetcher(),
            investigation_id="test-investigation",
            max_manifests=10,
        )

    assert [item.manifest_url for item in result.manifests] == [
        f"{server.base_url}/templated/11/manifest",
        f"{server.base_url}/templated/13/manifest",
    ]
    assert result.audit["pages_fetched"] == 2
    assert result.audit["records_examined"] == 3
    assert result.audit["identifiers_selected"] == 2
    assert result.audit["manifests_validated"] == 2


def test_same_skill_handles_nested_records_and_provider_filter():
    with LocalHttpServer() as server:
        result = execute_skill(
            {
                "skill_id": "artwork-style",
                "type": "paginated_json_identifiers_to_manifest_templates",
                "api_url": f"{server.base_url}/api-artworks",
                "records_path": "data",
                "identifier_path": "id",
                "required_nonempty_paths": [],
                "filters": [{"path": "is_public_domain", "equals": True}],
                "pagination": {
                    "page_parameter": "page",
                    "page_size_parameter": "limit",
                    "page_size": 10,
                    "max_pages": 1,
                },
                "max_identifiers": 10,
                "manifest_url_templates": [
                    f"{server.base_url}/templated/{{identifier}}/manifest"
                ],
            },
            _fetcher(),
            investigation_id="held-out-test",
            max_manifests=10,
        )

    assert [item.manifest_url for item in result.manifests] == [
        f"{server.base_url}/templated/21/manifest"
    ]
    assert result.audit["status"] == "manifests_found"


def test_omeka_s_probe_reuses_epfl_method_for_new_installation():
    with LocalHttpServer() as server:
        result = execute_omeka_s_probe(
            [f"{server.base_url}/omeka/s/demo/page/home"],
            _fetcher(),
            max_manifests=10,
            request_delay_seconds=0,
        )

    assert result is not None
    assert [item.manifest_url for item in result.manifests] == [
        f"{server.base_url}/omeka/iiif/3/31/manifest"
    ]
    assert result.audit["detected_platform"] == "Omeka S"
    assert result.audit["platform_root"] == f"{server.base_url}/omeka"
    assert result.audit["probe_mode"] == "reusable_epfl_method"
