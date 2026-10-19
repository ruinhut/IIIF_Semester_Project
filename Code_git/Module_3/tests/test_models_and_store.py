"""Tests for Module 2 compatibility, stable IDs, and evidence merging."""

import json
from pathlib import Path
import tempfile
import unittest

from iiif_resource_discovery.models import (
    DiscoveryEvidence,
    ProviderInputRecord,
    manifest_record,
    stable_manifest_id,
)
from iiif_resource_discovery.store import read_provider_jsonl

from helpers import provider_value


class ModelsAndStoreTests(unittest.TestCase):
    def test_reads_module_2_record_without_losing_fields(self) -> None:
        value = provider_value("https://example.org/stream", json_type="OrderedCollection")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checked.jsonl"
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            record = read_provider_jsonl(path)[0]
        self.assertEqual(record.to_dict(), value)

    def test_stable_manifest_id_uses_canonical_url(self) -> None:
        self.assertEqual(
            stable_manifest_id("HTTPS://EXAMPLE.ORG:443/manifest#fragment"),
            stable_manifest_id("https://example.org/manifest"),
        )

    def test_manifest_record_merges_providers_and_deduplicates_evidence(self) -> None:
        first = DiscoveryEvidence("provider-a", "A", "change_discovery", "https://a.example/stream")
        second = DiscoveryEvidence("provider-b", "B", "curated_entry", "https://b.example/list")
        row = manifest_record("https://example.org/manifest", [first, first, second])
        self.assertEqual(len(row["providers"]), 2)
        self.assertEqual(len(row["discovery_evidence"]), 2)

    def test_rejects_record_without_module_2_check(self) -> None:
        value = provider_value("https://example.org/")
        del value["endpoint_check"]
        with self.assertRaisesRegex(ValueError, "endpoint_check"):
            ProviderInputRecord.from_mapping(value)


if __name__ == "__main__":
    unittest.main()
