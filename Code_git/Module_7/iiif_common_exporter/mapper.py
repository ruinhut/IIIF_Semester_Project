"""Map Module 6 records into the provisional team interchange profile."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from .models import MEDIA_SCHEMA_VERSION, RECORD_SCHEMA_VERSION, Module6Record


def map_record(value: Mapping[str, Any], *, media_count: int, exported_at: str) -> dict[str, Any]:
    source_record = Module6Record.from_mapping(value).data
    metadata = source_record["normalized_metadata"]
    rights = metadata["rights"]
    source = metadata["source"]
    return {
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_id": str(source_record["manifest_id"]),
        "object": {
            "identifier": str(metadata["identifier"]["primary"]),
            "identifiers": list(metadata["identifier"]["values"]),
            "title": metadata["title"]["preferred"],
            "titles": list(metadata["title"]["values"]),
            "description": metadata["description"]["preferred"],
            "descriptions": list(metadata["description"]["values"]),
            "creators": list(metadata["creators"]),
            "dates": [_map_date(item) for item in metadata["dates"]],
            "places": [{"raw": item["value"], "normalized": item["normalized"], "source_label": item.get("source_label")} for item in metadata["places"]],
            "subjects": list(metadata["subjects"]),
            "types": list(metadata["types"]),
            "languages": [{"raw": item["value"], "code": item["code"]} for item in metadata["languages"]],
        },
        "rights": {
            "category": rights.get("category"),
            "label": dict(rights.get("display_label", {})),
            "decision": rights.get("decision"),
            "policy_version": rights.get("policy_version"),
            "statements": [item for item in rights.get("evidence", []) if item.get("decisive")],
        },
        "source": {
            "manifest_id": source.get("manifest_id"),
            "manifest_url": source.get("manifest_url"),
            "declared_manifest_id": source.get("declared_manifest_id"),
            "presentation_version": source.get("presentation_version"),
            "providers": list(source.get("providers", [])),
            "discovery_evidence": list(source.get("discovery_evidence", [])),
        },
        "media_count": media_count,
        "quality": dict(source_record.get("quality", {})),
        "provenance": {
            "pipeline_versions": dict(source_record.get("pipeline_versions", {})),
            "module_6_schema_version": source_record.get("module_6_schema_version"),
            "normalized_at": source_record.get("normalization", {}).get("normalized_at"),
            "exported_at": exported_at,
        },
    }


def map_media(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": MEDIA_SCHEMA_VERSION,
        "resource_id": value.get("resource_id"),
        "record_id": value.get("manifest_id"),
        "sequence": value.get("canvas_index"),
        "canvas": {"id": value.get("canvas_id"), "label": value.get("canvas_label")},
        "image": {
            "id": value.get("body_id"), "type": value.get("body_type"),
            "format": value.get("body_format"),
            "service_urls": list(value.get("image_service_urls", [])),
        },
        "rights": {
            "category": value.get("rights_category"),
            "decision": value.get("rights_decision"),
            "policy_version": value.get("rights_policy_version"),
        },
        "source_manifest_url": value.get("manifest_url"),
    }


def _map_date(value: Mapping[str, Any]) -> dict[str, Any]:
    normalized = value.get("normalization", {})
    return {
        "raw": value.get("value"),
        "normalized": normalized.get("normalized"),
        "start_year": normalized.get("start_year"),
        "end_year": normalized.get("end_year"),
        "precision": normalized.get("precision"),
        "approximate": bool(normalized.get("approximate", False)),
        "source_label": value.get("source_label"),
    }
