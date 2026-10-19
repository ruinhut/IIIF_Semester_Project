"""Tests for nested IIIF rights evidence extraction."""

from __future__ import annotations

import unittest

from iiif_rights_filter.extractor import extract_rights_evidence


class ExtractorTests(unittest.TestCase):
    def test_extracts_manifest_nested_metadata_and_notices(self) -> None:
        document = {
            "id": "https://example.org/manifest",
            "type": "Manifest",
            "rights": "http://creativecommons.org/publicdomain/mark/1.0/",
            "requiredStatement": {
                "label": {"en": ["Attribution"]},
                "value": {"en": ["Credit Example Library"]},
            },
            "metadata": [
                {
                    "label": {"en": ["License"]},
                    "value": {"en": ["http://creativecommons.org/licenses/by/4.0/"]},
                },
                {"label": {"en": ["Date"]}, "value": {"en": ["1900"]}},
            ],
            "items": [
                {
                    "id": "https://example.org/canvas/1",
                    "type": "Canvas",
                    "rights": "https://rightsstatements.org/vocab/InC/1.0/",
                    "items": [],
                }
            ],
        }
        result = extract_rights_evidence(document)
        self.assertEqual(4, len(result))
        by_type = {item.evidence_type: item for item in result}
        self.assertTrue(by_type["rights"].decisive)
        self.assertTrue(by_type["metadata_rights"].decisive)
        self.assertFalse(by_type["required_statement"].decisive)
        self.assertIn("$.items[0].rights", [item.json_path for item in result])
        self.assertNotIn("1900", [item.raw_value for item in result])

    def test_rights_labelled_required_statement_is_decisive(self) -> None:
        document = {
            "type": "Manifest",
            "requiredStatement": {
                "label": {"en": ["Copyright and usage"]},
                "value": {"en": ["All rights reserved"]},
            },
        }
        result = extract_rights_evidence(document)
        self.assertEqual(1, len(result))
        self.assertTrue(result[0].decisive)
        self.assertEqual("Copyright and usage", result[0].source_label)

    def test_iiif_two_language_markers_are_not_evidence_values(self) -> None:
        document = {
            "@type": "sc:Manifest",
            "attribution": [
                {"@value": "Example Library", "@language": "en"},
                {"@value": "Beispielbibliothek", "@language": "de"},
            ],
        }
        result = extract_rights_evidence(document)
        self.assertEqual(
            ["Example Library", "Beispielbibliothek"],
            [item.raw_value for item in result],
        )


if __name__ == "__main__":
    unittest.main()
