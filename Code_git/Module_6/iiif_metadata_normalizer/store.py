"""File I/O helpers for Module 6."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a UTF-8 JSON Lines file and require one object per non-empty line."""

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(value)
    return rows


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def write_metadata_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    """Write a human-readable summary; JSONL remains the lossless output."""

    fieldnames = [
        "manifest_id", "manifest_url", "title", "identifiers", "creators",
        "date_values", "date_start", "date_end", "places", "subjects",
        "types", "languages", "rights_category", "rights_decision",
        "research_status", "public_reuse_eligible", "public_distribution_allowed",
        "commercial_use_allowed", "provider_names", "quality_status",
        "missing_fields",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            metadata = row["normalized_metadata"]
            dates = metadata["dates"]
            rights = metadata["rights"]
            usage = rights.get("usage_permissions", {})
            starts = [
                item["normalization"]["start_year"]
                for item in dates
                if item["normalization"]["start_year"] is not None
            ]
            ends = [
                item["normalization"]["end_year"]
                for item in dates
                if item["normalization"]["end_year"] is not None
            ]
            writer.writerow({
                "manifest_id": row["manifest_id"],
                "manifest_url": row["manifest_url"],
                "title": metadata["title"]["preferred"] or "",
                "identifiers": _join(item["value"] for item in metadata["identifier"]["values"]),
                "creators": _join(item["value"] for item in metadata["creators"]),
                "date_values": _join(item["value"] for item in dates),
                "date_start": min(starts) if starts else "",
                "date_end": max(ends) if ends else "",
                "places": _join(item["normalized"] or item["value"] for item in metadata["places"]),
                "subjects": _join(item["value"] for item in metadata["subjects"]),
                "types": _join(item["value"] for item in metadata["types"]),
                "languages": _join(item["code"] or item["value"] for item in metadata["languages"]),
                "rights_category": rights.get("category", ""),
                "rights_decision": rights.get("decision", ""),
                "research_status": rights.get("research_status", ""),
                "public_reuse_eligible": rights.get("public_reuse_eligible", False),
                "public_distribution_allowed": usage.get("public_distribution", False),
                "commercial_use_allowed": usage.get("commercial_use", False),
                "provider_names": _join(
                    item["provider_name"] for item in metadata["source"]["providers"]
                ),
                "quality_status": row["quality"]["status"],
                "missing_fields": _join(row["quality"]["missing_fields"]),
            })


def write_resource_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    fieldnames = [
        "resource_id", "manifest_id", "manifest_url", "canvas_index",
        "canvas_id", "canvas_label", "body_id", "body_type", "body_format",
        "image_service_urls", "rights_category", "rights_decision",
        "research_status", "academic_analysis_allowed",
        "public_reuse_eligible", "public_distribution_allowed",
        "commercial_use_allowed",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                name: (
                    _join(row.get(name, []))
                    if name == "image_service_urls"
                    else row.get(name, "")
                )
                for name in fieldnames
            })


def _join(values: Iterable[Any]) -> str:
    return " | ".join(str(value) for value in values if value not in (None, ""))
