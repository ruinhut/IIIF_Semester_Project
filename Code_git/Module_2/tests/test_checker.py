"""Tests for real HTTP behavior against a deterministic local server."""

import unittest

from iiif_entry_validator.checker import EndpointChecker

from http_test_server import FixtureHandler, LocalHttpServer


CHECKED_AT = "2026-09-19T10:00:00+02:00"


class EndpointCheckerTests(unittest.TestCase):
    def _checker(self, **overrides: object) -> EndpointChecker:
        settings = {
            "timeout_seconds": 1,
            "retries": 0,
            "backoff_seconds": 0,
            "max_response_bytes": 1024,
        }
        settings.update(overrides)
        return EndpointChecker(**settings)

    def test_follows_redirect_and_parses_activity_stream_json(self) -> None:
        with LocalHttpServer() as server:
            result = self._checker().check(
                f"{server.base_url}/redirect", checked_at=CHECKED_AT
            )

        self.assertEqual(result.check_result, "reachable_json")
        self.assertTrue(result.json_parseable)
        self.assertEqual(result.json_resource_type, "OrderedCollection")
        self.assertTrue(result.final_url.endswith("/json"))
        self.assertEqual(len(result.redirect_chain), 1)
        self.assertEqual(result.redirect_chain[0].status_code, 302)

    def test_recognizes_json_even_when_server_mislabels_it(self) -> None:
        with LocalHttpServer() as server:
            result = self._checker().check(
                f"{server.base_url}/mislabelled-json", checked_at=CHECKED_AT
            )
        self.assertEqual(result.check_result, "reachable_json")
        self.assertEqual(result.content_type, "text/plain")
        self.assertEqual(result.json_resource_type, "Collection")

    def test_classifies_non_json_invalid_json_and_http_errors(self) -> None:
        expected = {
            "/html": "reachable_non_json",
            "/bad-json": "invalid_json",
            "/restricted": "restricted",
            "/temporary": "temporary_failure",
            "/missing": "unreachable",
        }
        with LocalHttpServer() as server:
            for path, expected_result in expected.items():
                with self.subTest(path=path):
                    result = self._checker().check(
                        f"{server.base_url}{path}", checked_at=CHECKED_AT
                    )
                    self.assertEqual(result.check_result, expected_result)

    def test_bounds_response_size(self) -> None:
        with LocalHttpServer() as server:
            result = self._checker(max_response_bytes=32).check(
                f"{server.base_url}/large", checked_at=CHECKED_AT
            )
        self.assertEqual(result.check_result, "response_too_large")
        self.assertTrue(result.body_truncated)
        self.assertEqual(result.response_bytes, 32)

    def test_retries_temporary_status_only_within_bound(self) -> None:
        with LocalHttpServer() as server:
            result = self._checker(retries=1).check(
                f"{server.base_url}/temporary", checked_at=CHECKED_AT
            )
        self.assertEqual(result.check_result, "temporary_failure")
        self.assertEqual(result.attempt_count, 2)
        self.assertEqual(FixtureHandler.request_counts["/temporary"], 2)


if __name__ == "__main__":
    unittest.main()
