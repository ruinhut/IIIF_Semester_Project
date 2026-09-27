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
        "manifest_url", "provider_names", "media_count", "quality_status",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            obj, source = row["object"], row["source"]
            starts = [item["start_year"] for item in obj["dates"] if item["start_year"] is not None]
            ends = [item["end_year"] for item in obj["dates"] if item["end_year"] is not None]
            writer.writerow({
                "record_id": row["record_id"], "identifier": obj["identifier"],
                "title": obj["title"] or "",
                "creators": _join(item["value"] for item in obj["creators"]),
                "date_start": min(starts) if starts else "",
                "date_end": max(ends) if ends else "",
                "date_values": _join(item["raw"] for item in obj["dates"]),
                "places": _join(item["normalized"] or item["raw"] for item in obj["places"]),
                "rights_category": row["rights"]["category"],
                "manifest_url": source["manifest_url"],
                "provider_names": _join(item.get("provider_name") for item in source["providers"]),
                "media_count": row["media_count"],
                "quality_status": row["quality"].get("status", ""),
            })
    temp.replace(path)


def write_media_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    fields = [
        "resource_id", "record_id", "sequence", "canvas_id", "canvas_label",
        "image_id", "image_type", "image_format", "image_service_urls",
        "rights_category", "source_manifest_url",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "resource_id": row["resource_id"], "record_id": row["record_id"],
                "sequence": row["sequence"], "canvas_id": row["canvas"].get("id"),
                "canvas_label": row["canvas"].get("label"), "image_id": row["image"].get("id"),
                "image_type": row["image"].get("type"), "image_format": row["image"].get("format"),
                "image_service_urls": _join(row["image"].get("service_urls", [])),
                "rights_category": row["rights"].get("category"),
                "source_manifest_url": row["source_manifest_url"],
            })
    temp.replace(path)


def file_descriptor(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"name": path.name, "bytes": len(payload), "sha256": sha256(payload).hexdigest()}


def _atomic_write(path: Path, content: str, encoding: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding=encoding, newline="\n")
    temp.replace(path)


def _join(values: Iterable[Any]) -> str:
    return " | ".join(str(value) for value in values if value not in (None, ""))
