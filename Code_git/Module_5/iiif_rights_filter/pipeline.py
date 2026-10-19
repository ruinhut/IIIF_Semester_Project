"""Configuration-driven Module 5 rights assessment and research handoff."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
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
    research_resource_count: int
    reuse_eligible_resource_count: int
    research_manifests_jsonl: Path
    reuse_eligible_manifests_jsonl: Path
    research_only_manifests_jsonl: Path
    research_resource_inventory_jsonl: Path
    research_resource_inventory_csv: Path
    reuse_eligible_resource_inventory_jsonl: Path
    reuse_eligible_resource_inventory_csv: Path
    rights_summary_csv: Path
    log_txt: Path


def run_pipeline(
    config_path: Path,
    *,
    limit: int | None = None,
    run_time: datetime | None = None,
) -> PipelineResult:
    """Assess rights and retain every processed record for research downstream."""

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
        str(config.get("policy_file", "policies/automatic-2026-09-29.json")),
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
    policy = RightsPolicy.from_mapping(_read_json_mapping(policy_path, "policy"))

    records = read_validated_manifests(validated_path)
    input_manifest_count = len(records)
    if effective_limit is not None:
        records = records[:effective_limit]

    output_directory.mkdir(parents=True, exist_ok=True)
    log_directory.mkdir(parents=True, exist_ok=True)
    local_run_time = _local_run_time(run_time)
    assessed_at = local_run_time.isoformat(timespec="seconds")

    research_manifests: list[dict[str, Any]] = []
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
            policy=policy,
            assessed_at=assessed_at,
        )
        output = record.to_dict()
        output["module_5_schema_version"] = MODULE_5_SCHEMA_VERSION
        output["rights_assessment"] = assessment.to_dict()
        research_manifests.append(output)
        by_decision[assessment.decision].append(output)
        decision_counts[assessment.decision] += 1
        category_counts[assessment.category] += 1

    selected_ids = {record.manifest_id for record in records}
    reuse_eligible_ids = {
        str(row["manifest_id"]) for row in by_decision["allow"]
    }
    assessment_by_id = {
        str(row["manifest_id"]): row["rights_assessment"]
        for row in research_manifests
    }
    inventory = read_jsonl_objects(inventory_path)
    relevant_inventory = [
        row for row in inventory if str(row.get("manifest_id", "")) in selected_ids
    ]
    research_resources = [
        _enrich_resource(row, assessment_by_id[str(row["manifest_id"])])
        for row in relevant_inventory
    ]
    reuse_eligible_resources = [
        row
        for row in research_resources
        if str(row.get("manifest_id", "")) in reuse_eligible_ids
    ]

    research_manifests_jsonl = output_directory / "research_manifests.jsonl"
    reuse_eligible_manifests_jsonl = output_directory / "reuse_eligible_manifests.jsonl"
    research_only_manifests_jsonl = output_directory / "research_only_manifests.jsonl"
    research_resource_inventory_jsonl = output_directory / "research_resource_inventory.jsonl"
    research_resource_inventory_csv = output_directory / "research_resource_inventory.csv"
    reuse_eligible_resource_inventory_jsonl = (
        output_directory / "reuse_eligible_resource_inventory.jsonl"
    )
    reuse_eligible_resource_inventory_csv = (
        output_directory / "reuse_eligible_resource_inventory.csv"
    )
    rights_summary_csv = output_directory / "rights_summary.csv"
    log_txt = log_directory / f"Module5_{local_run_time.strftime('%Y-%m-%d_%H-%M-%S')}_log.txt"

    # Remove obsolete outputs so old binary-filter files are not mistaken for
    # the current research-retention handoff.
    for legacy_name in (
        "rights_assessed_manifests.jsonl",
        "allowed_manifests.jsonl",
        "excluded_manifests.jsonl",
        "allowed_resource_inventory.jsonl",
        "allowed_resource_inventory.csv",
        "denied_manifests.jsonl",
        "manual_review.jsonl",
    ):
        legacy_path = output_directory / legacy_name
        if legacy_path.exists():
            legacy_path.unlink()

    write_jsonl(research_manifests_jsonl, research_manifests)
    write_jsonl(reuse_eligible_manifests_jsonl, by_decision["allow"])
    write_jsonl(research_only_manifests_jsonl, by_decision["exclude"])
    write_jsonl(research_resource_inventory_jsonl, research_resources)
    write_resource_csv(research_resource_inventory_csv, research_resources)
    write_jsonl(reuse_eligible_resource_inventory_jsonl, reuse_eligible_resources)
    write_resource_csv(reuse_eligible_resource_inventory_csv, reuse_eligible_resources)
    write_summary_csv(rights_summary_csv, research_manifests)
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
            decision_counts=decision_counts,
            category_counts=category_counts,
            research_resource_count=len(research_resources),
            reuse_eligible_resource_count=len(reuse_eligible_resources),
            research_manifests_jsonl=research_manifests_jsonl,
            reuse_eligible_manifests_jsonl=reuse_eligible_manifests_jsonl,
            research_only_manifests_jsonl=research_only_manifests_jsonl,
            research_resource_inventory_jsonl=research_resource_inventory_jsonl,
            research_resource_inventory_csv=research_resource_inventory_csv,
            reuse_eligible_resource_inventory_jsonl=reuse_eligible_resource_inventory_jsonl,
            reuse_eligible_resource_inventory_csv=reuse_eligible_resource_inventory_csv,
            rights_summary_csv=rights_summary_csv,
        ),
    )

    return PipelineResult(
        input_manifest_count=input_manifest_count,
        processed_manifest_count=len(records),
        decision_counts=dict(sorted(decision_counts.items())),
        category_counts=dict(sorted(category_counts.items())),
        research_resource_count=len(research_resources),
        reuse_eligible_resource_count=len(reuse_eligible_resources),
        research_manifests_jsonl=research_manifests_jsonl,
        reuse_eligible_manifests_jsonl=reuse_eligible_manifests_jsonl,
        research_only_manifests_jsonl=research_only_manifests_jsonl,
        research_resource_inventory_jsonl=research_resource_inventory_jsonl,
        research_resource_inventory_csv=research_resource_inventory_csv,
        reuse_eligible_resource_inventory_jsonl=reuse_eligible_resource_inventory_jsonl,
        reuse_eligible_resource_inventory_csv=reuse_eligible_resource_inventory_csv,
        rights_summary_csv=rights_summary_csv,
        log_txt=log_txt,
    )


def _assess_record(
    record: Module4ManifestRecord,
    *,
    module_4_directory: Path,
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
    usage = assessment.get("usage_permissions", {})
    output = dict(resource)
    output.pop("rights_values", None)
    output["rights_category"] = assessment["category"]
    output["rights_decision"] = assessment["decision"]
    output["rights_decision_scope"] = assessment["decision_scope"]
    output["rights_policy_version"] = assessment["policy_version"]
    output["research_status"] = assessment["research_status"]
    output["retain_url_and_metadata"] = bool(usage.get("retain_url_and_metadata"))
    output["academic_analysis_allowed"] = bool(usage.get("academic_analysis"))
    output["public_distribution_allowed"] = bool(usage.get("public_distribution"))
    output["commercial_use_allowed"] = bool(usage.get("commercial_use"))
    output["public_reuse_eligible"] = bool(assessment["public_reuse_eligible"])
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
    decision_counts: Mapping[str, int],
    category_counts: Mapping[str, int],
    research_resource_count: int,
    reuse_eligible_resource_count: int,
    research_manifests_jsonl: Path,
    reuse_eligible_manifests_jsonl: Path,
    research_only_manifests_jsonl: Path,
    research_resource_inventory_jsonl: Path,
    research_resource_inventory_csv: Path,
    reuse_eligible_resource_inventory_jsonl: Path,
    reuse_eligible_resource_inventory_csv: Path,
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
            "Decision scope: public reuse only",
            "Research retention: all processed records",
            f"Input valid Manifests: {input_manifest_count}",
            f"Run limit: {effective_limit if effective_limit is not None else 'none'}",
            f"Processed Manifests: {processed_manifest_count}",
            f"Research-retained Manifests: {processed_manifest_count}",
            f"Public-reuse-eligible Manifests: {decision_counts.get('allow', 0)}",
            f"Research-only Manifests: {decision_counts.get('exclude', 0)}",
            f"Research resource rows: {research_resource_count}",
            f"Public-reuse-eligible resource rows: {reuse_eligible_resource_count}",
            "",
            "Public-reuse decisions:",
            *decision_lines,
            "",
            "Rights categories:",
            *category_lines,
            "",
            "Outputs:",
            f"- Research Manifests: {research_manifests_jsonl}",
            f"- Public-reuse-eligible Manifests: {reuse_eligible_manifests_jsonl}",
            f"- Research-only Manifests: {research_only_manifests_jsonl}",
            f"- Research resources JSONL: {research_resource_inventory_jsonl}",
            f"- Research resources CSV: {research_resource_inventory_csv}",
            f"- Public-reuse resources JSONL: {reuse_eligible_resource_inventory_jsonl}",
            f"- Public-reuse resources CSV: {reuse_eligible_resource_inventory_csv}",
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
