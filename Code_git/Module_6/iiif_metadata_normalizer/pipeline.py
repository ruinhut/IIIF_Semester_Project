"""Orchestration for metadata extraction and normalization."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping

from .extractor import extract_and_normalize, normalize_language
from .models import MODULE_6_SCHEMA_VERSION, Module5ResearchRecord, stable_resource_id
from .reference_text import extract_reference_text_resources
from .catalogue_reference import extract_catalogue_references
from .store import read_jsonl, write_jsonl, write_metadata_csv, write_resource_csv


def run_pipeline(config_path: Path, *, limit: int | None = None) -> dict[str, Any]:
    """Normalize every Module 5 record retained for academic research."""

    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    base = config_path.parent
    manifests_path = _resolve(base, config["research_manifests_jsonl"])
    resources_path = _resolve(base, config["research_resource_inventory_jsonl"])
    module4_dir = _resolve(base, config["module_4_directory"])
    output_dir = _resolve(base, config["output_directory"])
    log_dir = _resolve(base, config["log_directory"])
    language_priority = list(config.get("language_priority", ["en", "none", "und"]))
    reference_sources = []
    reference_audit = []
    source_config = config.get("provider_reference_sources")
    if source_config:
        source_path = _resolve(base, source_config)
        reference_sources = json.loads(source_path.read_text(encoding="utf-8"))["sources"]
    reference_cache = _resolve(base, config["catalogue_reference_cache_directory"]) if config.get(
        "catalogue_reference_cache_directory") else output_dir.parent / "catalogue_reference_cache"
    configured_limit = config.get("run", {}).get("max_records")
    effective_limit = limit if limit is not None else configured_limit
    started = datetime.now().astimezone()

    handoffs = read_jsonl(manifests_path)
    if effective_limit is not None:
        handoffs = handoffs[: int(effective_limit)]
    resource_rows = read_jsonl(resources_path) if resources_path.exists() else []
    selected_ids = {str(row.get("manifest_id", "")) for row in handoffs}
    normalized: list[dict[str, Any]] = []
    reference_texts: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for raw_handoff in handoffs:
        manifest_id = str(raw_handoff.get("manifest_id", ""))
        try:
            handoff = Module5ResearchRecord.from_mapping(raw_handoff)
            raw_path = (module4_dir / handoff.raw_manifest_path).resolve()
            raw_bytes = raw_path.read_bytes()
            document = json.loads(raw_bytes.decode("utf-8-sig"))
            record = extract_and_normalize(
                document,
                handoff.data,
                language_priority=language_priority,
                normalized_at=datetime.now().astimezone().isoformat(timespec="seconds"),
            )
            record["module_6_schema_version"] = MODULE_6_SCHEMA_VERSION
            normalized.append(record)
            for reference in extract_reference_text_resources(document, handoff.data):
                reference["module_6_schema_version"] = MODULE_6_SCHEMA_VERSION
                reference_texts.append(reference)
            for reference in extract_catalogue_references(document, handoff.data, reference_sources, reference_cache, reference_audit):
                reference["module_6_schema_version"] = MODULE_6_SCHEMA_VERSION
                reference_texts.append(reference)
                language = reference.get("language")
                if isinstance(language, str) and language.strip():
                    languages = record["normalized_metadata"]["languages"]
                    if not any(item["value"] == language for item in languages):
                        languages.append({"value": language, "code": normalize_language(language),
                            "source_label": "Catalogue original transcription language",
                            "json_path": reference["catalogue_provenance"]["language_field"],
                            "source_url": reference["source_url"]})
                record.setdefault("catalogue_enrichment", []).append(reference["catalogue_provenance"])
        except Exception as exc:
            failed.append({
                "manifest_id": manifest_id,
                "manifest_url": raw_handoff.get("manifest_url"),
                "error_type": type(exc).__name__,
                "error": str(exc),
            })

    successful_ids = {row["manifest_id"] for row in normalized}
    normalized_resources: list[dict[str, Any]] = []
    for resource in resource_rows:
        manifest_id = str(resource.get("manifest_id", ""))
        if manifest_id not in selected_ids or manifest_id not in successful_ids:
            continue
        if resource.get("research_status") != "retained":
            continue
        if resource.get("academic_analysis_allowed") is not True:
            continue
        normalized_resources.append({
            **resource,
            "resource_id": stable_resource_id(resource),
            "module_6_schema_version": MODULE_6_SCHEMA_VERSION,
        })

    retained_canvas_keys = {
        (
            str(row.get("manifest_id", "")),
            row.get("canvas_index"),
            str(row.get("canvas_id") or ""),
        )
        for row in normalized_resources
    }
    reference_texts = [
        row for row in reference_texts
        if row.get("alignment_scope") == "manifest"
        or (
            str(row.get("manifest_id", "")),
            row.get("canvas_index"),
            str(row.get("canvas_id") or ""),
        ) in retained_canvas_keys
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "normalized_records.jsonl", normalized)
    write_jsonl(output_dir / "normalized_resources.jsonl", normalized_resources)
    write_jsonl(output_dir / "normalized_reference_texts.jsonl", reference_texts)
    write_jsonl(output_dir / "catalogue_reference_audit.jsonl", reference_audit)
    write_metadata_csv(output_dir / "metadata_summary.csv", normalized)
    write_resource_csv(output_dir / "normalized_resources.csv", normalized_resources)
    write_jsonl(output_dir / "failed_records.jsonl", failed)

    finished = datetime.now().astimezone()
    summary = {
        "module": "Module 6 - Metadata Extraction and Normalization",
        "schema_version": MODULE_6_SCHEMA_VERSION,
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "input_manifest_records": len(handoffs),
        "normalized_records": len(normalized),
        "complete_records": sum(row["quality"]["status"] == "complete" for row in normalized),
        "partial_records": sum(row["quality"]["status"] == "partial" for row in normalized),
        "failed_records": len(failed),
        "research_resource_rows": len(normalized_resources),
        "normalized_resources": len(normalized_resources),
        "normalized_reference_texts": len(reference_texts),
        "catalogue_reference_enrichment_attempts": len(reference_audit),
        "catalogue_reference_enrichment_failures": sum(p["status"] == "catalogue_enrichment_failed" for p in reference_audit),
        "output_directory": str(output_dir),
    }
    _write_log(log_dir, finished, summary)
    return summary


def _write_log(log_dir: Path, now: datetime, summary: Mapping[str, Any]) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"Module6_{now.strftime('%Y-%m-%d_%H-%M-%S')}_log.txt"
    lines = [f"{key}: {value}" for key, value in summary.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()
