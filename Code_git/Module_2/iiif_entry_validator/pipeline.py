"""Orchestrate the complete Module 2 entry-point checking workflow."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any, Mapping, Protocol, Sequence

from .checker import EndpointChecker
from .models import CHECK_RESULTS, CheckedProviderRecord, EndpointCheck
from .store import read_provider_jsonl, write_checked_jsonl, write_csv, write_text


DISCOVERY_READY_RESULTS = {"reachable_json"}
MANUAL_REVIEW_RESULTS = {
    "reachable_non_json",
    "invalid_json",
    "response_too_large",
    "restricted",
}
UNAVAILABLE_RESULTS = {"temporary_failure", "unreachable"}


class CheckerProtocol(Protocol):
    def check(self, url: str, *, checked_at: str) -> EndpointCheck:
        """Return an endpoint check for one URL."""


@dataclass(frozen=True)
class PipelineResult:
    input_count: int
    checked_count: int
    result_counts: Mapping[str, int]
    checked_jsonl: Path
    discovery_ready_jsonl: Path
    manual_review_jsonl: Path
    unavailable_jsonl: Path
    checked_csv: Path
    log_txt: Path


def run_pipeline(
    config_path: Path,
    *,
    limit: int | None = None,
    run_time: datetime | None = None,
    checker: CheckerProtocol | None = None,
) -> PipelineResult:
    """Check Module 1 entry points and write every documented Module 2 output."""

    config_path = config_path.resolve()
    config = _read_config(config_path)
    base_directory = config_path.parent
    input_path = _resolve_path(str(config.get("input_jsonl", "")), base_directory)
    if not str(config.get("input_jsonl", "")).strip():
        raise ValueError("input_jsonl must be configured")

    providers = read_provider_jsonl(input_path)
    original_input_count = len(providers)
    run_config = _mapping(config.get("run", {}), "run")
    configured_limit = _optional_positive_int(run_config.get("max_records"), "max_records")
    effective_limit = limit if limit is not None else configured_limit
    if effective_limit is not None:
        if effective_limit < 1:
            raise ValueError("limit must be positive")
        providers = providers[:effective_limit]

    network = _mapping(config.get("network", {}), "network")
    active_checker = checker or EndpointChecker(
        timeout_seconds=float(network.get("timeout_seconds", 10)),
        retries=int(network.get("retries", 1)),
        backoff_seconds=float(network.get("backoff_seconds", 0.5)),
        max_redirects=int(network.get("max_redirects", 10)),
        max_response_bytes=int(network.get("max_response_bytes", 2 * 1024 * 1024)),
        user_agent=str(
            network.get(
                "user_agent",
                "iiif-entry-validator/0.1 (+EPFL DHLAB academic research)",
            )
        ),
    )
    delay = float(run_config.get("delay_between_requests_seconds", 0.1))
    if delay < 0:
        raise ValueError("delay_between_requests_seconds must be non-negative")

    local_run_time = _local_run_time(run_time)
    checked_at = local_run_time.isoformat(timespec="seconds")
    checked_records: list[CheckedProviderRecord] = []
    for index, provider in enumerate(providers):
        endpoint_check = active_checker.check(provider.discovery_endpoint, checked_at=checked_at)
        checked_records.append(CheckedProviderRecord(provider, endpoint_check))
        if delay and index + 1 < len(providers):
            time.sleep(delay)

    discovery_ready = _records_with_results(checked_records, DISCOVERY_READY_RESULTS)
    manual_review = _records_with_results(checked_records, MANUAL_REVIEW_RESULTS)
    unavailable = _records_with_results(checked_records, UNAVAILABLE_RESULTS)
    observed_counts = Counter(record.endpoint_check.check_result for record in checked_records)
    result_counts = {name: observed_counts.get(name, 0) for name in sorted(CHECK_RESULTS)}

    output_directory = _resolve_path(
        str(config.get("output_directory", "data/output")), base_directory
    )
    log_directory = _resolve_path(str(config.get("log_directory", "data/log")), base_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    log_directory.mkdir(parents=True, exist_ok=True)

    checked_jsonl = output_directory / "checked_entry_points.jsonl"
    discovery_ready_jsonl = output_directory / "discovery_ready.jsonl"
    manual_review_jsonl = output_directory / "manual_review.jsonl"
    unavailable_jsonl = output_directory / "unavailable_entry_points.jsonl"
    checked_csv = output_directory / "checked_entry_points.csv"
    log_txt = log_directory / f"Module2_{local_run_time.strftime('%Y-%m-%d_%H-%M-%S')}_log.txt"

    write_checked_jsonl(checked_jsonl, checked_records)
    write_checked_jsonl(discovery_ready_jsonl, discovery_ready)
    write_checked_jsonl(manual_review_jsonl, manual_review)
    write_checked_jsonl(unavailable_jsonl, unavailable)
    write_csv(checked_csv, checked_records)
    write_text(
        log_txt,
        _format_run_log(
            run_at=checked_at,
            input_path=input_path,
            original_input_count=original_input_count,
            effective_limit=effective_limit,
            checked_count=len(checked_records),
            result_counts=result_counts,
            checked_jsonl=checked_jsonl,
            discovery_ready_jsonl=discovery_ready_jsonl,
            manual_review_jsonl=manual_review_jsonl,
            unavailable_jsonl=unavailable_jsonl,
            checked_csv=checked_csv,
        ),
    )

    return PipelineResult(
        input_count=original_input_count,
        checked_count=len(checked_records),
        result_counts=result_counts,
        checked_jsonl=checked_jsonl,
        discovery_ready_jsonl=discovery_ready_jsonl,
        manual_review_jsonl=manual_review_jsonl,
        unavailable_jsonl=unavailable_jsonl,
        checked_csv=checked_csv,
        log_txt=log_txt,
    )


def _records_with_results(
    records: Sequence[CheckedProviderRecord], results: set[str]
) -> list[CheckedProviderRecord]:
    return [record for record in records if record.endpoint_check.check_result in results]


def _format_run_log(
    *,
    run_at: str,
    input_path: Path,
    original_input_count: int,
    effective_limit: int | None,
    checked_count: int,
    result_counts: Mapping[str, int],
    checked_jsonl: Path,
    discovery_ready_jsonl: Path,
    manual_review_jsonl: Path,
    unavailable_jsonl: Path,
    checked_csv: Path,
) -> str:
    result_lines = [
        f"- {name}: {count}" for name, count in sorted(result_counts.items())
    ] or ["- (no records checked)"]
    lines = [
        "Module 2 Run Log",
        "================",
        f"Run time (computer local time): {run_at}",
        f"Input: {input_path}",
        f"Input records: {original_input_count}",
        f"Run limit: {effective_limit if effective_limit is not None else 'none'}",
        f"Checked records: {checked_count}",
        "",
        "Results:",
        *result_lines,
        "",
        "Outputs:",
        f"- All checked entry points: {checked_jsonl}",
        f"- JSON responses ready for Module 3: {discovery_ready_jsonl}",
        f"- Manual review queue: {manual_review_jsonl}",
        f"- Unavailable entry points: {unavailable_jsonl}",
        f"- Human-readable table: {checked_csv}",
    ]
    return "\n".join(lines)


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
