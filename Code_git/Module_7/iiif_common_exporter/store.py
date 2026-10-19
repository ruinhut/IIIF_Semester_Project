"""Deterministic writers and checksums for the final export bundle."""

from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number} is not a JSON object")
            rows.append(value)
    return rows


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    content = "".join(
        json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n"
        for row in rows
    )
    _atomic_write(path, content, "utf-8")


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_write(
        path,
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "utf-8",
    )


def write_record_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    fields = [
        "record_id", "identifier", "title", "creators", "date_start",
        "date_end", "date_values", "places", "rights_category",
        "rights_decision", "research_status", "public_reuse_eligible",
        "public_distribution_allowed", "commercial_use_allowed",
        "manifest_url", "provider_names", "media_count", "quality_status",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            obj, source, rights = row["object"], row["source"], row["rights"]
            usage = rights.get("usage_permissions", {})
            starts = [
                item["start_year"] for item in obj["dates"]
                if item["start_year"] is not None
            ]
            ends = [
                item["end_year"] for item in obj["dates"]
                if item["end_year"] is not None
            ]
            writer.writerow({
                "record_id": row["record_id"],
                "identifier": obj["identifier"],
                "title": obj["title"] or "",
                "creators": _join(item["value"] for item in obj["creators"]),
                "date_start": min(starts) if starts else "",
                "date_end": max(ends) if ends else "",
                "date_values": _join(item["raw"] for item in obj["dates"]),
                "places": _join(
                    item["normalized"] or item["raw"] for item in obj["places"]
                ),
                "rights_category": rights.get("category"),
                "rights_decision": rights.get("decision"),
                "research_status": rights.get("research_status"),
                "public_reuse_eligible": rights.get("public_reuse_eligible", False),
                "public_distribution_allowed": usage.get(
                    "public_distribution", False
                ),
                "commercial_use_allowed": usage.get("commercial_use", False),
                "manifest_url": source["manifest_url"],
                "provider_names": _join(
                    item.get("provider_name") for item in source["providers"]
                ),
                "media_count": row["media_count"],
                "quality_status": row["quality"].get("status", ""),
            })
    temp.replace(path)


def write_media_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    fields = [
        "resource_id", "record_id", "sequence", "canvas_id", "canvas_label",
        "image_id", "image_source_id", "image_download_url",
        "image_info_json_url", "image_type", "image_format",
        "image_service_urls",
        "rights_category", "rights_decision", "research_status",
        "academic_analysis_allowed", "public_reuse_eligible",
        "public_distribution_allowed", "commercial_use_allowed",
        "source_manifest_url",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            rights = row["rights"]
            writer.writerow({
                "resource_id": row["resource_id"],
                "record_id": row["record_id"],
                "sequence": row["sequence"],
                "canvas_id": row["canvas"].get("id"),
                "canvas_label": row["canvas"].get("label"),
                "image_id": row["image"].get("id"),
                "image_source_id": row["image"].get("source_id"),
                "image_download_url": row["image"].get("download_url"),
                "image_info_json_url": row["image"].get("info_json_url"),
                "image_type": row["image"].get("type"),
                "image_format": row["image"].get("format"),
                "image_service_urls": _join(row["image"].get("service_urls", [])),
                "rights_category": rights.get("category"),
                "rights_decision": rights.get("decision"),
                "research_status": rights.get("research_status"),
                "academic_analysis_allowed": rights.get(
                    "academic_analysis_allowed", False
                ),
                "public_reuse_eligible": rights.get("public_reuse_eligible", False),
                "public_distribution_allowed": rights.get(
                    "public_distribution_allowed", False
                ),
                "commercial_use_allowed": rights.get(
                    "commercial_use_allowed", False
                ),
                "source_manifest_url": row["source_manifest_url"],
            })
    temp.replace(path)


def write_ocr_profile_csv(
    path: Path, rows: Iterable[Mapping[str, Any]]
) -> None:
    """Write the per-Manifest OCR profile in a compact review format."""

    fields = [
        "record_id", "manifest_url", "provider_names", "title", "languages",
        "date_start", "date_end", "primary_century", "scripts",
        "document_types", "production_method", "production_confidence",
        "production_evidence", "reported_typeface_features", "media_count",
        "scan_quality_status", "academic_analysis_allowed",
        "public_reuse_eligible",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            date = row["date_profile"]
            production = row["production_method"]
            rights = row["rights"]
            writer.writerow({
                "record_id": row["record_id"],
                "manifest_url": row["manifest_url"],
                "provider_names": _join(row.get("provider_names", [])),
                "title": row.get("title") or "",
                "languages": _join(
                    item.get("code") or item.get("raw")
                    for item in row.get("languages", [])
                ),
                "date_start": date.get("start_year") or "",
                "date_end": date.get("end_year") or "",
                "primary_century": date.get("primary_century_label") or "",
                "scripts": _join(
                    item.get("value") for item in row.get("scripts", [])
                ),
                "document_types": _join(
                    item.get("value") for item in row.get("document_types", [])
                ),
                "production_method": production.get("category"),
                "production_confidence": production.get("confidence"),
                "production_evidence": _join(
                    _shorten(item.get("value"), 240)
                    for item in production.get("evidence", [])[:3]
                ),
                "reported_typeface_features": _join(
                    row.get("historical_typography", {}).get(
                        "reported_features", []
                    )
                ),
                "media_count": row.get("media_count", 0),
                "scan_quality_status": row.get("scan_quality", {}).get(
                    "assessment_status", ""
                ),
                "academic_analysis_allowed": rights.get(
                    "academic_analysis_allowed", False
                ),
                "public_reuse_eligible": rights.get(
                    "public_reuse_eligible", False
                ),
            })
    temp.replace(path)


def write_ocr_candidate_csv(
    path: Path, rows: Iterable[Mapping[str, Any]]
) -> None:
    """Write representative OCR page candidates with direct IIIF references."""

    fields = [
        "candidate_id", "record_id", "manifest_url", "provider_names", "title",
        "languages", "date_start", "date_end", "primary_century", "scripts",
        "production_method", "reported_typeface_features", "candidate_status", "sequence",
        "canvas_id", "canvas_label", "image_id", "image_source_id",
        "image_download_url", "image_info_json_url", "image_service_urls",
        "academic_analysis_allowed", "public_reuse_eligible",
        "public_distribution_allowed", "selection_facets",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            date = row["date_profile"]
            rights = row["rights"]
            writer.writerow({
                "candidate_id": row["candidate_id"],
                "record_id": row["record_id"],
                "manifest_url": row["manifest_url"],
                "provider_names": _join(row.get("provider_names", [])),
                "title": row.get("title") or "",
                "languages": _join(
                    item.get("code") or item.get("raw")
                    for item in row.get("languages", [])
                ),
                "date_start": date.get("start_year") or "",
                "date_end": date.get("end_year") or "",
                "primary_century": date.get("primary_century_label") or "",
                "scripts": _join(
                    item.get("value") for item in row.get("scripts", [])
                ),
                "production_method": row.get("production_method", {}).get(
                    "category"
                ),
                "reported_typeface_features": _join(
                    row.get("reported_typeface_features", [])
                ),
                "candidate_status": row.get("candidate_status", ""),
                "sequence": row.get("sequence"),
                "canvas_id": row.get("canvas_id"),
                "canvas_label": row.get("canvas_label"),
                "image_id": row.get("image_id"),
                "image_source_id": row.get("image_source_id"),
                "image_download_url": row.get("image_download_url"),
                "image_info_json_url": row.get("image_info_json_url"),
                "image_service_urls": _join(
                    row.get("image_service_urls", [])
                ),
                "academic_analysis_allowed": rights.get(
                    "academic_analysis_allowed", False
                ),
                "public_reuse_eligible": rights.get(
                    "public_reuse_eligible", False
                ),
                "public_distribution_allowed": rights.get(
                    "public_distribution_allowed", False
                ),
                "selection_facets": _join(row.get("selection_facets", [])),
            })
    temp.replace(path)


def file_descriptor(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "name": path.name,
        "bytes": len(payload),
        "sha256": sha256(payload).hexdigest(),
    }


def _atomic_write(path: Path, content: str, encoding: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding=encoding, newline="\n")
    temp.replace(path)


def _join(values: Iterable[Any]) -> str:
    return " | ".join(str(value) for value in values if value not in (None, ""))


def _shorten(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
