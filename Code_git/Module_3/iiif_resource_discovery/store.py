"""Persist Module 3 provider reports, Manifest handoff data, CSV, and logs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import ProviderInputRecord


PROVIDER_CSV_COLUMNS = (
    "provider_id",
    "name",
    "input_endpoint",
    "module_2_result",
    "module_3_status",
    "manifest_count",
    "resolved_endpoint_count",
    "html_pages_visited",
    "stream_pages_visited",
    "collections_visited",
    "issue_count",
    "truncated",
)


def read_provider_jsonl(path: Path) -> list[ProviderInputRecord]:
    """Read and validate the Module 2 handoff file."""

    records: list[ProviderInputRecord] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                records.append(ProviderInputRecord.from_mapping(value))
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid Module 2 record at {path}:{line_number}: {exc}") from exc
    return records


def write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> int:
    """Write one complete JSON object per line and return the count."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            json.dump(dict(record), handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            count += 1
    return count


def write_provider_csv(path: Path, provider_reports: Iterable[Mapping[str, Any]]) -> int:
    """Write a flattened summary suitable for spreadsheet inspection."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROVIDER_CSV_COLUMNS)
        writer.writeheader()
        for report in provider_reports:
            discovery = report.get("resource_discovery", {})
            endpoint_check = report.get("endpoint_check", {})
            writer.writerow(
                {
                    "provider_id": report.get("provider_id", ""),
                    "name": report.get("name", ""),
                    "input_endpoint": report.get("discovery_endpoint", ""),
                    "module_2_result": endpoint_check.get("check_result", "")
                    if isinstance(endpoint_check, Mapping)
                    else "",
                    "module_3_status": discovery.get("status", "")
                    if isinstance(discovery, Mapping)
                    else "",
                    "manifest_count": discovery.get("manifest_count", 0)
                    if isinstance(discovery, Mapping)
                    else 0,
                    "resolved_endpoint_count": len(discovery.get("resolved_endpoints", []))
                    if isinstance(discovery, Mapping)
                    else 0,
                    "html_pages_visited": discovery.get("html_pages_visited", 0)
                    if isinstance(discovery, Mapping)
                    else 0,
                    "stream_pages_visited": discovery.get("stream_pages_visited", 0)
                    if isinstance(discovery, Mapping)
                    else 0,
                    "collections_visited": discovery.get("collections_visited", 0)
                    if isinstance(discovery, Mapping)
                    else 0,
                    "issue_count": len(discovery.get("issues", []))
                    if isinstance(discovery, Mapping)
                    else 0,
                    "truncated": discovery.get("truncated", False)
                    if isinstance(discovery, Mapping)
                    else False,
                }
            )
            count += 1
    return count


def write_text(path: Path, value: str) -> None:
    """Write a UTF-8 human-readable run log."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value.rstrip())
        handle.write("\n")
