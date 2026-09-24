"""End-to-end tests for the complete Module 2 pipeline."""

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from iiif_entry_validator.pipeline import run_pipeline
from iiif_entry_validator.store import read_checked_jsonl

from http_test_server import LocalHttpServer
from test_models_and_store import provider_value


class PipelineTests(unittest.TestCase):
    def test_local_end_to_end_run_partitions_and_logs_results(self) -> None:
        with LocalHttpServer() as server, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = []
            for index, path in enumerate(("/json", "/html", "/bad-json", "/restricted", "/missing")):
                value = provider_value(f"{server.base_url}{path}")
                value["provider_id"] = f"provider-{index}"
                value["name"] = f"Provider {index}"
                values.append(value)
            input_path = root / "selected_providers.jsonl"
            input_path.write_text(
                "".join(json.dumps(value) + "\n" for value in values), encoding="utf-8"
            )
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "input_jsonl": str(input_path),
                        "output_directory": str(root / "output"),
                        "log_directory": str(root / "log"),
                        "network": {
                            "timeout_seconds": 1,
                            "retries": 0,
                            "backoff_seconds": 0,
                            "max_response_bytes": 1024,
                        },
                        "run": {"delay_between_requests_seconds": 0},
                    }
                ),
                encoding="utf-8",
            )

            result = run_pipeline(
                config_path,
                run_time=datetime(2026, 9, 19, 8, 30, 45, tzinfo=timezone.utc),
            )

            self.assertEqual(result.input_count, 5)
            self.assertEqual(result.checked_count, 5)
            self.assertEqual(result.result_counts["reachable_json"], 1)
            self.assertEqual(result.result_counts["invalid_json"], 1)
            self.assertEqual(result.result_counts["response_too_large"], 0)
            self.assertEqual(len(read_checked_jsonl(result.discovery_ready_jsonl)), 1)
            self.assertEqual(len(read_checked_jsonl(result.manual_review_jsonl)), 3)
            self.assertEqual(len(read_checked_jsonl(result.unavailable_jsonl)), 1)
            self.assertTrue(result.checked_csv.exists())
            self.assertEqual(result.log_txt.name, "Module2_2026-09-19_08-30-45_log.txt")
            log_text = result.log_txt.read_text(encoding="utf-8")
            self.assertIn("Checked records: 5", log_text)
            self.assertIn("reachable_json: 1", log_text)

    def test_limit_creates_an_explicit_bounded_run(self) -> None:
        with LocalHttpServer() as server, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "selected.jsonl"
            input_path.write_text(
                "".join(
                    json.dumps(provider_value(f"{server.base_url}/json?record={index}")) + "\n"
                    for index in range(3)
                ),
                encoding="utf-8",
            )
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "input_jsonl": str(input_path),
                        "output_directory": str(root / "output"),
                        "log_directory": str(root / "log"),
                        "network": {"retries": 0},
                        "run": {"delay_between_requests_seconds": 0},
                    }
                ),
                encoding="utf-8",
            )

            result = run_pipeline(config_path, limit=1)
            log_text = result.log_txt.read_text(encoding="utf-8")

            self.assertEqual(result.input_count, 3)
            self.assertEqual(result.checked_count, 1)
            self.assertIn("Run limit: 1", log_text)


    def test_checks_every_endpoint_of_one_provider(self) -> None:
        with LocalHttpServer() as server, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = provider_value(f"{server.base_url}/json")
            value["endpoints"] = [
                {
                    "url": f"{server.base_url}/json",
                    "endpoint_role": "provider_api",
                    "discovery_type": "ProviderAPI",
                },
                {
                    "url": f"{server.base_url}/html",
                    "endpoint_role": "institution_website",
                    "discovery_type": "InstitutionWebsite",
                },
            ]
            input_path = root / "selected.jsonl"
            input_path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "input_jsonl": str(input_path),
                        "output_directory": str(root / "output"),
                        "log_directory": str(root / "log"),
                        "network": {"retries": 0},
                        "run": {"delay_between_requests_seconds": 0},
                    }
                ),
                encoding="utf-8",
            )

            result = run_pipeline(config_path)
            checked = read_checked_jsonl(result.checked_jsonl)

        self.assertEqual(result.input_count, 1)
        self.assertEqual(result.input_endpoint_count, 2)
        self.assertEqual(result.checked_count, 2)
        self.assertEqual(
            {record.endpoint_candidate.endpoint_role for record in checked},
            {"provider_api", "institution_website"},
        )


if __name__ == "__main__":
    unittest.main()
