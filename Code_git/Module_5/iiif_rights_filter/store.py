"""Read Module 4 handoffs and write reproducible Module 5 outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import Module4ManifestRecord


SUMMARY_COLUMNS = (
    "manifest_id", "manifest_url", "provider_names", "category", "decision",
    "decision_scope", "research_status", "public_reuse_eligible",
    "retain_url_and_metadata", "academic_analysis", "public_distribution",
    "commercial_use", "rights_label_en", "rights_label_zh", "evidence_count",
    "decisive_evidence_count", "effective_categories", "normalized_rights_values",
    "reason_codes", "policy_version", "assessed_at",
)

RESOURCE_COLUMNS = (
    "manifest_id", "manifest_url", "provider_names", "presentation_version",
    "canvas_index", "canvas_id", "canvas_label", "body_id", "body_type",
    "body_format", "image_service_urls", "rights_category", "rights_decision",
    "rights_decision_scope", "research_status", "retain_url_and_metadata",
    "academic_analysis_allowed", "public_distribution_allowed",
    "commercial_use_allowed", "public_reuse_eligible", "rights_policy_version",
)


def read_validated_manifests(path: Path) -> list[Module4ManifestRecord]:
    """Read Module 4 valid records and reject duplicate Manifest IDs."""

    records: list[Module4ManifestRecord] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                record = Module4ManifestRecord.from_mapping(value)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid Module 4 record at {path}:{line_number}: {exc}"
                ) from exc
            if record.manifest_id in seen:
                raise ValueError(f"Duplicate manifest_id {record.manifest_id!r}")
            seen.add(record.manifest_id)
            records.append(record)
    return records


def read_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file whose non-empty rows must be JSON objects."""

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, Mapping):
                raise ValueError(f"Expected JSON object at {path}:{line_number}")
            records.append(dict(value))
    return records


def write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            json.dump(dict(record), handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            count += 1
    return count


def write_summary_csv(path: Path, records: Iterable[Mapping[str, Any]]) -> int:
    """Write one audit-friendly summary row per assessed Manifest."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        for record in records:
            assessment = record.get("rights_assessment", {})
            evidence = assessment.get("evidence", []) if isinstance(assessment, Mapping) else []
            usage = assessment.get("usage_permissions", {}) if isinstance(assessment, Mapping) else {}
            row = {
                "manifest_id": record.get("manifest_id", ""),
                "manifest_url": record.get("manifest_url", ""),
                "provider_names": " | ".join(_provider_names(record)),
                "category": assessment.get("category", ""),
                "decision": assessment.get("decision", ""),
                "decision_scope": assessment.get("decision_scope", ""),
                "research_status": assessment.get("research_status", ""),
                "public_reuse_eligible": assessment.get("public_reuse_eligible", False),
                "retain_url_and_metadata": usage.get("retain_url_and_metadata", False),
                "academic_analysis": usage.get("academic_analysis", False),
                "public_distribution": usage.get("public_distribution", False),
                "commercial_use": usage.get("commercial_use", False),
                "rights_label_en": (
                    assessment.get("display_label", {}).get("en", "")
                    if isinstance(assessment.get("display_label"), Mapping) else ""
                ),
                "rights_label_zh": (
                    assessment.get("display_label", {}).get("zh", "")
                    if isinstance(assessment.get("display_label"), Mapping) else ""
                ),
                "evidence_count": assessment.get("evidence_count", 0),
                "decisive_evidence_count": assessment.get("decisive_evidence_count", 0),
                "effective_categories": " | ".join(
                    str(item) for item in assessment.get("effective_categories", [])
                ),
                "normalized_rights_values": " | ".join(sorted({
                    str(item.get("normalized_value", ""))
                    for item in evidence
                    if isinstance(item, Mapping)
                    and item.get("decisive")
                    and item.get("normalized_value")
                })),
                "reason_codes": " | ".join(
                    str(item) for item in assessment.get("reason_codes", [])
                ),
                "policy_version": assessment.get("policy_version", ""),
                "assessed_at": assessment.get("assessed_at", ""),
            }
            writer.writerow(row)
            count += 1
    return count


def write_resource_csv(path: Path, records: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESOURCE_COLUMNS)
        writer.writeheader()
        for record in records:
            row = {name: record.get(name, "") for name in RESOURCE_COLUMNS}
            for name in ("provider_names", "image_service_urls"):
                if isinstance(row[name], list):
                    row[name] = " | ".join(str(item) for item in row[name])
            writer.writerow(row)
            count += 1
    return count


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value.rstrip())
        handle.write("\n")


def _provider_names(record: Mapping[str, Any]) -> list[str]:
    return [
        str(item.get("provider_name", ""))
        for item in record.get("providers", [])
        if isinstance(item, Mapping) and item.get("provider_name")
    ]
