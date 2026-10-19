"""Read Module 1 JSONL and persist Module 2 endpoint results."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .models import CheckedProviderRecord, ProviderInputRecord


CSV_COLUMNS = (
    "provider_id",
    "name",
    "institution_url",
    "endpoint_role",
    "candidate_url",
    "candidate_discovery_type",
    "verification_status",
    "check_result",
    "status_code",
    "requested_url",
    "final_url",
    "redirect_count",
    "content_type",
    "response_time_ms",
    "response_bytes",
    "body_truncated",
    "json_parseable",
    "json_resource_type",
    "attempt_count",
    "checked_at",
    "error_type",
    "error_message",
    "source_type",
    "source_url",
    "source_page_url",
)


def read_provider_jsonl(path: Path) -> list[ProviderInputRecord]:
    """Read Module 1 schema 1 or schema 2 institution records."""

    records: list[ProviderInputRecord] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                records.append(ProviderInputRecord.from_mapping(value))
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid Module 1 record at {path}:{line_number}: {exc}"
                ) from exc
    return records


def write_checked_jsonl(
    path: Path, records: Iterable[CheckedProviderRecord]
) -> int:
    """Write one provider-endpoint check per JSONL line."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            json.dump(record.to_dict(), handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            count += 1
    return count


def read_checked_jsonl(path: Path) -> list[CheckedProviderRecord]:
    """Read stored Module 2 schema 1 or schema 2 records."""

    records: list[CheckedProviderRecord] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                records.append(CheckedProviderRecord.from_mapping(value))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid Module 2 record at {path}:{line_number}: {exc}"
                ) from exc
    return records


def write_csv(path: Path, records: Iterable[CheckedProviderRecord]) -> int:
    """Write a flattened UTF-8 endpoint-check table."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(_csv_row(record))
            count += 1
    return count


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value.rstrip())
        handle.write("\n")


def _csv_row(record: CheckedProviderRecord) -> dict[str, Any]:
    check = record.endpoint_check
    candidate = record.endpoint_candidate
    assert candidate is not None
    candidate_data = candidate.to_dict()
    source = candidate_data.get("source")
    if not isinstance(source, dict):
        source = {}
    provider_data = record.provider.to_dict()
    return {
        "provider_id": record.provider.provider_id,
        "name": record.provider.name,
        "institution_url": provider_data.get("institution_url") or "",
        "endpoint_role": candidate.endpoint_role,
        "candidate_url": candidate.url,
        "candidate_discovery_type": candidate.discovery_type,
        "verification_status": candidate_data.get("verification_status", ""),
        "check_result": check.check_result,
        "status_code": "" if check.status_code is None else check.status_code,
        "requested_url": check.requested_url,
        "final_url": check.final_url or "",
        "redirect_count": len(check.redirect_chain),
        "content_type": check.content_type or "",
        "response_time_ms": check.response_time_ms,
        "response_bytes": check.response_bytes,
        "body_truncated": check.body_truncated,
        "json_parseable": (
            "" if check.json_parseable is None else check.json_parseable
        ),
        "json_resource_type": check.json_resource_type or "",
        "attempt_count": check.attempt_count,
        "checked_at": check.checked_at,
        "error_type": check.error_type or "",
        "error_message": check.error_message or "",
        "source_type": source.get("source_type", ""),
        "source_url": source.get("source_url", ""),
        "source_page_url": source.get("source_page_url", ""),
    }
