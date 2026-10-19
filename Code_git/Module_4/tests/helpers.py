"""Small test-data builders for Module 4."""

from __future__ import annotations

from iiif_manifest_validator.models import stable_manifest_id


def module_3_record(url: str, provider_name: str = "Example Library") -> dict:
    return {
        "manifest_id": stable_manifest_id(url),
        "manifest_url": url,
        "resource_type": "Manifest",
        "providers": [
            {
                "provider_id": "provider-example",
                "provider_name": provider_name,
            }
        ],
        "discovery_evidence": [
            {
                "provider_id": "provider-example",
                "provider_name": provider_name,
                "discovery_method": "test",
                "source_url": url,
                "activity_type": None,
                "activity_time": None,
            }
        ],
        "module_3_schema_version": "2.0",
    }
