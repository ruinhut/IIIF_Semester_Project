"""End-to-end tests for the complete Module 1 orchestration path."""

import json
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
            result = run_pipeline(config_path)

            self.assertEqual(result.all_provider_count, 3)
            self.assertEqual(result.selected_provider_count, 1)
            self.assertTrue(result.providers_csv.exists())
            self.assertTrue(result.run_summary_json.exists())
            selected = read_jsonl(result.selected_providers_jsonl)
            self.assertEqual(selected[0].name, "Beta Library")
            summary = json.loads(result.run_summary_json.read_text(encoding="utf-8"))
            self.assertEqual(summary["provider_count_before_deduplication"], 3)


if __name__ == "__main__":
    unittest.main()
