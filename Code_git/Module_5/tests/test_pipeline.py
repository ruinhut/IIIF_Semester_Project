"""End-to-end tests for Module 5 file contracts and filtering."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from iiif_rights_filter.pipeline import run_pipeline

from tests.helpers import module4_record, write_json, write_jsonl


POLICY = {
    "policy_version": "test-v1",
    "category_decisions": {
        "public_domain": "allow",
        "open_license": "allow",
        "noncommercial_or_limited": "review",
        "in_copyright": "deny",
        "no_known_copyright": "review",
        "institutional_terms": "review",
        "unknown": "review",
        "conflicting": "review"
    }
}


class PipelineTests(unittest.TestCase):
    def test_pipeline_partitions_manifests_and_filters_resources(self) -> None:
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
                "manifest-deny": {
                    "id": "https://example.org/b",
                    "type": "Manifest",
                    "rights": "https://rightsstatements.org/vocab/InC/1.0/",
                },
                "manifest-review": {
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
                        "image_service_urls": [f"https://example.org/{manifest_id}/image"],
                    }
                    for manifest_id, record in zip(documents, records)
                ],
            )
            module5 = root / "Module_5"
            write_json(module5 / "policy.json", POLICY)
            config = {
                "validated_manifests_jsonl": "../Module_4/data/output/validated_manifests.jsonl",
                "resource_inventory_jsonl": "../Module_4/data/output/manifest_resource_inventory.jsonl",
                "module_4_directory": "../Module_4",
                "policy_file": "policy.json",
                "output_directory": "data/output",
                "log_directory": "data/log",
                "run": {"verify_raw_sha256": True},
            }
            write_json(module5 / "config.json", config)

            result = run_pipeline(
                module5 / "config.json",
                run_time=datetime(2026, 9, 25, 12, 34, 56, tzinfo=timezone.utc),
            )

            self.assertEqual(3, result.processed_manifest_count)
            self.assertEqual({"allow": 1, "deny": 1, "review": 1}, result.decision_counts)
            self.assertEqual(1, result.allowed_resource_count)
            self.assertEqual(1, _line_count(result.allowed_manifests_jsonl))
            self.assertEqual(1, _line_count(result.denied_manifests_jsonl))
            self.assertEqual(1, _line_count(result.manual_review_jsonl))
            allowed_resource = json.loads(
                result.allowed_resource_inventory_jsonl.read_text(encoding="utf-8")
            )
            self.assertEqual("manifest-allow", allowed_resource["manifest_id"])
            self.assertEqual("allow", allowed_resource["rights_decision"])
            self.assertIn("Policy version: test-v1", result.log_txt.read_text(encoding="utf-8"))

    def test_checksum_mismatch_routes_to_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module4 = root / "Module_4"
            raw_path = module4 / "data" / "raw_manifests" / "manifest-x.json"
            original = write_json(
                raw_path,
                {"type": "Manifest", "rights": "https://creativecommons.org/licenses/by/4.0/"},
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
            row = json.loads(result.manual_review_jsonl.read_text(encoding="utf-8"))
            self.assertIn(
                "raw_manifest_checksum_mismatch",
                row["rights_assessment"]["reason_codes"],
            )
            self.assertEqual("review", row["rights_assessment"]["decision"])
            self.assertEqual(
                "operational_guard.review",
                row["rights_assessment"]["policy_rule"],
            )


def _line_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)


if __name__ == "__main__":
    unittest.main()
