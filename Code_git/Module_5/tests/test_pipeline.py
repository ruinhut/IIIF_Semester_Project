"""End-to-end tests for Module 5 research and public-reuse outputs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from iiif_rights_filter.pipeline import run_pipeline

from tests.helpers import module4_record, write_json, write_jsonl


POLICY = {
    "policy_version": "test-v2",
    "category_decisions": {
        "public_domain": "allow",
        "open_license": "allow",
        "noncommercial_or_limited": "exclude",
        "in_copyright": "exclude",
        "no_known_copyright": "exclude",
        "institutional_terms": "exclude",
        "unknown": "exclude",
        "conflicting": "exclude",
    },
}


class PipelineTests(unittest.TestCase):
    def test_pipeline_retains_all_records_and_partitions_public_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module4 = root / "Module_4"
            raw_dir = module4 / "data" / "raw_manifests"
            output4 = module4 / "data" / "output"
            records = []
            documents = {
                "manifest-allow": {
                    "id": "https://example.org/a",
                    "type": "Manifest",
                    "rights": "http://creativecommons.org/licenses/by/4.0/",
                },
                "manifest-excluded": {
                    "id": "https://example.org/b",
                    "type": "Manifest",
                    "rights": "https://rightsstatements.org/vocab/InC/1.0/",
                },
                "manifest-unknown": {
                    "id": "https://example.org/c",
                    "type": "Manifest",
                },
            }
            for manifest_id, document in documents.items():
                relative = f"data/raw_manifests/{manifest_id}.json"
                body = write_json(raw_dir / f"{manifest_id}.json", document)
                records.append(module4_record(manifest_id, relative, body))
            write_jsonl(output4 / "validated_manifests.jsonl", records)
            write_jsonl(
                output4 / "manifest_resource_inventory.jsonl",
                [
                    {
                        "manifest_id": manifest_id,
                        "manifest_url": record["manifest_url"],
                        "provider_names": ["Test Provider"],
                        "canvas_index": 0,
                        "image_service_urls": [
                            f"https://example.org/{manifest_id}/image"
                        ],
                    }
                    for manifest_id, record in zip(documents, records)
                ],
            )
            module5 = root / "Module_5"
            write_json(module5 / "policy.json", POLICY)
            write_json(
                module5 / "config.json",
                {
                    "validated_manifests_jsonl": "../Module_4/data/output/validated_manifests.jsonl",
                    "resource_inventory_jsonl": "../Module_4/data/output/manifest_resource_inventory.jsonl",
                    "module_4_directory": "../Module_4",
                    "policy_file": "policy.json",
                    "output_directory": "data/output",
                    "log_directory": "data/log",
                    "run": {},
                },
            )

            result = run_pipeline(
                module5 / "config.json",
                run_time=datetime(2026, 9, 29, 12, 34, 56, tzinfo=timezone.utc),
            )

            self.assertEqual(3, result.processed_manifest_count)
            self.assertEqual({"allow": 1, "exclude": 2}, result.decision_counts)
            self.assertEqual(3, result.research_resource_count)
            self.assertEqual(1, result.reuse_eligible_resource_count)
            self.assertEqual(3, _line_count(result.research_manifests_jsonl))
            self.assertEqual(1, _line_count(result.reuse_eligible_manifests_jsonl))
            self.assertEqual(2, _line_count(result.research_only_manifests_jsonl))
            self.assertEqual(3, _line_count(result.research_resource_inventory_jsonl))

            research_rows = _read_jsonl(result.research_manifests_jsonl)
            by_id = {row["manifest_id"]: row for row in research_rows}
            for manifest_id in ("manifest-excluded", "manifest-unknown"):
                assessment = by_id[manifest_id]["rights_assessment"]
                self.assertEqual("retained", assessment["research_status"])
                self.assertTrue(assessment["usage_permissions"]["academic_analysis"])
                self.assertFalse(assessment["public_reuse_eligible"])
                self.assertFalse(
                    assessment["usage_permissions"]["public_distribution"]
                )
                self.assertFalse(assessment["usage_permissions"]["commercial_use"])

            resources = _read_jsonl(result.research_resource_inventory_jsonl)
            self.assertEqual(
                {"manifest-allow", "manifest-excluded", "manifest-unknown"},
                {row["manifest_id"] for row in resources},
            )
            self.assertTrue(all(row["academic_analysis_allowed"] for row in resources))
            self.assertIn(
                "Research-retained Manifests: 3",
                result.log_txt.read_text(encoding="utf-8"),
            )

    def test_pipeline_uses_current_raw_manifest_without_checksum_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module4 = root / "Module_4"
            raw_path = module4 / "data" / "raw_manifests" / "manifest-x.json"
            original = write_json(
                raw_path,
                {
                    "type": "Manifest",
                    "rights": "https://creativecommons.org/licenses/by/4.0/",
                },
            )
            record = module4_record(
                "manifest-x", "data/raw_manifests/manifest-x.json", original
            )
            raw_path.write_text('{"type":"Manifest"}', encoding="utf-8")
            output4 = module4 / "data" / "output"
            write_jsonl(output4 / "validated_manifests.jsonl", [record])
            write_jsonl(output4 / "manifest_resource_inventory.jsonl", [])
            module5 = root / "Module_5"
            write_json(module5 / "policy.json", POLICY)
            write_json(
                module5 / "config.json",
                {
                    "validated_manifests_jsonl": "../Module_4/data/output/validated_manifests.jsonl",
                    "resource_inventory_jsonl": "../Module_4/data/output/manifest_resource_inventory.jsonl",
                    "module_4_directory": "../Module_4",
                    "policy_file": "policy.json",
                    "output_directory": "data/output",
                    "log_directory": "data/log",
                },
            )
            result = run_pipeline(module5 / "config.json")
            row = _read_jsonl(result.research_only_manifests_jsonl)[0]
            assessment = row["rights_assessment"]
            self.assertEqual("unknown", assessment["category"])
            self.assertNotIn("raw_manifest_checksum_mismatch", assessment["reason_codes"])
            self.assertEqual("exclude", assessment["decision"])
            self.assertEqual("retained", assessment["research_status"])


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _line_count(path: Path) -> int:
    return len(_read_jsonl(path))


if __name__ == "__main__":
    unittest.main()
