"""Persistence helpers for Module 4 inputs, outputs, raw JSON, and logs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import ManifestInputRecord


RESOURCE_COLUMNS = (
    "manifest_id",
    "manifest_url",
    "provider_names",
    "presentation_version",
    "rights_values",
    "canvas_index",
    "canvas_id",
    "canvas_label",
    "body_id",
    "body_type",
    "body_format",
    "image_service_urls",
)


def read_manifest_jsonl(path: Path) -> list[ManifestInputRecord]:
    """Read Module 3 handoff JSONL and reject conflicting duplicate IDs."""

    records: list[ManifestInputRecord] = []
    seen: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                record = ManifestInputRecord.from_mapping(value)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid Module 3 record at {path}:{line_number}: {exc}"
                ) from exc
            previous = seen.get(record.manifest_id)
            if previous is not None:
                if previous != record.manifest_url:
                    raise ValueError(
                        f"Conflicting duplicate manifest_id {record.manifest_id!r}"
                    )
                continue
            seen[record.manifest_id] = record.manifest_url
            records.append(record)
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


def write_resource_csv(
    path: Path, records: Iterable[Mapping[str, Any]]
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESOURCE_COLUMNS)
        writer.writeheader()
        for record in records:
            row = {name: record.get(name, "") for name in RESOURCE_COLUMNS}
            for name in ("provider_names", "rights_values", "image_service_urls"):
                value = row[name]
                if isinstance(value, list):
                    row[name] = " | ".join(str(item) for item in value)
            writer.writerow(row)
            count += 1
    return count


def write_raw_response(path: Path, body: bytes) -> None:
    """Atomically preserve the exact parseable JSON response bytes."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value.rstrip())
        handle.write("\n")
