"""Persist Module 1 provider records as UTF-8 JSONL, CSV, and text."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .models import EndpointCandidate, ProviderRecord


CSV_COLUMNS = (
    "provider_id",
    "name",
    "institution_url",
    "endpoint_count",
    "endpoint_url",
    "endpoint_role",
    "discovery_type",
    "endpoint_label",
    "verification_status",
    "collection_focus",
    "estimated_size",
    "rights_status",
    "rights_values",
    "record_status",
    "last_checked_at",
    "source_type",
    "source_url",
    "source_page_url",
    "observed_at",
)


def write_jsonl(path: Path, records: Iterable[ProviderRecord]) -> int:
    """Write one complete institution object per line."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            json.dump(record.to_dict(), handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            count += 1
    return count


def read_jsonl(path: Path) -> list[ProviderRecord]:
    """Read both legacy schema 1 records and schema 2 endpoint arrays."""

    records: list[ProviderRecord] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                records.append(ProviderRecord.from_mapping(value))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid record at {path}:{line_number}: {exc}") from exc
    return records


def write_csv(path: Path, records: Iterable[ProviderRecord]) -> int:
    """Write one review row per endpoint while repeating provider identity."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            for endpoint in record.endpoints:
                writer.writerow(_csv_row(record, endpoint))
                count += 1
    return count


def write_text(path: Path, value: str) -> None:
    """Write a UTF-8 human-readable run log with normalized newlines."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value.rstrip())
        handle.write("\n")


def _csv_row(
    record: ProviderRecord, endpoint: EndpointCandidate
) -> dict[str, Any]:
    """Flatten one endpoint and its provider-level context."""

    return {
        "provider_id": record.provider_id,
        "name": record.name,
        "institution_url": record.institution_url or "",
        "endpoint_count": record.endpoint_count,
        "endpoint_url": endpoint.url,
        "endpoint_role": endpoint.endpoint_role,
        "discovery_type": endpoint.discovery_type,
        "endpoint_label": endpoint.label or "",
        "verification_status": endpoint.verification_status,
        "collection_focus": record.collection_focus or "",
        "estimated_size": "" if record.estimated_size is None else record.estimated_size,
        "rights_status": record.rights_status,
        "rights_values": " | ".join(record.rights_values),
        "record_status": record.record_status,
        "last_checked_at": record.last_checked_at or "",
        "source_type": endpoint.source.source_type,
        "source_url": endpoint.source.source_url,
        "source_page_url": endpoint.source.source_page_url or "",
        "observed_at": endpoint.source.observed_at or "",
    }
