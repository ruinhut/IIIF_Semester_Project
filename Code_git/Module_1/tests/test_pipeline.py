"""End-to-end tests for the complete Module 1 orchestration path."""

import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from iiif_provider_census.pipeline import run_pipeline
from iiif_provider_census.store import read_jsonl


FIXTURES = Path(__file__).parent / "fixtures"


class PipelineTests(unittest.TestCase):
    def test_local_end_to_end_run_writes_contract_outputs(self) -> None:
        """A local Registry plus a manual source must produce all outputs."""

        # A temporary directory ensures the test never overwrites real census
        # data and verifies that output directories are created automatically.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {
                "registry_sources": [str(FIXTURES / "registry-index.json")],
                "manual_sources": [str(FIXTURES / "manual-providers.json")],
                "selection": {
                    "include_name_keywords": ["library"],
                    "record_statuses": ["active"],
                },
                "network": {"max_registry_pages": 10},
                "output_directory": str(root / "output"),
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            # This call exercises the same orchestration used by the CLI.
            result = run_pipeline(
                config_path,
                institution_selection=["Beta Library"],
                run_time=datetime(2026, 9, 16, 20, 30, 45, tzinfo=timezone.utc),
            )

            self.assertEqual(result.all_provider_count, 3)
            self.assertEqual(result.selected_provider_count, 1)
            self.assertTrue(result.providers_csv.exists())
            self.assertEqual(result.log_txt.name, "Module1_2026-09-16_20-30-45_log.txt")
            self.assertEqual(result.log_txt.parent, root / "data" / "log")
            self.assertTrue(result.log_txt.exists())
            selected = read_jsonl(result.selected_providers_jsonl)
            self.assertEqual(selected[0].name, "Beta Library")
            log_text = result.log_txt.read_text(encoding="utf-8")
            self.assertIn("Institution selection: Beta Library", log_text)
            self.assertIn("Records before deduplication: 3", log_text)

    def test_all_selects_every_active_known_provider(self) -> None:
        """The explicit all keyword selects every active provider after deduplication."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "registry_sources": [str(FIXTURES / "registry-index.json")],
                        "manual_sources": [str(FIXTURES / "manual-providers.json")],
                        "output_directory": str(root / "output"),
                    }
                ),
                encoding="utf-8",
            )

            result = run_pipeline(config_path, institution_selection=["all"])

            self.assertEqual(result.all_provider_count, 3)
            self.assertEqual(result.selected_provider_count, 2)
            self.assertEqual(
                [record.name for record in read_jsonl(result.selected_providers_jsonl)],
                ["Alpha Museum Updated", "Beta Library"],
            )

    def test_unknown_explicit_institution_fails_with_available_names(self) -> None:
        """A typing error must fail rather than silently producing an empty run."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "registry_sources": [],
                        "manual_sources": [str(FIXTURES / "manual-providers.json")],
                        "output_directory": str(root / "output"),
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Available active institutions: Beta Library"):
                run_pipeline(config_path, institution_selection=["Unknown Museum"])


if __name__ == "__main__":
    unittest.main()
