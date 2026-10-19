from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from iiif_manifest_validator.fetch import FetchError, HttpFetcher
from iiif_manifest_validator.pipeline import run_pipeline
from tests.helpers import module_3_record
from tests.http_test_server import ManifestTestServer


class FetchAndPipelineTests(unittest.TestCase):
    def test_fetch_follows_redirect_and_retains_final_url(self) -> None:
        with ManifestTestServer() as server:
            response = HttpFetcher(retries=0).fetch(server.url("/redirect"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.final_url.endswith("/v3/manifest"))
        self.assertGreater(len(response.body), 0)

    def test_fetch_classifies_restricted_response(self) -> None:
        with ManifestTestServer() as server:
            with self.assertRaises(FetchError) as raised:
                HttpFetcher(retries=0).fetch(server.url("/forbidden"))
        self.assertEqual(raised.exception.error_type, "restricted")
        self.assertEqual(raised.exception.status_code, 403)

    def test_fetch_enforces_response_size(self) -> None:
        with ManifestTestServer() as server:
            with self.assertRaises(FetchError) as raised:
                HttpFetcher(
                    retries=0,
                    max_response_bytes=100,
                ).fetch(server.url("/large"))
        self.assertEqual(raised.exception.error_type, "response_too_large")

    def test_pipeline_classifies_every_outcome(self) -> None:
        with ManifestTestServer() as server, TemporaryDirectory() as directory:
            root = Path(directory)
            urls = [
                server.url("/v3/manifest"),
                server.url("/v2/manifest"),
                server.url("/missing-context"),
                server.url("/empty"),
                server.url("/wrong-type"),
                server.url("/invalid-json"),
                server.url("/forbidden"),
            ]
            input_path = root / "input.jsonl"
            input_path.write_text(
                "".join(json.dumps(module_3_record(url)) + "\n" for url in urls),
                encoding="utf-8",
            )
            config_path = _write_config(root, input_path)
            result = run_pipeline(
                config_path,
                run_time=datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc),
            )

            self.assertEqual(result.processed_manifest_count, 7)
            self.assertEqual(
                result.status_counts,
                {
                    "invalid": 2,
                    "manual_review": 2,
                    "unavailable": 1,
                    "valid": 2,
                },
            )
            self.assertEqual(result.valid_manifest_count, 2)
            self.assertEqual(result.canvas_count, 3)
            self.assertEqual(result.image_body_count, 4)
            resources = _read_jsonl(result.resource_inventory_jsonl)
            self.assertEqual(len(resources), 4)
            self.assertEqual(len(_read_jsonl(result.invalid_manifests_jsonl)), 2)
            self.assertEqual(len(_read_jsonl(result.manual_review_jsonl)), 2)
            self.assertEqual(len(_read_jsonl(result.unavailable_manifests_jsonl)), 1)
            self.assertTrue(result.log_txt.exists())

    def test_second_run_uses_cached_raw_json(self) -> None:
        with ManifestTestServer() as server, TemporaryDirectory() as directory:
            root = Path(directory)
            urls = [server.url("/v3/manifest"), server.url("/v2/manifest")]
            input_path = root / "input.jsonl"
            input_path.write_text(
                "".join(json.dumps(module_3_record(url)) + "\n" for url in urls),
                encoding="utf-8",
            )
            config_path = _write_config(root, input_path)
            first = run_pipeline(config_path)
            request_count = sum(server.requests.values())
            second = run_pipeline(config_path)

            self.assertEqual(first.cache_hit_count, 0)
            self.assertEqual(second.cache_hit_count, 2)
            self.assertEqual(sum(server.requests.values()), request_count)
            self.assertEqual(second.valid_manifest_count, 2)


def _write_config(root: Path, input_path: Path) -> Path:
    config = {
        "input_jsonl": str(input_path),
        "raw_manifest_directory": str(root / "raw"),
        "output_directory": str(root / "output"),
        "log_directory": str(root / "log"),
        "network": {
            "timeout_seconds": 2,
            "retries": 0,
            "backoff_seconds": 0,
            "max_response_bytes": 1024 * 1024,
            "user_agent": "module4-test",
        },
        "run": {
            "max_records": None,
            "delay_between_requests_seconds": 0,
            "force_refresh": False,
        },
    }
    path = root / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


if __name__ == "__main__":
    unittest.main()
