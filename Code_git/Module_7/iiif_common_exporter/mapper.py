"""Map Module 6 records into the provisional team interchange profile."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .models import Module6Record
from .models import REFERENCE_TEXT_SCHEMA_VERSION


def map_record(
    value: Mapping[str, Any], *, media_count: int, exported_at: str
) -> dict[str, Any]:
    source_record = Module6Record.from_mapping(value).data
    metadata = source_record["normalized_metadata"]
    rights = metadata["rights"]
    source = metadata["source"]
    return {
        "schema_version": "iiif-time-atlas-record-0.1",
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
            "places": [
                {
                    "raw": item["value"],
                    "normalized": item["normalized"],
                    "source_label": item.get("source_label"),
                }
                for item in metadata["places"]
            ],
            "subjects": list(metadata["subjects"]),
            "types": list(metadata["types"]),
            "languages": [
                {"raw": item["value"], "code": item["code"]}
                for item in metadata["languages"]
            ],
        },
        "rights": {
            "category": rights.get("category"),
            "label": dict(rights.get("display_label", {})),
            "decision": rights.get("decision"),
            "decision_scope": rights.get("decision_scope"),
            "research_status": rights.get("research_status"),
            "usage_permissions": dict(rights.get("usage_permissions", {})),
            "public_reuse_eligible": bool(rights.get("public_reuse_eligible", False)),
            "policy_version": rights.get("policy_version"),
            "statements": [
                item for item in rights.get("evidence", []) if item.get("decisive")
            ],
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
            "catalogue_enrichment": list(source_record.get("catalogue_enrichment", [])),
        },
    }


def map_media(value: Mapping[str, Any]) -> dict[str, Any]:
    source_image_id = _optional_text(value.get("body_id"))
    service_urls = [
        text
        for item in value.get("image_service_urls", [])
        if (text := _optional_text(item)) is not None
    ]
    download_url, info_json_url = _resolve_image_urls(
        source_image_id, service_urls, value.get("body_format")
    )
    return {
        "schema_version": "iiif-time-atlas-media-0.1",
        "resource_id": value.get("resource_id"),
        "record_id": value.get("manifest_id"),
        "sequence": value.get("canvas_index"),
        "canvas": {"id": value.get("canvas_id"), "label": value.get("canvas_label")},
        "image": {
            # `id` is the URL that downstream users should open or download.
            # Some providers incorrectly put the Image API service base in the
            # Presentation body ID; keep that raw value separately as source_id.
            "id": download_url,
            "source_id": source_image_id,
            "download_url": download_url,
            "info_json_url": info_json_url,
            "type": value.get("body_type"),
            "format": value.get("body_format"),
            "service_urls": service_urls,
        },
        "rights": {
            "category": value.get("rights_category"),
            "decision": value.get("rights_decision"),
            "decision_scope": value.get("rights_decision_scope"),
            "research_status": value.get("research_status"),
            "academic_analysis_allowed": bool(
                value.get("academic_analysis_allowed", False)
            ),
            "public_reuse_eligible": bool(value.get("public_reuse_eligible", False)),
            "public_distribution_allowed": bool(
                value.get("public_distribution_allowed", False)
            ),
            "commercial_use_allowed": bool(
                value.get("commercial_use_allowed", False)
            ),
            "policy_version": value.get("rights_policy_version"),
        },
        "source_manifest_url": value.get("manifest_url"),
    }


def map_reference_text(
    value: Mapping[str, Any], media: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Map one provider-declared OCR/transcription resource to its page image."""

    providers = [
        str(item.get("provider_name", "")).strip()
        for item in value.get("providers", [])
        if isinstance(item, Mapping) and str(item.get("provider_name", "")).strip()
    ]
    return {
        "schema_version": REFERENCE_TEXT_SCHEMA_VERSION,
        "reference_text_id": value.get("reference_text_id"),
        "record_id": value.get("manifest_id"),
        "resource_id": media.get("resource_id") if media else None,
        "sequence": value.get("canvas_index"),
        "canvas": {
            "id": value.get("canvas_id"),
            "label": value.get("canvas_label"),
        },
        "reference_text": {
            "id": value.get("source_url"),
            "inline_text": value.get("inline_text"),
            "format": value.get("format"),
            "type": value.get("type"),
            "label": value.get("label"),
            "language": value.get("language"),
            "profile": value.get("profile"),
            "motivation": list(value.get("motivation", [])),
            "source_kind": value.get("source_kind"),
            "alignment_scope": value.get("alignment_scope"),
            "text_role": value.get("text_role"),
        },
        "status": "institution_provided_ocr_reference",
        "quality_note": (
            "Provider-supplied OCR or transcription; it is usable as a reference "
            "label but is not asserted to be manually corrected gold truth."
        ),
        "provenance": {
            "provider_names": providers,
            "source_manifest_url": value.get("manifest_url"),
            "catalogue_reference": value.get("catalogue_provenance"),
        },
        "rights": {
            "category": value.get("rights_category"),
            "research_status": value.get("research_status"),
            "academic_analysis_allowed": bool(
                value.get("academic_analysis_allowed", False)
            ),
        },
    }


def _resolve_image_urls(
    source_image_id: str | None,
    service_urls: list[str],
    media_type: Any,
) -> tuple[str | None, str | None]:
    """Return a directly retrievable image URL and optional info.json URL.

    A IIIF Image API service ID identifies the service, not the image bytes.
    When a Manifest uses that base as its body ID, construct a valid full-image
    request while retaining the provider-supplied identifier in `source_id`.
    """

    if not service_urls:
        return source_image_id, None

    service_base = _service_base(service_urls[0])
    info_json_url = f"{service_base}/info.json"
    normalized_source = _service_base(source_image_id) if source_image_id else None
    if source_image_id and normalized_source != service_base:
        return source_image_id, info_json_url

    size = "max" if re.search(r"/iiif/3(?:/|$)", service_base, re.I) else "full"
    image_format = str(media_type or "").lower()
    extension = {
        "image/png": "png",
        "image/tiff": "tif",
        "image/webp": "webp",
        "image/jp2": "jp2",
    }.get(image_format, "jpg")
    return f"{service_base}/full/{size}/0/default.{extension}", info_json_url


def _service_base(value: str) -> str:
    text = value.strip().rstrip("/")
    if text.lower().endswith("/info.json"):
        return text[:-10].rstrip("/")
    return text


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


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
