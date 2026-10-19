"""Verify that recoverable transport IDs do not hide original source defects."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from iiif_manifest_validator.normalization import infer_missing_manifest_id
from iiif_manifest_validator.pipeline import run_pipeline
from iiif_manifest_validator.validator import validate_manifest
from tests.helpers import module_3_record
from tests.http_test_server import ManifestTestServer


def test_pipeline_preserves_raw_bytes_and_records_exact_patch():
    with ManifestTestServer() as server, TemporaryDirectory() as directory:
        root = Path(directory)
        url = server.url("/missing-id")
        (root / "input.jsonl").write_text(json.dumps(module_3_record(url)) + "\n", encoding="utf-8")
        config = {"input_jsonl": "input.jsonl", "raw_manifest_directory": "raw", "output_directory": "out",
                  "log_directory": "log", "network": {"retries": 0},
                  "run": {"delay_between_requests_seconds": 0}}
        path = root / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        result = run_pipeline(path)
        row = json.loads(result.validated_manifests_jsonl.read_text(encoding="utf-8"))
        original = json.loads((root / row["raw_manifest"]["raw_manifest_path"]).read_text(encoding="utf-8"))
        normalized = json.loads((root / row["structural_normalization"]["normalized_manifest_path"]).read_text(encoding="utf-8"))
        assert "@id" not in original and normalized["@id"] == url
        assert row["source_structural_validation"]["status"] == "invalid"
        assert row["structural_validation"]["status"] == "valid"
        assert result.normalized_manifest_count == 1
        config["normalization"] = {"infer_missing_manifest_id": False}
        path.write_text(json.dumps(config), encoding="utf-8")
        strict = run_pipeline(path)
        assert strict.valid_manifest_count == 0 and strict.status_counts == {"invalid": 1}


def test_only_transport_identity_is_repaired_and_strict_validator_is_unchanged():
    document = {"@context": "http://iiif.io/api/presentation/2/context.json", "@type": "sc:Manifest", "sequences": []}
    repaired, patches = infer_missing_manifest_id(document, "https://example.org/manifest?format=json")
    assert "@id" not in document
    assert repaired["@id"] == "https://example.org/manifest?format=json"
    assert patches[0]["evidence"] == "successful_retrieval_final_url"
    assert validate_manifest(document).status == "invalid"
    assert validate_manifest(repaired).status == "manual_review"  # No pages were invented.


def test_declared_malformed_or_valid_identifiers_are_never_overwritten():
    for value in ["https://example.org/original", "invalid identifier", 0]:
        document = {"@context": "http://iiif.io/api/presentation/3/context.json", "type": "Manifest", "id": value}
        repaired, patches = infer_missing_manifest_id(document, "https://example.org/fetched")
        assert repaired == document and not patches
    for document in [{"type": ["Manifest"]}, {"type": "Collection"}, {}, []]:
        assert infer_missing_manifest_id(document, "https://example.org/fetched") == (document, [])
