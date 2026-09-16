"""Tests for provider filtering and the persistent data contracts."""

import csv
import json
from pathlib import Path
import tempfile
import unittest

from iiif_provider_census.models import ProviderRecord, SourceProvenance
from iiif_provider_census.selector import SelectionCriteria, select_providers
from iiif_provider_census.store import read_jsonl, write_csv, write_jsonl


def provider(name: str, endpoint: str, status: str = "active") -> ProviderRecord:
    """Build a minimal provider record for selection tests."""

    return ProviderRecord(
        provider_id="",
        name=name,
        institution_url=None,
        discovery_endpoint=endpoint,
        record_status=status,
        source=SourceProvenance("test", "fixture"),
    )


class SelectorAndStoreTests(unittest.TestCase):
    def test_filters_by_name_host_status_and_limit_deterministically(self) -> None:
        """All filters and the final limit must compose predictably."""

        records = [
            provider("Zeta Museum", "https://data.zeta.example/activity"),
            provider("Alpha Library", "https://iiif.alpha.example/activity"),
            provider("Removed Alpha", "https://old.alpha.example/activity", "removed"),
        ]
        criteria = SelectionCriteria(
            include_hosts=("alpha.example",),
            exclude_name_keywords=("removed",),
            limit=1,
        )

        selected = select_providers(records, criteria)
        self.assertEqual([item.name for item in selected], ["Alpha Library"])

    def test_exact_name_matching_is_case_insensitive(self) -> None:
        """CLI-style institution names must match exactly but ignore letter case."""

        records = [
            provider("Alpha Library", "https://alpha.example/activity"),
            provider("Alpha Library Annex", "https://annex.example/activity"),
        ]
        criteria = SelectionCriteria(include_exact_names=("alpha library",))

        selected = select_providers(records, criteria)
        self.assertEqual([item.name for item in selected], ["Alpha Library"])

    def test_jsonl_round_trip_preserves_raw_record_and_csv_is_flat(self) -> None:
        """JSONL keeps provenance while CSV intentionally remains flat."""

        original = ProviderRecord(
            provider_id="provider-test",
            name="München Test",
            institution_url="https://example.org",
            discovery_endpoint="https://example.org/activity",
            rights_values=("https://creativecommons.org/licenses/by/4.0/",),
            rights_status="declared",
            source=SourceProvenance("test", "fixture", observed_at="2026-09-16T12:00:00Z"),
            raw_source_record={"nested": {"kept": True}},
        )
        with tempfile.TemporaryDirectory() as directory:
            jsonl_path = Path(directory) / "providers.jsonl"
            csv_path = Path(directory) / "providers.csv"
            write_jsonl(jsonl_path, [original])
            write_csv(csv_path, [original])

            loaded = read_jsonl(jsonl_path)
            self.assertEqual(loaded[0].raw_source_record, {"nested": {"kept": True}})
            self.assertEqual(loaded[0].name, "München Test")
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["name"], "München Test")
            self.assertNotIn("raw_source_record", row)


if __name__ == "__main__":
    unittest.main()
