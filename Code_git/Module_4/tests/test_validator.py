from __future__ import annotations

import unittest

from iiif_manifest_validator.validator import validate_manifest
from tests.http_test_server import ManifestTestServer


class ValidatorTests(unittest.TestCase):
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
