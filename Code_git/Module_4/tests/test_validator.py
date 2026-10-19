from __future__ import annotations

import unittest

from iiif_manifest_validator.validator import validate_manifest
from tests.http_test_server import ManifestTestServer


class ValidatorTests(unittest.TestCase):
    def test_legacy_shared_canvas_preserves_source_format_and_inventory(self) -> None:
        with ManifestTestServer() as server:
            value = server.v2_manifest()
        value['@context'] = 'http://www.shared-canvas.org/ns/context.json'
        result = validate_manifest(value)
        self.assertEqual(result.status, 'valid')
        self.assertEqual(result.image_body_count, 1)
        self.assertEqual(result.source_format, 'legacy_shared_canvas')
        self.assertEqual(result.summary_dict()['source_format'], 'legacy_shared_canvas')
        self.assertEqual(value['@context'], 'http://www.shared-canvas.org/ns/context.json')
        self.assertIn('legacy_shared_canvas_context', {issue.code for issue in result.issues})

    def test_canvas_fragment_is_part_of_its_identity(self) -> None:
        """Distinct logical Canvases may share a document URL but use fragments."""
        value = {"@context": "http://iiif.io/api/presentation/2/context.json",
                 "@id": "https://example.org/manifest", "@type": "sc:Manifest",
                 "sequences": [{"canvases": [
                     {"@id": "https://example.org/page#front", "@type": "sc:Canvas",
                      "images": [{"resource": {"@id": "https://example.org/front.jpg", "@type": "dctypes:Image"}}]},
                     {"@id": "https://example.org/page#back", "@type": "sc:Canvas",
                      "images": [{"resource": {"@id": "https://example.org/back.jpg", "@type": "dctypes:Image"}}]}
                 ]}]}
        result = validate_manifest(value)
        self.assertEqual([r.canvas_id for r in result.canvas_resources],
                         ["https://example.org/page#front", "https://example.org/page#back"])

    def test_validates_presentation_3_and_choice_bodies(self) -> None:
        with ManifestTestServer() as server:
            result = validate_manifest(server.v3_manifest())
        self.assertEqual(result.status, "valid")
        self.assertEqual(result.presentation_version, "3")
        self.assertEqual(result.canvas_count, 2)
        self.assertEqual(result.image_body_count, 3)
        self.assertEqual(result.image_service_count, 1)
        self.assertEqual(len(result.canvas_resources), 3)
        self.assertEqual(
            result.rights_values,
            ["http://creativecommons.org/publicdomain/mark/1.0/"],
        )

    def test_validates_presentation_2(self) -> None:
        with ManifestTestServer() as server:
            result = validate_manifest(server.v2_manifest())
        self.assertEqual(result.status, "valid")
        self.assertEqual(result.presentation_version, "2")
        self.assertEqual(result.canvas_count, 1)
        self.assertEqual(result.image_body_count, 1)
        self.assertEqual(result.image_service_count, 1)

    def test_missing_context_requires_manual_review(self) -> None:
        with ManifestTestServer() as server:
            value = server.v3_manifest()
            value.pop("@context")
            result = validate_manifest(value)
        self.assertEqual(result.status, "manual_review")
        self.assertEqual(result.presentation_version, "3")
        self.assertIn("missing_context", {item.code for item in result.issues})

    def test_empty_manifest_requires_manual_review(self) -> None:
        with ManifestTestServer() as server:
            value = server.v3_manifest()
            value["items"] = []
            result = validate_manifest(value)
        self.assertEqual(result.status, "manual_review")
        self.assertIn("no_canvases", {item.code for item in result.issues})
        self.assertIn("no_image_bodies", {item.code for item in result.issues})

    def test_collection_is_rejected(self) -> None:
        value = {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": "https://example.org/collection",
            "type": "Collection",
            "items": [],
        }
        result = validate_manifest(value)
        self.assertEqual(result.status, "invalid")
        self.assertIn("not_manifest", {item.code for item in result.issues})

    def test_non_object_json_is_rejected(self) -> None:
        result = validate_manifest(["not", "a", "manifest"])
        self.assertEqual(result.status, "invalid")
        self.assertEqual(result.issues[0].code, "json_not_object")


if __name__ == "__main__":
    unittest.main()
