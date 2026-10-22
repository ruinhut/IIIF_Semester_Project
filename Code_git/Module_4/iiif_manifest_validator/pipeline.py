"""Configuration-driven orchestration for Module 4."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Any, Mapping, Optional

from .fetch import FetchError, FetchedResponse, HttpFetcher
from .models import (
    MODULE_4_SCHEMA_VERSION,
    ManifestInputRecord,
    ValidationResult,
)
from .store import (
    read_manifest_jsonl,
    write_jsonl,
    write_raw_response,
    write_resource_csv,
    write_text,
)
from .validator import validate_manifest
from .normalization import infer_missing_manifest_id


@dataclass(frozen=True)
class PipelineResult:
    input_manifest_count: int
    processed_manifest_count: int
    status_counts: Mapping[str, int]
    valid_manifest_count: int
    canvas_count: int
    image_body_count: int
    image_service_count: int
    cache_hit_count: int
    normalized_manifest_count: int
    validated_manifests_jsonl: Path
    resource_inventory_jsonl: Path
    resource_inventory_csv: Path
    invalid_manifests_jsonl: Path
    manual_review_jsonl: Path
    unavailable_manifests_jsonl: Path
    log_txt: Path


def run_pipeline(
    config_path: Path,
    *,
    limit: int | None = None,
    force_refresh: bool | None = None,
    run_time: datetime | None = None,
    fetcher: HttpFetcher | None = None,
) -> PipelineResult:
    """Fetch, cache, validate, inventory, and classify Manifest records."""

    config_path = config_path.resolve()
    config = _read_config(config_path)
    base_directory = config_path.parent

    input_path = _resolve_path(
        str(config.get("input_jsonl", "../Module_3/data/output/manifest_urls.jsonl")),
        base_directory,
    )
    raw_directory = _resolve_path(
        str(config.get("raw_manifest_directory", "data/raw_manifests")),
        base_directory,
    )
    output_directory = _resolve_path(
        str(config.get("output_directory", "data/output")),
        base_directory,
    )
    log_directory = _resolve_path(
        str(config.get("log_directory", "data/log")),
        base_directory,
    )

    run_config = _mapping(config.get("run", {}), "run")
    normalization = _mapping(config.get("normalization", {}), "normalization")
    infer_transport_id = normalization.get("infer_missing_manifest_id", True)
    if not isinstance(infer_transport_id, bool):
        raise ValueError("normalization.infer_missing_manifest_id must be boolean")
    configured_limit = _optional_positive_int(
        run_config.get("max_records"), "run.max_records"
    )
    effective_limit = _optional_positive_int(limit, "limit") if limit is not None else configured_limit
    configured_force = bool(run_config.get("force_refresh", False))
    effective_force = configured_force if force_refresh is None else force_refresh
    delay_seconds = float(run_config.get("delay_between_requests_seconds", 0.1))
    if delay_seconds < 0:
        raise ValueError("run.delay_between_requests_seconds cannot be negative")

    records = read_manifest_jsonl(input_path)
    input_manifest_count = len(records)
    if effective_limit is not None:
        records = records[:effective_limit]

    network = _mapping(config.get("network", {}), "network")
    active_fetcher = fetcher or HttpFetcher(
        timeout_seconds=float(network.get("timeout_seconds", 15)),
        retries=int(network.get("retries", 1)),
        backoff_seconds=float(network.get("backoff_seconds", 0.5)),
        max_response_bytes=int(network.get("max_response_bytes", 16 * 1024 * 1024)),
        user_agent=str(
            network.get(
                "user_agent",
                "iiif-manifest-validator/0.1 (+EPFL DHLAB academic research)",
            )
        ),
    )

    raw_directory.mkdir(parents=True, exist_ok=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    log_directory.mkdir(parents=True, exist_ok=True)
    local_run_time = _local_run_time(run_time)
    run_at = local_run_time.isoformat(timespec="seconds")

    valid_rows: list[dict[str, Any]] = []
    manual_rows: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    unavailable_rows: list[dict[str, Any]] = []
    resource_rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    cache_hit_count = 0
    network_fetch_count = 0
    normalized_manifest_count = 0
    source_status_counts: Counter[str] = Counter()

    for index, record in enumerate(records):
        raw_path = raw_directory / f"{record.manifest_id}.json"
        metadata_path = raw_directory / f"{record.manifest_id}.meta.json"
        cached = raw_path.exists() and not effective_force

        if cached:
            body = raw_path.read_bytes()
            fetch_metadata = _cached_fetch_metadata(
                record, metadata_path, body, run_at
            )
            cache_hit_count += 1
        else:
            try:
                response = active_fetcher.fetch(record.manifest_url)
            except FetchError as exc:
                row = _failure_record(
                    record,
                    stage="fetch",
                    failure_type=exc.error_type,
                    message=str(exc),
                    run_at=run_at,
                    status_code=exc.status_code,
                    attempt_count=exc.attempt_count,
                )
                unavailable_rows.append(row)
                status_counts["unavailable"] += 1
                if delay_seconds and index < len(records) - 1:
                    time.sleep(delay_seconds)
                continue
            body = response.body
            fetch_metadata = _network_fetch_metadata(response, run_at)
            network_fetch_count += 1
            if delay_seconds and index < len(records) - 1:
                time.sleep(delay_seconds)

        digest = sha256(body).hexdigest()
        fetch_metadata["sha256"] = digest
        fetch_metadata["response_bytes"] = len(body)

        try:
            document = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            row = _failure_record(
                record,
                stage="parse",
                failure_type="invalid_json",
                message=str(exc),
                run_at=run_at,
                fetch_metadata=fetch_metadata,
            )
            invalid_rows.append(row)
            status_counts["invalid"] += 1
            continue

        if not cached:
            write_raw_response(raw_path, body)
            _write_cache_metadata(metadata_path, fetch_metadata)
        fetch_metadata["raw_manifest_path"] = _display_path(
            raw_path, base_directory
        )

        source_validation = validate_manifest(document)
        source_status_counts[source_validation.status] += 1
        patches = []
        effective_document = document
        if infer_transport_id:
            effective_document, patches = infer_missing_manifest_id(
                document, str(fetch_metadata.get("final_url") or record.manifest_url)
            )
        validation = validate_manifest(effective_document) if patches else source_validation
        output_record = _validated_record(
            record, fetch_metadata, validation, run_at
        )
        if patches:
            normalized_manifest_count += 1
            normalized_path = raw_directory / f"{record.manifest_id}.normalized.json"
            write_raw_response(normalized_path, (json.dumps(effective_document, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            output_record["source_structural_validation"] = source_validation.summary_dict()
            output_record["structural_normalization"] = {
                "policy": "transport-id-inference-1.0", "patches": patches,
                "normalized_manifest_path": _display_path(normalized_path, base_directory),
                "raw_source_preserved": True,
            }
        status_counts[validation.status] += 1

        if validation.status == "valid":
            valid_rows.append(output_record)
            resource_rows.extend(_resource_rows(record, validation))
        elif validation.status == "manual_review":
            manual_rows.append(output_record)
        else:
            invalid_rows.append(output_record)

    validated_manifests_jsonl = output_directory / "validated_manifests.jsonl"
    resource_inventory_jsonl = output_directory / "manifest_resource_inventory.jsonl"
    resource_inventory_csv = output_directory / "manifest_resource_inventory.csv"
    invalid_manifests_jsonl = output_directory / "invalid_manifests.jsonl"
    manual_review_jsonl = output_directory / "manual_review.jsonl"
    unavailable_manifests_jsonl = output_directory / "unavailable_manifests.jsonl"
    log_txt = log_directory / (
        f"Module4_{local_run_time.strftime('%Y-%m-%d_%H-%M-%S')}_log.txt"
    )

    write_jsonl(validated_manifests_jsonl, valid_rows)
    write_jsonl(resource_inventory_jsonl, resource_rows)
    write_resource_csv(resource_inventory_csv, resource_rows)
    write_jsonl(invalid_manifests_jsonl, invalid_rows)
    write_jsonl(manual_review_jsonl, manual_rows)
    write_jsonl(unavailable_manifests_jsonl, unavailable_rows)

    canvas_count = sum(
        int(row["structural_validation"]["canvas_count"]) for row in valid_rows
    )
    image_body_count = sum(
        int(row["structural_validation"]["image_body_count"]) for row in valid_rows
    )
    image_service_count = sum(
        int(row["structural_validation"]["image_service_count"]) for row in valid_rows
    )

    write_text(
        log_txt,
        _format_log(
            run_at=run_at,
            input_path=input_path,
            input_manifest_count=input_manifest_count,
            processed_manifest_count=len(records),
            effective_limit=effective_limit,
            force_refresh=effective_force,
            network_fetch_count=network_fetch_count,
            cache_hit_count=cache_hit_count,
            normalized_manifest_count=normalized_manifest_count,
            source_status_counts=source_status_counts,
            status_counts=status_counts,
            canvas_count=canvas_count,
            image_body_count=image_body_count,
            image_service_count=image_service_count,
            validated_manifests_jsonl=validated_manifests_jsonl,
            resource_inventory_jsonl=resource_inventory_jsonl,
            resource_inventory_csv=resource_inventory_csv,
            invalid_manifests_jsonl=invalid_manifests_jsonl,
            manual_review_jsonl=manual_review_jsonl,
            unavailable_manifests_jsonl=unavailable_manifests_jsonl,
        ),
    )

    return PipelineResult(
        input_manifest_count=input_manifest_count,
        processed_manifest_count=len(records),
        status_counts=dict(sorted(status_counts.items())),
        valid_manifest_count=len(valid_rows),
        canvas_count=canvas_count,
        image_body_count=image_body_count,
        image_service_count=image_service_count,
        cache_hit_count=cache_hit_count,
        normalized_manifest_count=normalized_manifest_count,
        validated_manifests_jsonl=validated_manifests_jsonl,
        resource_inventory_jsonl=resource_inventory_jsonl,
        resource_inventory_csv=resource_inventory_csv,
        invalid_manifests_jsonl=invalid_manifests_jsonl,
        manual_review_jsonl=manual_review_jsonl,
        unavailable_manifests_jsonl=unavailable_manifests_jsonl,
        log_txt=log_txt,
    )


def _validated_record(
    record: ManifestInputRecord,
    fetch_metadata: Mapping[str, Any],
    validation: ValidationResult,
    run_at: str,
) -> dict[str, Any]:
    output = record.to_dict()
    output["module_4_schema_version"] = MODULE_4_SCHEMA_VERSION
    output["processed_at"] = run_at
    output["raw_manifest"] = dict(fetch_metadata)
    output["structural_validation"] = validation.summary_dict()
    return output


def _resource_rows(
    record: ManifestInputRecord, validation: ValidationResult
) -> list[dict[str, Any]]:
    provider_names = [
        str(item.get("provider_name", ""))
        for item in record.data.get("providers", [])
        if isinstance(item, Mapping) and item.get("provider_name")
    ]
    rows: list[dict[str, Any]] = []
    for resource in validation.canvas_resources:
        rows.append(
            {
                "manifest_id": record.manifest_id,
                "manifest_url": record.manifest_url,
                "provider_names": provider_names,
                "presentation_version": validation.presentation_version,
                "rights_values": list(validation.rights_values),
                **resource.to_dict(),
                "module_4_schema_version": MODULE_4_SCHEMA_VERSION,
            }
        )
    return rows


def _failure_record(
    record: ManifestInputRecord,
    *,
    stage: str,
    failure_type: str,
    message: str,
    run_at: str,
    status_code: int | None = None,
    attempt_count: int | None = None,
    fetch_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    output = record.to_dict()
    output["module_4_schema_version"] = MODULE_4_SCHEMA_VERSION
    output["processed_at"] = run_at
    if fetch_metadata is not None:
        output["raw_manifest"] = dict(fetch_metadata)
    output["failure"] = {
        "stage": stage,
        "failure_type": failure_type,
        "message": message,
        "status_code": status_code,
        "attempt_count": attempt_count,
    }
    return output


def _network_fetch_metadata(
    response: FetchedResponse, run_at: str
) -> dict[str, Any]:
    return {
        "fetch_source": "network",
        "requested_url": response.requested_url,
        "final_url": response.final_url,
        "status_code": response.status_code,
        "content_type": response.content_type,
        "response_time_ms": response.response_time_ms,
        "attempt_count": response.attempt_count,
        "fetched_at": run_at,
    }


def _cached_fetch_metadata(
    record: ManifestInputRecord,
    metadata_path: Path,
    body: bytes,
    run_at: str,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if metadata_path.exists():
        try:
            value = json.loads(metadata_path.read_text(encoding="utf-8"))
            if isinstance(value, Mapping):
                metadata.update(value)
        except (OSError, json.JSONDecodeError):
            pass
    metadata.update(
        {
            "fetch_source": "cache",
            "requested_url": metadata.get("requested_url", record.manifest_url),
            "final_url": metadata.get("final_url", record.manifest_url),
            "status_code": metadata.get("status_code"),
            "content_type": metadata.get("content_type", "application/json"),
            "response_time_ms": 0,
            "attempt_count": 0,
            "fetched_at": metadata.get("fetched_at", run_at),
            "sha256": sha256(body).hexdigest(),
            "response_bytes": len(body),
        }
    )
    return metadata


def _write_cache_metadata(path: Path, metadata: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(dict(metadata), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _format_log(
    *,
    run_at: str,
    input_path: Path,
    input_manifest_count: int,
    processed_manifest_count: int,
    effective_limit: int | None,
    force_refresh: bool,
    network_fetch_count: int,
    cache_hit_count: int,
    normalized_manifest_count: int,
    source_status_counts: Mapping[str, int],
    status_counts: Mapping[str, int],
    canvas_count: int,
    image_body_count: int,
    image_service_count: int,
    validated_manifests_jsonl: Path,
    resource_inventory_jsonl: Path,
    resource_inventory_csv: Path,
    invalid_manifests_jsonl: Path,
    manual_review_jsonl: Path,
    unavailable_manifests_jsonl: Path,
) -> str:
    status_lines = [
        f"- {name}: {count}" for name, count in sorted(status_counts.items())
    ] or ["- (no records processed)"]
    return "\n".join(
        [
            "Module 4 Run Log",
            "================",
            f"Run time (computer local time): {run_at}",
            f"Input: {input_path}",
            f"Input Manifest URLs: {input_manifest_count}",
            f"Run limit: {effective_limit if effective_limit is not None else 'none'}",
            f"Processed records: {processed_manifest_count}",
            f"Force refresh: {force_refresh}",
            f"Network fetches: {network_fetch_count}",
            f"Cache hits: {cache_hit_count}",
            f"Strict source structural statuses: {json.dumps(dict(source_status_counts), sort_keys=True)}",
            f"Manifests normalized with explicit ID-inference patches: {normalized_manifest_count}",
            f"Validated Canvas count: {canvas_count}",
            f"Validated image-body count: {image_body_count}",
            f"Validated Image Service count: {image_service_count}",
            "",
            "Record results:",
            *status_lines,
            "",
            "Outputs:",
            f"- Validated Manifests for Module 5: {validated_manifests_jsonl}",
            f"- Page/image inventory JSONL: {resource_inventory_jsonl}",
            f"- Page/image inventory CSV: {resource_inventory_csv}",
            f"- Structurally invalid records: {invalid_manifests_jsonl}",
            f"- Manual review records: {manual_review_jsonl}",
            f"- Unavailable records: {unavailable_manifests_jsonl}",
        ]
    )


def _read_config(path: Path) -> Mapping[str, Any]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read configuration {path}: {exc}") from exc
    return _mapping(value, "configuration")


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _resolve_path(value: str, base_directory: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = base_directory / path
    return path.resolve()


def _display_path(path: Path, base_directory: Path) -> str:
    try:
        return path.resolve().relative_to(base_directory.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _optional_positive_int(value: Any, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a positive integer or null")
    result = int(value)
    if result < 1:
        raise ValueError(f"{name} must be a positive integer or null")
    return result


def _local_run_time(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now().astimezone()
    if value.tzinfo is None:
        return value.astimezone()
    return value
