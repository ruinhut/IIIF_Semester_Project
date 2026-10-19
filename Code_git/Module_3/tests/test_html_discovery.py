"""Tests for bounded HTML discovery and crawl behavior."""

import unittest

from iiif_resource_discovery.fetch import HttpFetcher
from iiif_resource_discovery.html_discovery import discover_html_candidates

from http_test_server import LocalHttpServer


class HtmlDiscoveryTests(unittest.TestCase):
    def _fetcher(self) -> HttpFetcher:
        return HttpFetcher(timeout_seconds=1, retries=0, backoff_seconds=0)

    def test_finds_declared_manifest_and_crawls_relevant_record_page(self) -> None:
        with LocalHttpServer() as server:
            result = discover_html_candidates(
                f"{server.base_url}/site",
                self._fetcher(),
                max_pages=3,
                max_depth=1,
                max_candidates_per_page=10,
                same_host_only=True,
                delay_seconds=0,
            )

        urls = {candidate.url for candidate in result.candidates}
        self.assertIn(f"{server.base_url}/manifest/1", urls)
        self.assertIn(f"{server.base_url}/collection", urls)
        self.assertEqual(result.pages_visited, 2)

    def test_extracts_typed_json_ld_resource(self) -> None:
        with LocalHttpServer() as server:
            result = discover_html_candidates(
                f"{server.base_url}/jsonld-site",
                self._fetcher(),
                max_pages=1,
                max_depth=0,
                max_candidates_per_page=10,
                same_host_only=True,
                delay_seconds=0,
            )
        self.assertEqual([item.url for item in result.candidates], [f"{server.base_url}/manifest/1"])

    def test_plain_page_produces_no_machine_candidate(self) -> None:
        with LocalHttpServer() as server:
            result = discover_html_candidates(
                f"{server.base_url}/plain",
                self._fetcher(),
                max_pages=1,
                max_depth=0,
                max_candidates_per_page=10,
                same_host_only=True,
                delay_seconds=0,
            )
        self.assertEqual(result.candidates, [])


if __name__ == "__main__":
    unittest.main()
