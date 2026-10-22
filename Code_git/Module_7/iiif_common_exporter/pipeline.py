"""Orchestrate mapping, validation, linking, and final bundle creation."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from .mapper import map_media, map_record, map_reference_text
from .models import (
    MEDIA_SCHEMA_VERSION,
    OCR_PROFILE_SCHEMA_VERSION,
    REFERENCE_TEXT_SCHEMA_VERSION,
    RECORD_SCHEMA_VERSION,
)
from .ocr_profiler import (
    build_ocr_profile,
    select_ground_truth_candidates,
    summarize_ocr_profiles,
)
from .store import (
    file_descriptor,
    read_jsonl,
    write_json,
    write_jsonl,
    write_media_csv,
    write_ocr_candidate_csv,
    write_ocr_profile_csv,
    write_record_csv,
)
from .validator import validate_media, validate_record


def run_pipeline(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    base = config_path.parent
    records_path = _resolve(base, config["normalized_records_jsonl"])
    resources_path = _resolve(base, config["normalized_resources_jsonl"])
    reference_texts_path = _optional_input_path(
        base,
        config.get("normalized_reference_texts_jsonl"),
        resources_path.parent / "normalized_reference_texts.jsonl",
    )
    profile_path = _resolve(base, config["profile_json"])
    record_schema_path = _resolve(base, config["record_schema_json"])
    media_schema_path = _resolve(base, config["media_schema_json"])
    ocr_schema_path = _resolve(base, config["ocr_profile_schema_json"])
    output_dir = _resolve(base, config["output_directory"])
    log_dir = _resolve(base, config["log_directory"])
    profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    record_schema = json.loads(record_schema_path.read_text(encoding="utf-8-sig"))
    media_schema = json.loads(media_schema_path.read_text(encoding="utf-8-sig"))
    ocr_schema = json.loads(ocr_schema_path.read_text(encoding="utf-8-sig"))
    Draft202012Validator.check_schema(record_schema)
    Draft202012Validator.check_schema(media_schema)
    Draft202012Validator.check_schema(ocr_schema)
    record_schema_validator = Draft202012Validator(record_schema)
    media_schema_validator = Draft202012Validator(media_schema)
    ocr_schema_validator = Draft202012Validator(ocr_schema)
    _validate_profile(profile)
    now = datetime.now().astimezone()
    exported_at = now.isoformat(timespec="seconds")

    source_records = read_jsonl(records_path)
    source_resources = read_jsonl(resources_path)
    source_reference_texts = (
        read_jsonl(reference_texts_path) if reference_texts_path else []
    )
    resource_counts = Counter(str(row.get("manifest_id", "")) for row in source_resources)
    mapped_records: list[dict[str, Any]] = []
    rejected_records: list[dict[str, Any]] = []
    for source in source_records:
        try:
            mapped = map_record(source, media_count=resource_counts[str(source.get("manifest_id", ""))], exported_at=exported_at)
            issues = _schema_issues(record_schema_validator, mapped) + validate_record(mapped)
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
        issues = _schema_issues(media_schema_validator, mapped) + validate_media(mapped)
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

    media_by_canvas = {
        (
            str(row.get("record_id", "")),
            row.get("sequence"),
            str(row.get("canvas", {}).get("id") or ""),
        ): row
        for row in mapped_media
    }
    mapped_reference_texts: list[dict[str, Any]] = []
    rejected_reference_texts: list[dict[str, Any]] = []
    for source in source_reference_texts:
        key = (
            str(source.get("manifest_id", "")),
            source.get("canvas_index"),
            str(source.get("canvas_id") or ""),
        )
        media = media_by_canvas.get(key)
        if source.get("alignment_scope") == "canvas" and media is None:
            rejected_reference_texts.append({
                "source": source,
                "issues": [{
                    "code": "foreign_key",
                    "path": "$.canvas_id",
                    "message": "does not reference an exported page image",
                }],
            })
            continue
        mapped_reference_texts.append(map_reference_text(source, media))

    source_by_id = {
        str(row.get("manifest_id", "")): row for row in source_records
    }
    ocr_profiles = [
        build_ocr_profile(source_by_id[row["record_id"]], row)
        for row in mapped_records
    ]
    for index, profile_row in enumerate(ocr_profiles):
        issues = _schema_issues(ocr_schema_validator, profile_row)
        if issues:
            raise ValueError(
                f"Generated OCR profile {index} failed schema validation: {issues}"
            )
    ocr_config = config.get("ocr_profile", {})
    max_ground_truth_records = int(
        ocr_config.get("max_ground_truth_records", 24)
    )
    pages_per_record = int(ocr_config.get("pages_per_record", 3))
    max_records_per_provider = int(
        ocr_config.get("max_records_per_provider", 4)
    )
    ocr_candidates = select_ground_truth_candidates(
        ocr_profiles,
        mapped_media,
        max_records=max_ground_truth_records,
        pages_per_record=pages_per_record,
        max_records_per_provider=max_records_per_provider,
    )
    ocr_summary = summarize_ocr_profiles(ocr_profiles)

    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "records_jsonl": output_dir / "common_records.jsonl",
        "media_jsonl": output_dir / "common_media.jsonl",
        "records_csv": output_dir / "common_records.csv",
        "media_csv": output_dir / "common_media.csv",
        "rejected_records": output_dir / "rejected_records.jsonl",
        "rejected_media": output_dir / "rejected_media.jsonl",
        "ocr_profiles_jsonl": output_dir / "ocr_document_profiles.jsonl",
        "ocr_profiles_csv": output_dir / "ocr_document_profiles.csv",
        "ocr_summary": output_dir / "ocr_dataset_summary.json",
        "ocr_candidates_jsonl": output_dir / "ocr_ground_truth_candidates.jsonl",
        "ocr_candidates_csv": output_dir / "ocr_ground_truth_candidates.csv",
        "reference_texts_jsonl": output_dir / "institution_reference_texts.jsonl",
        "rejected_reference_texts": output_dir / "rejected_reference_texts.jsonl",
    }
    write_jsonl(files["records_jsonl"], mapped_records)
    write_jsonl(files["media_jsonl"], mapped_media)
    write_record_csv(files["records_csv"], mapped_records)
    write_media_csv(files["media_csv"], mapped_media)
    write_jsonl(files["rejected_records"], rejected_records)
    write_jsonl(files["rejected_media"], rejected_media)
    write_jsonl(files["ocr_profiles_jsonl"], ocr_profiles)
    write_ocr_profile_csv(files["ocr_profiles_csv"], ocr_profiles)
    write_json(files["ocr_summary"], ocr_summary)
    write_jsonl(files["ocr_candidates_jsonl"], ocr_candidates)
    write_ocr_candidate_csv(files["ocr_candidates_csv"], ocr_candidates)
    write_jsonl(files["reference_texts_jsonl"], mapped_reference_texts)
    write_jsonl(files["rejected_reference_texts"], rejected_reference_texts)
    bundle = {
        "bundle_version": "iiif-time-atlas-bundle-0.2",
        "generated_at": exported_at,
        "profile_version": profile["profile_version"],
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "media_schema_version": MEDIA_SCHEMA_VERSION,
        "ocr_profile_schema_version": OCR_PROFILE_SCHEMA_VERSION,
        "reference_text_schema_version": REFERENCE_TEXT_SCHEMA_VERSION,
        "counts": {
            "input_records": len(source_records), "valid_records": len(mapped_records),
            "rejected_records": len(rejected_records), "input_media": len(source_resources),
            "valid_media": len(mapped_media), "rejected_media": len(rejected_media),
            "ocr_profiles": len(ocr_profiles),
            "ocr_ground_truth_candidates": len(ocr_candidates),
            "institution_reference_texts": len(mapped_reference_texts),
            "rejected_reference_texts": len(rejected_reference_texts),
        },
        "source_inputs": {
            "records": str(records_path),
            "resources": str(resources_path),
            "reference_texts": str(reference_texts_path) if reference_texts_path else None,
        },
        "schemas": {
            "record": str(record_schema_path),
            "media": str(media_schema_path),
            "ocr_profile": str(ocr_schema_path),
        },
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


def _schema_issues(validator: Draft202012Validator, value: Mapping[str, Any]) -> list[dict[str, str]]:
    """Convert JSON Schema errors into the module's stable issue format."""

    return [
        {"code": "json_schema", "path": error.json_path, "message": error.message}
        for error in sorted(validator.iter_errors(value), key=lambda item: item.json_path)
    ]


def _validate_profile(profile: Mapping[str, Any]) -> None:
    if profile.get("record_schema_version") != RECORD_SCHEMA_VERSION:
        raise ValueError("Profile record schema version does not match the implementation")
    if profile.get("media_schema_version") != MEDIA_SCHEMA_VERSION:
        raise ValueError("Profile media schema version does not match the implementation")
    if profile.get("ocr_profile_schema_version") != OCR_PROFILE_SCHEMA_VERSION:
        raise ValueError("Profile OCR schema version does not match the implementation")


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


def _optional_input_path(
    base: Path, configured: Any, default_path: Path
) -> Path | None:
    if configured is not None:
        path = _resolve(base, str(configured))
        if not path.is_file():
            raise FileNotFoundError(f"Reference-text input does not exist: {path}")
        return path
    return default_path.resolve() if default_path.is_file() else None
