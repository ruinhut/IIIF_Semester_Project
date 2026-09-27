"""Orchestrate mapping, validation, linking, and final bundle creation."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping

from .mapper import map_media, map_record
from .models import MEDIA_SCHEMA_VERSION, RECORD_SCHEMA_VERSION
from .store import file_descriptor, read_jsonl, write_json, write_jsonl, write_media_csv, write_record_csv
from .validator import validate_media, validate_record


def run_pipeline(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    base = config_path.parent
    records_path = _resolve(base, config["normalized_records_jsonl"])
    resources_path = _resolve(base, config["normalized_resources_jsonl"])
    profile_path = _resolve(base, config["profile_json"])
    record_schema_path = _resolve(base, config["record_schema_json"])
    media_schema_path = _resolve(base, config["media_schema_json"])
    output_dir = _resolve(base, config["output_directory"])
    log_dir = _resolve(base, config["log_directory"])
    profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    json.loads(record_schema_path.read_text(encoding="utf-8-sig"))
    json.loads(media_schema_path.read_text(encoding="utf-8-sig"))
    _validate_profile(profile)
    now = datetime.now().astimezone()
    exported_at = now.isoformat(timespec="seconds")

    source_records = read_jsonl(records_path)
    source_resources = read_jsonl(resources_path)
    resource_counts = Counter(str(row.get("manifest_id", "")) for row in source_resources)
    mapped_records: list[dict[str, Any]] = []
    rejected_records: list[dict[str, Any]] = []
    for source in source_records:
        try:
            mapped = map_record(source, media_count=resource_counts[str(source.get("manifest_id", ""))], exported_at=exported_at)
            issues = validate_record(mapped)
        except Exception as exc:
            mapped = None
            issues = [{"code": "mapping", "path": "$", "message": str(exc)}]
        if issues:
            rejected_records.append({"source": source, "mapped": mapped, "issues": issues})
        else:
            mapped_records.append(mapped)

    valid_record_ids = {row["record_id"] for row in mapped_records}
    duplicate_record_ids = _duplicates(row["record_id"] for row in mapped_records)
    if duplicate_record_ids:
        kept: list[dict[str, Any]] = []
        for row in mapped_records:
            if row["record_id"] in duplicate_record_ids:
                rejected_records.append({"source": row, "mapped": row, "issues": [{"code": "duplicate", "path": "$.record_id", "message": "record_id is duplicated"}]})
            else:
                kept.append(row)
        mapped_records = kept
        valid_record_ids = {row["record_id"] for row in mapped_records}

    mapped_media: list[dict[str, Any]] = []
    rejected_media: list[dict[str, Any]] = []
    for source in source_resources:
        mapped = map_media(source)
        issues = validate_media(mapped)
        if mapped.get("record_id") not in valid_record_ids:
            issues.append({"code": "foreign_key", "path": "$.record_id", "message": "does not reference a valid object record"})
        if issues:
            rejected_media.append({"source": source, "mapped": mapped, "issues": issues})
        else:
            mapped_media.append(mapped)

    duplicate_resource_ids = _duplicates(row["resource_id"] for row in mapped_media)
    if duplicate_resource_ids:
        kept_media: list[dict[str, Any]] = []
        for row in mapped_media:
            if row["resource_id"] in duplicate_resource_ids:
                rejected_media.append({"source": row, "mapped": row, "issues": [{"code": "duplicate", "path": "$.resource_id", "message": "resource_id is duplicated"}]})
            else:
                kept_media.append(row)
        mapped_media = kept_media

    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "records_jsonl": output_dir / "common_records.jsonl",
        "media_jsonl": output_dir / "common_media.jsonl",
        "records_csv": output_dir / "common_records.csv",
        "media_csv": output_dir / "common_media.csv",
        "rejected_records": output_dir / "rejected_records.jsonl",
        "rejected_media": output_dir / "rejected_media.jsonl",
    }
    write_jsonl(files["records_jsonl"], mapped_records)
    write_jsonl(files["media_jsonl"], mapped_media)
    write_record_csv(files["records_csv"], mapped_records)
    write_media_csv(files["media_csv"], mapped_media)
    write_jsonl(files["rejected_records"], rejected_records)
    write_jsonl(files["rejected_media"], rejected_media)
    bundle = {
        "bundle_version": "iiif-time-atlas-bundle-0.1",
        "generated_at": exported_at,
        "profile_version": profile["profile_version"],
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "media_schema_version": MEDIA_SCHEMA_VERSION,
        "counts": {
            "input_records": len(source_records), "valid_records": len(mapped_records),
            "rejected_records": len(rejected_records), "input_media": len(source_resources),
            "valid_media": len(mapped_media), "rejected_media": len(rejected_media),
        },
        "source_inputs": {"records": str(records_path), "resources": str(resources_path)},
        "schemas": {"record": str(record_schema_path), "media": str(media_schema_path)},
        "files": [file_descriptor(path) for path in files.values()],
    }
    write_json(output_dir / "dataset_manifest.json", bundle)
    summary = {
        "module": "Module 7 - Common-Schema Validator and Exporter",
        "profile_version": profile["profile_version"],
        "generated_at": exported_at,
        **bundle["counts"],
        "output_directory": str(output_dir),
    }
    _write_log(log_dir, now, summary)
    return summary


def _validate_profile(profile: Mapping[str, Any]) -> None:
    if profile.get("record_schema_version") != RECORD_SCHEMA_VERSION:
        raise ValueError("Profile record schema version does not match the implementation")
    if profile.get("media_schema_version") != MEDIA_SCHEMA_VERSION:
        raise ValueError("Profile media schema version does not match the implementation")


def _duplicates(values: Any) -> set[str]:
    counter = Counter(str(value) for value in values)
    return {value for value, count in counter.items() if count > 1}


def _write_log(log_dir: Path, now: datetime, summary: Mapping[str, Any]) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"Module7_{now.strftime('%Y-%m-%d_%H-%M-%S')}_log.txt"
    path.write_text("\n".join(f"{key}: {value}" for key, value in summary.items()) + "\n", encoding="utf-8")


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()
