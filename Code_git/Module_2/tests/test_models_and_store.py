"""Tests for Module 1 compatibility and Module 2 persistence."""

import json
from pathlib import Path
import tempfile
import unittest

from iiif_entry_validator.models import CheckedProviderRecord, EndpointCheck, ProviderInputRecord
from iiif_entry_validator.store import read_checked_jsonl, read_provider_jsonl, write_checked_jsonl, write_csv


def provider_value(endpoint: str = "https://example.org/iiif/") -> dict[str, object]:
    return {
        "provider_id": "provider-example",
        "name": "Example Library",
        "institution_url": "https://example.org/",
        "discovery_endpoint": endpoint,
        "discovery_type": "OrderedCollection",
        "rights_status": "unknown",
        "rights_values": [],
        "record_status": "active",
        "source": {"source_type": "iiif_registry", "source_url": "https://registry.iiif.io/"},
        "raw_source_record": {"kept": True},
        "schema_version": "1.0",
    }


class ModelsAndStoreTests(unittest.TestCase):
    def test_reads_module_1_record_without_losing_nested_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "selected_providers.jsonl"
            path.write_text(json.dumps(provider_value()) + "\n", encoding="utf-8")
            record = read_provider_jsonl(path)[0]

        self.assertEqual(record.provider_id, "provider-example")
        self.assertEqual(record.to_dict()["raw_source_record"], {"kept": True})

    def test_checked_jsonl_round_trip_and_csv(self) -> None:
        provider = ProviderInputRecord.from_mapping(provider_value())
        check = EndpointCheck(
            requested_url=provider.discovery_endpoint,
            final_url=provider.discovery_endpoint,
            checked_at="2026-09-19T10:00:00+02:00",
            check_result="reachable_json",
            status_code=200,
            content_type="application/json",
            response_time_ms=12,
            response_bytes=42,
            json_parseable=True,
            json_resource_type="OrderedCollection",
        )
        checked = CheckedProviderRecord(provider, check)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jsonl_path = root / "checked.jsonl"
            csv_path = root / "checked.csv"
            write_checked_jsonl(jsonl_path, [checked])
            write_csv(csv_path, [checked])
            restored = read_checked_jsonl(jsonl_path)[0]
            csv_text = csv_path.read_text(encoding="utf-8-sig")

        self.assertEqual(restored.provider.to_dict(), provider.to_dict())
        self.assertEqual(restored.endpoint_check.json_resource_type, "OrderedCollection")
        self.assertIn("reachable_json", csv_text)

    def test_rejects_invalid_module_1_contract(self) -> None:
        value = provider_value()
        del value["discovery_endpoint"]
        with self.assertRaisesRegex(ValueError, "discovery_endpoint"):
            ProviderInputRecord.from_mapping(value)

    def test_rejects_inconsistent_json_result(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires json_parseable=true"):
            EndpointCheck(
                requested_url="https://example.org/",
                final_url="https://example.org/",
                checked_at="2026-09-19T10:00:00+02:00",
                check_result="reachable_json",
                json_parseable=None,
            )


if __name__ == "__main__":
    unittest.main()
