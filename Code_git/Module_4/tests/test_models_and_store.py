from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from iiif_manifest_validator.models import (
    ManifestInputRecord,
    canonicalize_url,
    stable_manifest_id,
)
from iiif_manifest_validator.store import read_manifest_jsonl, write_resource_csv
from tests.helpers import module_3_record


class ModelsAndStoreTests(unittest.TestCase):
    def test_canonical_url_and_id_are_stable(self) -> None:
        first = "HTTPS://EXAMPLE.ORG:443/manifest#fragment"
        second = "https://example.org/manifest"
        self.assertEqual(canonicalize_url(first), second)
        self.assertEqual(stable_manifest_id(first), stable_manifest_id(second))

    def test_input_rejects_mismatched_manifest_id(self) -> None:
        row = module_3_record("https://example.org/manifest")
        row["manifest_id"] = "manifest-wrong"
        with self.assertRaisesRegex(ValueError, "does not match"):
            ManifestInputRecord.from_mapping(row)

    def test_jsonl_reader_deduplicates_identical_records(self) -> None:
        row = module_3_record("https://example.org/manifest")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "input.jsonl"
            path.write_text(
                json.dumps(row) + "\n" + json.dumps(row) + "\n",
                encoding="utf-8",
            )
            records = read_manifest_jsonl(path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].manifest_url, row["manifest_url"])

    def test_resource_csv_flattens_array_fields(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "resources.csv"
            write_resource_csv(
                path,
                [
                    {
                        "manifest_id": "m1",
                        "manifest_url": "https://example.org/m1",
                        "provider_names": ["A", "B"],
                        "presentation_version": "3",
                        "rights_values": ["https://rights.example/open"],
                        "canvas_index": 0,
                        "canvas_id": "https://example.org/c1",
                        "canvas_label": "Page 1",
                        "body_id": "https://example.org/i1.jpg",
                        "body_type": "Image",
                        "body_format": "image/jpeg",
                        "image_service_urls": ["https://example.org/iiif/i1"],
                    }
                ],
            )
            text = path.read_text(encoding="utf-8-sig")
        self.assertIn("A | B", text)
        self.assertIn("https://rights.example/open", text)


if __name__ == "__main__":
    unittest.main()
