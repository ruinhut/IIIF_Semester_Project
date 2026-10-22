"""Input-contract helpers for the three linked Module 7 outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping
from urllib.parse import urlparse


@dataclass(frozen=True)
class DownloadItem:
    record: Mapping[str, Any]
    media: Mapping[str, Any]
    ocr_profile: Mapping[str, Any]
    reference_texts: tuple[Mapping[str, Any], ...]
    download_url: str

    @property
    def record_id(self) -> str:
        return str(self.media["record_id"])

    @property
    def resource_id(self) -> str:
        return str(self.media["resource_id"])

    @property
    def sequence(self) -> int:
        return int(self.media.get("sequence", 0))

    def relative_directory(self) -> Path:
        record = safe_component(self.record_id)
        resource = safe_component(self.resource_id)
        return Path(record) / f"{self.sequence:06d}_{resource}"


def build_download_items(
    records: list[dict[str, Any]],
    media_rows: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    reference_rows: list[dict[str, Any]] | None = None,
    *,
    require_academic_analysis_allowed: bool,
    require_reference_text: bool = False,
) -> tuple[list[DownloadItem], list[dict[str, Any]]]:
    record_index = _unique_index(records, "record_id", "common record")
    profile_index = _unique_index(profiles, "record_id", "OCR profile")
    seen_resources: set[str] = set()
    items: list[DownloadItem] = []
    skipped: list[dict[str, Any]] = []
    references_by_resource: dict[str, list[dict[str, Any]]] = {}
    for row in reference_rows or []:
        resource_id = str(row.get("resource_id") or "").strip()
        if resource_id:
            references_by_resource.setdefault(resource_id, []).append(row)

    for position, media in enumerate(media_rows, 1):
        resource_id = _required_text(media, "resource_id", position, "media")
        record_id = _required_text(media, "record_id", position, "media")
        if resource_id in seen_resources:
            raise ValueError(f"Duplicate media resource_id: {resource_id}")
        seen_resources.add(resource_id)
        if record_id not in record_index:
            raise ValueError(
                f"Media {resource_id} references missing common record {record_id}"
            )
        if record_id not in profile_index:
            raise ValueError(
                f"Media {resource_id} references missing OCR profile {record_id}"
            )
        rights = media.get("rights")
        academic_allowed = (
            isinstance(rights, Mapping)
            and rights.get("academic_analysis_allowed") is True
        )
        if require_academic_analysis_allowed and not academic_allowed:
            skipped.append({
                "resource_id": resource_id,
                "record_id": record_id,
                "reason": "academic_analysis_not_allowed",
            })
            continue
        image = media.get("image")
        if not isinstance(image, Mapping):
            skipped.append({
                "resource_id": resource_id,
                "record_id": record_id,
                "reason": "missing_image_object",
            })
            continue
        url = str(image.get("download_url") or image.get("id") or "").strip()
        if not is_http_url(url):
            skipped.append({
                "resource_id": resource_id,
                "record_id": record_id,
                "reason": "missing_http_download_url",
                "value": url or None,
            })
            continue
        reference_texts = tuple(references_by_resource.get(resource_id, []))
        if require_reference_text and not reference_texts:
            skipped.append({
                "resource_id": resource_id,
                "record_id": record_id,
                "reason": "missing_institution_reference_text",
            })
            continue
        items.append(DownloadItem(
            record=record_index[record_id],
            media=media,
            ocr_profile=profile_index[record_id],
            reference_texts=reference_texts,
            download_url=url,
        ))
    return items, skipped


def safe_component(value: str, *, limit: int = 100) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._")
    cleaned = cleaned or "unnamed"
    return cleaned[:limit]


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _unique_index(
    rows: list[dict[str, Any]], key: str, label: str
) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for position, row in enumerate(rows, 1):
        value = _required_text(row, key, position, label)
        if value in output:
            raise ValueError(f"Duplicate {label} {key}: {value}")
        output[value] = row
    return output


def _required_text(
    row: Mapping[str, Any], key: str, position: int, label: str
) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} row {position} requires non-empty {key}")
    return value.strip()
