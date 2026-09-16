"""Tests for Registry traversal, normalization, and manual supplementation."""

from pathlib import Path
import unittest

from iiif_provider_census.fetch import JsonFetcher
from iiif_provider_census.registry import read_manual_records, read_registry


FIXTURES = Path(__file__).parent / "fixtures"


class RegistryReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        """Use local JSON fixtures and a fixed timestamp for reproducibility."""

        self.fetcher = JsonFetcher()
        self.observed_at = "2026-09-16T12:00:00Z"

    def test_follows_pages_and_keeps_latest_activity_per_endpoint(self) -> None:
        """Forward traversal must let a later Update replace an older Add."""

        records = read_registry(
            str(FIXTURES / "registry-index.json"),
            self.fetcher,
            observed_at=self.observed_at,
        )

        self.assertEqual(len(records), 2)
        active = next(record for record in records if record.record_status == "active")
        removed = next(record for record in records if record.record_status == "removed")
        self.assertEqual(active.name, "Alpha Museum Updated")
        self.assertEqual(active.estimated_size, 45)
        self.assertEqual(active.stream_label, "All collections")
        self.assertEqual(active.source.activity_type, "Update")
        self.assertEqual(removed.name, "Removed Provider")

    def test_live_registry_actor_shape_and_declared_rights_are_parsed(self) -> None:
        """Parse the actor layout observed in the current official Registry."""

        page = FIXTURES / "live-registry-page.json"
        records = read_registry(str(page), self.fetcher, observed_at=self.observed_at)
        alpha = next(record for record in records if record.name == "Alpha Museum")

        self.assertEqual(alpha.institution_url, "https://alpha.example/")
        self.assertEqual(alpha.collection_focus, "Museum collections")
        self.assertEqual(alpha.rights_status, "declared")
        self.assertEqual(
            alpha.rights_values,
            ("https://creativecommons.org/publicdomain/zero/1.0/",),
        )

    def test_can_traverse_backwards_when_registry_omits_first_page(self) -> None:
        """The required last/prev links must work when first is absent."""

        records = read_registry(
            str(FIXTURES / "registry-index-last-only.json"),
            self.fetcher,
            observed_at=self.observed_at,
        )
        alpha = next(record for record in records if record.record_status == "active")
        self.assertEqual(alpha.name, "Alpha Museum Updated")
        self.assertEqual(alpha.estimated_size, 45)

    def test_reads_manual_provider_list(self) -> None:
        """Manual providers must be normalized into the same record model."""

        records = read_manual_records(
            str(FIXTURES / "manual-providers.json"),
            self.fetcher,
            observed_at=self.observed_at,
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, "Beta Library")
        self.assertEqual(records[0].source.source_type, "manual")


if __name__ == "__main__":
    unittest.main()
