"""Tests for converting upstream catalogue repositories into Module 1 input."""

from pathlib import Path
import tempfile
import unittest

from tools.build_catalog_inputs import build_awesome_records, build_guides_records


class CatalogBuilderTests(unittest.TestCase):
    def test_guides_excludes_hidden_and_non_resource_pages(self) -> None:
        """Only visible guide pages with a homepage are provider candidates."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            visible = root / "guides" / "example.org"
            hidden = root / "guides" / "hidden.example"
            internal = root / "guides" / "personas"
            for path in (visible, hidden, internal):
                path.mkdir(parents=True)
            (visible / "index.md").write_text(
                "---\ntitle: Example Library\nhomepage: https://example.org/\n---\n"
                "API documentation: https://example.org/api/docs\n"
                "Manifest template: https://example.org/iiif/{id}/manifest\n",
                encoding="utf-8",
            )
            (hidden / "index.md").write_text(
                "---\ntitle: Hidden\nhomepage: https://hidden.example/\nvisible: no\n---\n",
                encoding="utf-8",
            )
            (internal / "index.md").write_text(
                "---\ntitle: Internal Guide\n---\n",
                encoding="utf-8",
            )

            records = build_guides_records(root)

            self.assertEqual([item["name"] for item in records], ["Example Library"])
            self.assertEqual(records[0]["endpoint_verification"], "pending_module_2")
            self.assertEqual(len(records[0]["endpoints"]), 3)
            self.assertEqual(
                {item["endpoint_role"] for item in records[0]["endpoints"]},
                {"institution_website", "provider_api", "manifest_url_template"},
            )

    def test_awesome_keeps_every_list_entry(self) -> None:
        """Do not silently drop tools or projects from the implementation list."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "implementations.md").write_text(
                "# Implementations\n\n"
                "- [Example Museum](https://museum.example/) publishes manifests.\n"
                "- [Example Tool](https://tool.example/) consumes manifests.\n",
                encoding="utf-8",
            )

            records = build_awesome_records(root)

            self.assertEqual(len(records), 2)
            self.assertEqual(
                {item["name"] for item in records},
                {"Example Museum", "Example Tool"},
            )


if __name__ == "__main__":
    unittest.main()
