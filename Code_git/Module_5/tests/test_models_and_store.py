"""Tests for Module 4 input validation and CSV/JSONL persistence."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from iiif_rights_filter.models import Module4ManifestRecord
from iiif_rights_filter.store import read_validated_manifests

from tests.helpers import module4_record, write_json, write_jsonl


class ModelAndStoreTests(unittest.TestCase):
    def test_rejects_non_valid_module4_record(self) -> None:
        body = b"{}"
        record = module4_record("manifest-x", "raw/x.json", body)
        record["structural_validation"]["status"] = "manual_review"
        with self.assertRaises(ValueError):
            Module4ManifestRecord.from_mapping(record)

    def test_reader_rejects_duplicate_manifest_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.jsonl"
            record = module4_record("manifest-x", "raw/x.json", b"{}")
            write_jsonl(path, [record, record])
            with self.assertRaises(ValueError):
                read_validated_manifests(path)


if __name__ == "__main__":
    unittest.main()
