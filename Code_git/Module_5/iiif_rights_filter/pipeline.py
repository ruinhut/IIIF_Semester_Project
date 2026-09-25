"""Configuration-driven Module 5 rights assessment and resource filtering."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Optional

from .extractor import extract_rights_evidence
from .models import (
    MODULE_5_SCHEMA_VERSION,
    Module4ManifestRecord,
    RightsAssessment,
    RightsPolicy,
)
from .policy import assess_rights, assessment_error
from .store import (
    read_jsonl_objects,
    read_validated_manifests,
    write_jsonl,
    write_resource_csv,
    write_summary_csv,
    write_text,
)


@dataclass(frozen=True)
class PipelineResult:
    input_manifest_count: int
    processed_manifest_count: int
    decision_counts: Mapping[str, int]
    category_counts: Mapping[str, int]
    allowed_resource_count: int
    rights_assessed_jsonl: Path
    allowed_manifests_jsonl: Path
    excluded_manifests_jsonl: Path
    allowed_resource_inventory_jsonl: Path
    allowed_resource_inventory_csv: Path
    rights_summary_csv: Path
    log_txt: Path


def run_pipeline(
    config_path: Path,
    *,
    limit: int | None = None,
    run_time: datetime | None = None,
) -> PipelineResult:
    """Assess Manifest rights, apply policy, and filter downstream resources."""

    config_path = config_path.resolve()
    config = _read_json_mapping(config_path, "configuration")
    base_directory = config_path.parent
    validated_path = _resolve_path(
        str(config.get("validated_manifests_jsonl", "../Module_4/data/output/validated_manifests.jsonl")),
        base_directory,
    )
    inventory_path = _resolve_path(
        str(config.get("resource_inventory_jsonl", "../Module_4/data/output/manifest_resource_inventory.jsonl")),
        base_directory,
    )
    module_4_directory = _resolve_path(
        str(config.get("module_4_directory", "../Module_4")), base_directory
    )
    policy_path = _resolve_path(
        str(config.get("policy_file", "policies/automatic-2026-09-25.json")),
        base_directory,
    )
    output_directory = _resolve_path(
        str(config.get("output_directory", "data/output")), base_directory
    )
    log_directory = _resolve_path(
        str(config.get("log_directory", "data/log")), base_directory
    )

    run_config = _mapping(config.get("run", {}), "run")
    configured_limit = _optional_positive_int(run_config.get("max_records"), "run.max_records")
    effective_limit = (
        _optional_positive_int(limit, "limit") if limit is not None else configured_limit
    )
    verify_sha256 = bool(run_config.get("verify_raw_sha256", True))
    policy = RightsPolicy.from_mapping(_read_json_mapping(policy_path, "policy"))

    records = read_validated_manifests(validated_path)
    input_manifest_count = len(records)
    if effective_limit is not None:
        records = records[:effective_limit]

    output_directory.mkdir(parents=True, exist_ok=True)
    log_directory.mkdir(parents=True, exist_ok=True)
    local_run_time = _local_run_time(run_time)
    assessed_at = local_run_time.isoformat(timespec="seconds")

    assessed_rows: list[dict[str, Any]] = []
    by_decision: dict[str, list[dict[str, Any]]] = {
        "allow": [],
        "exclude": [],
    }
    decision_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()

    for record in records:
        assessment = _assess_record(
            record,
            module_4_directory=module_4_directory,
            verify_sha256=verify_sha256,
            policy=policy,
            assessed_at=assessed_at,
        )
        output = record.to_dict()
        output["module_5_schema_version"] = MODULE_5_SCHEMA_VERSION
        output["rights_assessment"] = assessment.to_dict()
        assessed_rows.append(output)
        by_decision[assessment.decision].append(output)
        decision_counts[assessment.decision] += 1
        category_counts[assessment.category] += 1

    selected_ids = {record.manifest_id for record in records}
    allowed_ids = {
        str(row["manifest_id"]) for row in by_decision["allow"]
    }
    assessment_by_id = {
        str(row["manifest_id"]): row["rights_assessment"] for row in assessed_rows
    }
    inventory = read_jsonl_objects(inventory_path)
    relevant_inventory = [
        row for row in inventory if str(row.get("manifest_id", "")) in selected_ids
    ]
    allowed_resources = [
        _enrich_resource(row, assessment_by_id[str(row["manifest_id"])])
        for row in relevant_inventory
        if str(row.get("manifest_id", "")) in allowed_ids
    ]

    rights_assessed_jsonl = output_directory / "rights_assessed_manifests.jsonl"
    allowed_manifests_jsonl = output_directory / "allowed_manifests.jsonl"
    excluded_manifests_jsonl = output_directory / "excluded_manifests.jsonl"
    allowed_resource_inventory_jsonl = output_directory / "allowed_resource_inventory.jsonl"
    allowed_resource_inventory_csv = output_directory / "allowed_resource_inventory.csv"
    rights_summary_csv = output_directory / "rights_summary.csv"
    log_txt = log_directory / f"Module5_{local_run_time.strftime('%Y-%m-%d_%H-%M-%S')}_log.txt"

    # Remove outputs from the earlier manual-review prototype so stale files
    # cannot be mistaken for current pipeline products.
    for legacy_name in ("denied_manifests.jsonl", "manual_review.jsonl"):
        legacy_path = output_directory / legacy_name
        if legacy_path.exists():
            legacy_path.unlink()

    write_jsonl(rights_assessed_jsonl, assessed_rows)
    write_jsonl(allowed_manifests_jsonl, by_decision["allow"])
    write_jsonl(excluded_manifests_jsonl, by_decision["exclude"])
    write_jsonl(allowed_resource_inventory_jsonl, allowed_resources)
    write_resource_csv(allowed_resource_inventory_csv, allowed_resources)
    write_summary_csv(rights_summary_csv, assessed_rows)
    write_text(
        log_txt,
        _format_log(
            assessed_at=assessed_at,
            validated_path=validated_path,
            inventory_path=inventory_path,
            policy_path=policy_path,
            policy=policy,
            input_manifest_count=input_manifest_count,
            processed_manifest_count=len(records),
            effective_limit=effective_limit,
            verify_sha256=verify_sha256,
            decision_counts=decision_counts,
            category_counts=category_counts,
            relevant_resource_count=len(relevant_inventory),
            allowed_resource_count=len(allowed_resources),
            rights_assessed_jsonl=rights_assessed_jsonl,
            allowed_manifests_jsonl=allowed_manifests_jsonl,
            excluded_manifests_jsonl=excluded_manifests_jsonl,
            allowed_resource_inventory_jsonl=allowed_resource_inventory_jsonl,
            allowed_resource_inventory_csv=allowed_resource_inventory_csv,
            rights_summary_csv=rights_summary_csv,
        ),
    )

    return PipelineResult(
        input_manifest_count=input_manifest_count,
        processed_manifest_count=len(records),
        decision_counts=dict(sorted(decision_counts.items())),
        category_counts=dict(sorted(category_counts.items())),
        allowed_resource_count=len(allowed_resources),
        rights_assessed_jsonl=rights_assessed_jsonl,
        allowed_manifests_jsonl=allowed_manifests_jsonl,
        excluded_manifests_jsonl=excluded_manifests_jsonl,
        allowed_resource_inventory_jsonl=allowed_resource_inventory_jsonl,
        allowed_resource_inventory_csv=allowed_resource_inventory_csv,
        rights_summary_csv=rights_summary_csv,
        log_txt=log_txt,
    )


def _assess_record(
    record: Module4ManifestRecord,
    *,
    module_4_directory: Path,
    verify_sha256: bool,
    policy: RightsPolicy,
    assessed_at: str,
) -> RightsAssessment:
    raw_path = Path(record.raw_manifest_path)
    if not raw_path.is_absolute():
        raw_path = module_4_directory / raw_path
    try:
        body = raw_path.read_bytes()
    except OSError:
        return assessment_error(policy, assessed_at, "raw_manifest_unavailable")

    if verify_sha256:
        if not record.expected_sha256:
            return assessment_error(policy, assessed_at, "raw_manifest_checksum_missing")
        if sha256(body).hexdigest().lower() != record.expected_sha256:
            return assessment_error(policy, assessed_at, "raw_manifest_checksum_mismatch")
    try:
        document = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return assessment_error(policy, assessed_at, "raw_manifest_invalid_json")
    try:
        extracted = extract_rights_evidence(document)
    except ValueError:
        return assessment_error(policy, assessed_at, "raw_manifest_not_object")
    return assess_rights(extracted, policy, assessed_at)


def _enrich_resource(
    resource: Mapping[str, Any], assessment: Mapping[str, Any]
) -> dict[str, Any]:
    output = dict(resource)
    output.pop("rights_values", None)
    output["rights_category"] = assessment["category"]
    output["rights_decision"] = assessment["decision"]
    output["rights_policy_version"] = assessment["policy_version"]
    output["module_5_schema_version"] = MODULE_5_SCHEMA_VERSION
    return output


def _format_log(
    *,
    assessed_at: str,
    validated_path: Path,
    inventory_path: Path,
    policy_path: Path,
    policy: RightsPolicy,
    input_manifest_count: int,
    processed_manifest_count: int,
    effective_limit: int | None,
    verify_sha256: bool,
    decision_counts: Mapping[str, int],
    category_counts: Mapping[str, int],
    relevant_resource_count: int,
    allowed_resource_count: int,
    rights_assessed_jsonl: Path,
    allowed_manifests_jsonl: Path,
    excluded_manifests_jsonl: Path,
    allowed_resource_inventory_jsonl: Path,
    allowed_resource_inventory_csv: Path,
    rights_summary_csv: Path,
) -> str:
    decision_lines = [f"- {key}: {value}" for key, value in sorted(decision_counts.items())] or ["- (none)"]
    category_lines = [f"- {key}: {value}" for key, value in sorted(category_counts.items())] or ["- (none)"]
    return "\n".join(
        [
            "Module 5 Run Log",
            "================",
            f"Run time (computer local time): {assessed_at}",
            f"Validated Manifest input: {validated_path}",
            f"Resource inventory input: {inventory_path}",
            f"Policy file: {policy_path}",
            f"Policy version: {policy.policy_version}",
            f"Input valid Manifests: {input_manifest_count}",
            f"Run limit: {effective_limit if effective_limit is not None else 'none'}",
            f"Processed Manifests: {processed_manifest_count}",
            f"Raw SHA-256 verification: {verify_sha256}",
            f"Relevant input resource rows: {relevant_resource_count}",
            f"Allowed output resource rows: {allowed_resource_count}",
            "",
            "Policy decisions:",
            *decision_lines,
            "",
            "Rights categories:",
            *category_lines,
            "",
            "Outputs:",
            f"- All assessments: {rights_assessed_jsonl}",
            f"- Allowed Manifests: {allowed_manifests_jsonl}",
            f"- Automatically excluded Manifests: {excluded_manifests_jsonl}",
            f"- Allowed resources JSONL: {allowed_resource_inventory_jsonl}",
            f"- Allowed resources CSV: {allowed_resource_inventory_csv}",
            f"- Rights summary CSV: {rights_summary_csv}",
        ]
    )


def _read_json_mapping(path: Path, name: str) -> Mapping[str, Any]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read {name} {path}: {exc}") from exc
    return _mapping(value, name)


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _resolve_path(value: str, base_directory: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = base_directory / path
    return path.resolve()


def _optional_positive_int(value: Any, name: str) -> Optional[int]:
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
