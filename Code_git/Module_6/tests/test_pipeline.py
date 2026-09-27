from hashlib import sha256
import json
from pathlib import Path

from iiif_metadata_normalizer.pipeline import run_pipeline


def _prepare(tmp_path: Path, bad_sha: bool = False) -> Path:
    module4 = tmp_path / "module4"
    raw = module4 / "data" / "raw_manifests" / "m1.json"
    raw.parent.mkdir(parents=True)
    document = {
        "@type": "sc:Manifest", "@id": "https://example.org/m1",
        "label": {"@value": "Test manuscript", "@language": "en"},
        "metadata": [
            {"label": "Date", "value": "1450"},
            {"label": "Place", "value": "Lausanne"},
            {"label": "Author", "value": "A. Example"},
        ],
    }
    payload = json.dumps(document).encode()
    raw.write_bytes(payload)
    handoff = {
        "module_3_schema_version": "2.0", "module_4_schema_version": "1.0", "module_5_schema_version": "1.0",
        "manifest_id": "m1", "manifest_url": "https://example.org/m1",
        "providers": [{"provider_id": "p1", "provider_name": "Provider"}],
        "raw_manifest": {"raw_manifest_path": "data/raw_manifests/m1.json", "sha256": "bad" if bad_sha else sha256(payload).hexdigest()},
        "rights_assessment": {"decision": "allow", "category": "open_license", "display_label": {"en": "Open license"}, "policy_version": "test", "evidence": []},
        "structural_validation": {"presentation_version": "2"},
    }
    manifests = tmp_path / "allowed.jsonl"
    manifests.write_text(json.dumps(handoff) + "\n", encoding="utf-8")
    resource = {"manifest_id": "m1", "manifest_url": "https://example.org/m1", "canvas_index": 0, "canvas_id": "c1", "canvas_label": "1", "body_id": "b1", "body_type": "Image", "body_format": "image/jpeg", "image_service_urls": ["https://example.org/iiif/x"], "rights_category": "open_license", "rights_decision": "allow"}
    resources = tmp_path / "resources.jsonl"
    resources.write_text(json.dumps(resource) + "\n", encoding="utf-8")
    config = {"allowed_manifests_jsonl": str(manifests), "allowed_resource_inventory_jsonl": str(resources), "module_4_directory": str(module4), "output_directory": str(tmp_path / "out"), "log_directory": str(tmp_path / "logs"), "language_priority": ["en", "und"], "run": {"verify_raw_sha256": True}}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def test_pipeline_writes_normalized_record_and_resource(tmp_path):
    summary = run_pipeline(_prepare(tmp_path))
    assert summary["normalized_records"] == 1
    assert summary["normalized_resources"] == 1
    record = json.loads((tmp_path / "out" / "normalized_records.jsonl").read_text().splitlines()[0])
    assert record["quality"]["status"] == "complete"
    assert record["normalized_metadata"]["dates"][0]["normalization"]["start_year"] == 1450
    assert record["normalized_metadata"]["places"][0]["normalized"] == "Lausanne"


def test_pipeline_isolates_checksum_failure(tmp_path):
    summary = run_pipeline(_prepare(tmp_path, bad_sha=True))
    assert summary["failed_records"] == 1
    assert summary["normalized_records"] == 0
