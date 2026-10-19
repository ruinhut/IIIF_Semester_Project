"""End-to-end tests for Module 3 orchestration and output partitioning."""

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from iiif_resource_discovery.pipeline import run_pipeline

from helpers import provider_value
from http_test_server import LocalHttpServer


def _jsonl_rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class PipelineTests(unittest.TestCase):
    def test_end_to_end_run_deduplicates_manifests_across_providers(self) -> None:
        with LocalHttpServer() as server, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = [
                provider_value(
                    f"{server.base_url}/stream",
                    provider_id="provider-stream",
                    name="Stream Provider",
                    json_type="OrderedCollection",
                ),
                provider_value(
                    f"{server.base_url}/site",
                    provider_id="provider-html",
                    name="HTML Provider",
                    check_result="reachable_non_json",
                ),
                provider_value(
                    f"{server.base_url}/plain",
                    provider_id="provider-plain",
                    name="Plain Provider",
                    check_result="reachable_non_json",
                ),
            ]
            input_path = root / "checked.jsonl"
            input_path.write_text(
                "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
            )
            curated_path = root / "curated.json"
            curated_path.write_text('{"providers":[]}', encoding="utf-8")
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "input_jsonl": str(input_path),
                        "curated_endpoints": str(curated_path),
                        "output_directory": str(root / "output"),
                        "log_directory": str(root / "log"),
                        "network": {"timeout_seconds": 1, "retries": 0, "backoff_seconds": 0},
                        "limits": {
                            "max_stream_pages_per_provider": 5,
                            "max_collections_per_provider": 10,
                            "max_html_pages_per_provider": 3,
                            "max_html_depth": 1,
                            "max_candidates_per_html_page": 10,
                            "max_machine_candidates_per_provider": 10,
                            "max_manifests_per_provider": 20,
                        },
                        "html_discovery": {
                            "enabled": True,
                            "same_host_only": True,
                            "delay_between_pages_seconds": 0,
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = run_pipeline(
                config_path,
                run_time=datetime(2026, 9, 19, 12, 30, 45, tzinfo=timezone.utc),
            )

            manifests = _jsonl_rows(result.manifest_urls_jsonl)
            unresolved = _jsonl_rows(result.unresolved_providers_jsonl)
            provider_reports = _jsonl_rows(result.provider_discovery_jsonl)
            self.assertEqual(result.input_provider_count, 3)
            self.assertEqual(result.processed_provider_count, 3)
            self.assertEqual(result.unique_manifest_count, 3)
            self.assertEqual(result.provider_status_counts["manifests_found"], 2)
            self.assertEqual(result.provider_status_counts["unresolved"], 1)
            self.assertEqual(len(manifests), 3)
            self.assertEqual(len(unresolved), 1)
            self.assertEqual(len(provider_reports), 3)
            manifest_one = next(row for row in manifests if str(row["manifest_url"]).endswith("/manifest/1"))
            self.assertEqual(len(manifest_one["providers"]), 2)
            self.assertTrue(result.provider_summary_csv.exists())
            self.assertEqual(result.log_txt.name, "Module3_2026-09-19_12-30-45_log.txt")
            self.assertIn("Unique Manifest URLs: 3", result.log_txt.read_text(encoding="utf-8"))

    def test_curated_mapping_is_matched_by_provider_name(self) -> None:
        with LocalHttpServer() as server, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "checked.jsonl"
            input_path.write_text(
                json.dumps(
                    provider_value(
                        f"{server.base_url}/plain",
                        name="Curated Library",
                        check_result="reachable_non_json",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            curated_path = root / "curated.json"
            curated_path.write_text(
                json.dumps(
                    {
                        "providers": [
                            {
                                "provider_name": "Curated Library",
                                "entry_points": [f"{server.base_url}/stream"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "input_jsonl": str(input_path),
                        "curated_endpoints": str(curated_path),
                        "output_directory": str(root / "output"),
                        "log_directory": str(root / "log"),
                        "network": {"timeout_seconds": 1, "retries": 0},
                        "limits": {"max_manifests_per_provider": 10},
                        "html_discovery": {"delay_between_pages_seconds": 0},
                    }
                ),
                encoding="utf-8",
            )

            result = run_pipeline(config_path)

        self.assertEqual(result.unique_manifest_count, 3)


    def test_groups_multiple_endpoint_rows_for_one_provider(self) -> None:
        with LocalHttpServer() as server, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = [
                provider_value(
                    f"{server.base_url}/plain",
                    provider_id="provider-multi",
                    name="Multi Route Provider",
                    check_result="reachable_non_json",
                ),
                provider_value(
                    f"{server.base_url}/stream",
                    provider_id="provider-multi",
                    name="Multi Route Provider",
                    json_type="OrderedCollection",
                ),
            ]
            input_path = root / "checked.jsonl"
            input_path.write_text(
                "".join(json.dumps(item) + "\n" for item in records),
                encoding="utf-8",
            )
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "input_jsonl": str(input_path),
                        "output_directory": str(root / "output"),
                        "log_directory": str(root / "log"),
                        "network": {"timeout_seconds": 1, "retries": 0},
                        "limits": {"max_manifests_per_provider": 10},
                        "html_discovery": {"delay_between_pages_seconds": 0},
                    }
                ),
                encoding="utf-8",
            )

            result = run_pipeline(config_path)
            reports = _jsonl_rows(result.provider_discovery_jsonl)

        self.assertEqual(result.input_endpoint_count, 2)
        self.assertEqual(result.input_provider_count, 1)
        self.assertEqual(result.processed_provider_count, 1)
        self.assertEqual(result.unique_manifest_count, 3)
        self.assertEqual(
            reports[0]["resource_discovery"]["input_endpoint_count"], 2
        )

    def test_knowledge_skill_resolves_previously_unresolved_provider(self) -> None:
        with LocalHttpServer() as server, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "checked.jsonl"
            input_path.write_text(
                json.dumps(
                    provider_value(
                        f"{server.base_url}/plain",
                        provider_id="provider-knowledge",
                        name="Knowledge Provider",
                        check_result="reachable_non_json",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            knowledge_path = root / "knowledge.json"
            knowledge_path.write_text(
                json.dumps({
                    "knowledge_base_version": "1.0",
                    "providers": [{
                        "provider_id": "provider-knowledge",
                        "provider_name": "Knowledge Provider",
                        "investigation_id": "investigation-test",
                        "skills": [{
                            "skill_id": "api-identifiers",
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
                        }],
                    }],
                }),
                encoding="utf-8",
            )
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps({
                    "input_jsonl": str(input_path),
                    "knowledge_base": str(knowledge_path),
                    "output_directory": str(root / "output"),
                    "log_directory": str(root / "log"),
                    "network": {"timeout_seconds": 1, "retries": 0},
                    "limits": {
                        "max_html_pages_per_provider": 1,
                        "max_manifests_per_provider": 10,
                    },
                    "html_discovery": {"delay_between_pages_seconds": 0},
                }),
                encoding="utf-8",
            )

            result = run_pipeline(config_path)
            reports = _jsonl_rows(result.provider_discovery_jsonl)

        assert result.unique_manifest_count == 2
        assert result.knowledge_skill_run_count == 1
        assert result.knowledge_resolved_provider_count == 1
        audit = reports[0]["resource_discovery"]["knowledge_application"][0]
        assert audit["status"] == "manifests_found"
        assert audit["manifests_validated"] == 2


if __name__ == "__main__":
    unittest.main()
