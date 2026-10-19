"""Tests for Change Discovery, Collection traversal, and curated fallbacks."""

import unittest

from iiif_resource_discovery.discovery import DiscoveryLimits, ResourceDiscoverer
from iiif_resource_discovery.fetch import HttpFetcher
from iiif_resource_discovery.models import ProviderInputRecord

from helpers import provider_value
from http_test_server import LocalHttpServer


class ResourceDiscovererTests(unittest.TestCase):
    def _discoverer(self, **limit_overrides: int) -> ResourceDiscoverer:
        settings = {
            "max_stream_pages_per_provider": 5,
            "max_collections_per_provider": 10,
            "max_html_pages_per_provider": 3,
            "max_html_depth": 1,
            "max_candidates_per_html_page": 10,
            "max_machine_candidates_per_provider": 10,
            "max_manifests_per_provider": 20,
        }
        settings.update(limit_overrides)
        return ResourceDiscoverer(
            HttpFetcher(timeout_seconds=1, retries=0, backoff_seconds=0),
            limits=DiscoveryLimits(**settings),
            html_delay_seconds=0,
        )

    def test_traverses_stream_backwards_and_filters_delete(self) -> None:
        with LocalHttpServer() as server:
            provider = ProviderInputRecord.from_mapping(
                provider_value(f"{server.base_url}/stream", json_type="OrderedCollection")
            )
            result = self._discoverer().discover(provider)

        urls = {finding.manifest_url for finding in result.manifests}
        self.assertEqual(
            urls,
            {
                f"{server.base_url}/manifest/1",
                f"{server.base_url}/manifest/2",
                f"{server.base_url}/manifest/3",
            },
        )
        self.assertNotIn(f"{server.base_url}/manifest/deleted", urls)
        self.assertEqual(result.stream_pages_visited, 2)
        self.assertEqual(result.collections_visited, 2)
        self.assertEqual(result.status, "manifests_found")

    def test_html_page_resolves_manifest_and_collection(self) -> None:
        with LocalHttpServer() as server:
            provider = ProviderInputRecord.from_mapping(
                provider_value(
                    f"{server.base_url}/site",
                    check_result="reachable_non_json",
                    json_type=None,
                )
            )
            result = self._discoverer().discover(provider)

        self.assertEqual(
            {finding.manifest_url for finding in result.manifests},
            {
                f"{server.base_url}/manifest/1",
                f"{server.base_url}/manifest/2",
                f"{server.base_url}/manifest/3",
            },
        )
        self.assertEqual(result.html_pages_visited, 2)

    def test_curated_entry_recovers_provider_without_declared_endpoint(self) -> None:
        with LocalHttpServer() as server:
            provider = ProviderInputRecord.from_mapping(
                provider_value(
                    f"{server.base_url}/plain",
                    check_result="reachable_non_json",
                    json_type=None,
                )
            )
            result = self._discoverer().discover(
                provider, curated_entry_points=[f"{server.base_url}/stream"]
            )

        self.assertEqual(result.status, "manifests_found")
        self.assertEqual(len({item.manifest_url for item in result.manifests}), 3)

    def test_manifest_limit_is_enforced_and_recorded(self) -> None:
        with LocalHttpServer() as server:
            provider = ProviderInputRecord.from_mapping(
                provider_value(f"{server.base_url}/stream", json_type="OrderedCollection")
            )
            result = self._discoverer(max_manifests_per_provider=1).discover(provider)

        self.assertEqual(len({item.manifest_url for item in result.manifests}), 1)
        self.assertTrue(result.truncated)

    def test_malformed_json_is_retained_as_issue(self) -> None:
        with LocalHttpServer() as server:
            provider = ProviderInputRecord.from_mapping(
                provider_value(f"{server.base_url}/bad-json", json_type="Collection")
            )
            result = self._discoverer().discover(provider)

        self.assertEqual(result.status, "unresolved")
        self.assertEqual(result.issues[0].issue_type, "json_decode_error")

    def test_rejects_non_iiif_json_ld_collection(self) -> None:
        with LocalHttpServer() as server:
            provider = ProviderInputRecord.from_mapping(
                provider_value(
                    f"{server.base_url}/non-iiif-collection",
                    json_type="Collection",
                )
            )
            result = self._discoverer().discover(provider)

        self.assertEqual(result.status, "unresolved")
        self.assertEqual(result.resolved_endpoints, [])
        self.assertEqual(result.issues[0].issue_type, "non_iiif_json_resource")


    def test_follows_presentation_collection_next_pagination(self) -> None:
        with LocalHttpServer() as server:
            provider = ProviderInputRecord.from_mapping(
                provider_value(
                    f"{server.base_url}/paged-collection-1",
                    json_type="Collection",
                )
            )
            result = self._discoverer().discover(provider)

        self.assertEqual(
            {item.manifest_url for item in result.manifests},
            {
                f"{server.base_url}/manifest/1",
                f"{server.base_url}/manifest/2",
            },
        )
        self.assertEqual(result.collections_visited, 2)

    def test_generic_provider_api_adapter_follows_explicit_manifest_link(self) -> None:
        with LocalHttpServer() as server:
            provider = ProviderInputRecord.from_mapping(
                provider_value(f"{server.base_url}/provider-api")
            )
            result = self._discoverer().discover(provider)

        self.assertEqual(result.status, "manifests_found")
        self.assertEqual(
            {item.manifest_url for item in result.manifests},
            {f"{server.base_url}/manifest/3"},
        )


if __name__ == "__main__":
    unittest.main()
