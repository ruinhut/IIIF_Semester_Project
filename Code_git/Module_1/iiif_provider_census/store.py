"""Persist Module 1 data contracts as UTF-8 JSONL, CSV, and JSON.

JSONL is the canonical machine-readable format because each provider can be
processed independently. CSV is a smaller, flattened view for human review.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .models import ProviderRecord


CSV_COLUMNS = (
    "provider_id",
    "name",
    "institution_url",
    "discovery_endpoint",
    "discovery_type",
    "stream_label",
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
    """Write one complete provider JSON object per line and return its count."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            json.dump(record.to_dict(), handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            count += 1
    return count


def read_jsonl(path: Path) -> list[ProviderRecord]:
    """Read and validate canonical provider records from a JSONL file."""

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
    """Write a spreadsheet-friendly view without nested raw source data."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(_csv_row(record))
            count += 1
    return count


def write_json(path: Path, value: Any) -> None:
    """Write an indented JSON document such as the run summary."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _csv_row(record: ProviderRecord) -> dict[str, Any]:
    """Flatten one nested ProviderRecord into the documented CSV columns."""

    return {
        "provider_id": record.provider_id,
        "name": record.name,
        "institution_url": record.institution_url or "",
        "discovery_endpoint": record.discovery_endpoint,
        "discovery_type": record.discovery_type,
        "stream_label": record.stream_label or "",
        "collection_focus": record.collection_focus or "",
        "estimated_size": "" if record.estimated_size is None else record.estimated_size,
        "rights_status": record.rights_status,
        "rights_values": " | ".join(record.rights_values),
        "record_status": record.record_status,
        "last_checked_at": record.last_checked_at or "",
        "source_type": record.source.source_type,
        "source_url": record.source.source_url,
        "source_page_url": record.source.source_page_url or "",
        "observed_at": record.source.observed_at or "",
    }
