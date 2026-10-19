"""Orchestrate Module 2 validation of every Module 1 endpoint."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any, Mapping, Protocol, Sequence

from .checker import EndpointChecker
from .models import (
    CHECK_RESULTS,
    CheckedProviderRecord,
    EndpointCheck,
)
from .store import read_provider_jsonl, write_checked_jsonl, write_csv, write_text


DISCOVERY_READY_RESULTS = {"reachable_json"}
MANUAL_REVIEW_RESULTS = {
    "reachable_non_json",
    "invalid_json",
    "response_too_large",
    "restricted",
}
UNAVAILABLE_RESULTS = {"temporary_failure", "unreachable"}
REACHABLE_RESULTS = {"reachable_json", "reachable_non_json", "invalid_json"}


class CheckerProtocol(Protocol):
    def check(self, url: str, *, checked_at: str) -> EndpointCheck:
        """Return an endpoint check for one URL."""


@dataclass(frozen=True)
class PipelineResult:
    input_count: int
    input_endpoint_count: int
    checked_count: int
    unique_request_count: int
    providers_with_reachable_endpoint: int
    providers_with_json_endpoint: int
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
    """Check every candidate endpoint for each selected Module 1 provider."""

    config_path = config_path.resolve()
    config = _read_config(config_path)
    base_directory = config_path.parent
    input_value = str(config.get("input_jsonl", "")).strip()
    if not input_value:
        raise ValueError("input_jsonl must be configured")
    input_path = _resolve_path(input_value, base_directory)

    providers = read_provider_jsonl(input_path)
    original_input_count = len(providers)
    original_endpoint_count = sum(
        len(provider.endpoint_candidates) for provider in providers
    )
    run_config = _mapping(config.get("run", {}), "run")
    configured_limit = _optional_positive_int(
        run_config.get("max_records"), "max_records"
    )
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
        max_response_bytes=int(
            network.get("max_response_bytes", 2 * 1024 * 1024)
        ),
        user_agent=str(
            network.get(
                "user_agent",
                "iiif-entry-validator/0.2 (+EPFL DHLAB academic research)",
            )
        ),
    )
    delay = float(run_config.get("delay_between_requests_seconds", 0.1))
    if delay < 0:
        raise ValueError("delay_between_requests_seconds must be non-negative")

    local_run_time = _local_run_time(run_time)
    checked_at = local_run_time.isoformat(timespec="seconds")
    jobs = [
        (provider, candidate)
        for provider in providers
        for candidate in provider.endpoint_candidates
    ]
    checked_records: list[CheckedProviderRecord] = []
    check_cache: dict[str, EndpointCheck] = {}
    requests_made = 0
    for job_index, (provider, candidate) in enumerate(jobs):
        endpoint_check = check_cache.get(candidate.url)
        if endpoint_check is None:
            endpoint_check = active_checker.check(
                candidate.url, checked_at=checked_at
            )
            check_cache[candidate.url] = endpoint_check
            requests_made += 1
            if delay and job_index + 1 < len(jobs):
                time.sleep(delay)
        checked_records.append(
            CheckedProviderRecord(
                provider=provider,
                endpoint_check=endpoint_check,
                endpoint_candidate=candidate,
            )
        )

    discovery_ready = _records_with_results(
        checked_records, DISCOVERY_READY_RESULTS
    )
    manual_review = _records_with_results(
        checked_records, MANUAL_REVIEW_RESULTS
    )
    unavailable = _records_with_results(checked_records, UNAVAILABLE_RESULTS)
    observed_counts = Counter(
        record.endpoint_check.check_result for record in checked_records
    )
    result_counts = {
        name: observed_counts.get(name, 0) for name in sorted(CHECK_RESULTS)
    }
    reachable_provider_ids = {
        record.provider.provider_id
        for record in checked_records
        if record.endpoint_check.check_result in REACHABLE_RESULTS
    }
    json_provider_ids = {
        record.provider.provider_id
        for record in checked_records
        if record.endpoint_check.check_result == "reachable_json"
    }

    output_directory = _resolve_path(
        str(config.get("output_directory", "data/output")), base_directory
    )
    log_directory = _resolve_path(
        str(config.get("log_directory", "data/log")), base_directory
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    log_directory.mkdir(parents=True, exist_ok=True)

    checked_jsonl = output_directory / "checked_entry_points.jsonl"
    discovery_ready_jsonl = output_directory / "discovery_ready.jsonl"
    manual_review_jsonl = output_directory / "manual_review.jsonl"
    unavailable_jsonl = output_directory / "unavailable_entry_points.jsonl"
    checked_csv = output_directory / "checked_entry_points.csv"
    log_txt = (
        log_directory
        / f"Module2_{local_run_time.strftime('%Y-%m-%d_%H-%M-%S')}_log.txt"
    )

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
            original_endpoint_count=original_endpoint_count,
            selected_provider_count=len(providers),
            effective_limit=effective_limit,
            checked_count=len(checked_records),
            unique_request_count=requests_made,
            providers_with_reachable_endpoint=len(reachable_provider_ids),
            providers_with_json_endpoint=len(json_provider_ids),
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
        input_endpoint_count=original_endpoint_count,
        checked_count=len(checked_records),
        unique_request_count=requests_made,
        providers_with_reachable_endpoint=len(reachable_provider_ids),
        providers_with_json_endpoint=len(json_provider_ids),
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
    return [
        record
        for record in records
        if record.endpoint_check.check_result in results
    ]


def _format_run_log(
    *,
    run_at: str,
    input_path: Path,
    original_input_count: int,
    original_endpoint_count: int,
    selected_provider_count: int,
    effective_limit: int | None,
    checked_count: int,
    unique_request_count: int,
    providers_with_reachable_endpoint: int,
    providers_with_json_endpoint: int,
    result_counts: Mapping[str, int],
    checked_jsonl: Path,
    discovery_ready_jsonl: Path,
    manual_review_jsonl: Path,
    unavailable_jsonl: Path,
    checked_csv: Path,
) -> str:
    result_lines = [
        f"- {name}: {count}" for name, count in sorted(result_counts.items())
    ] or ["- (no endpoints checked)"]
    return "\n".join(
        [
            "Module 2 Run Log",
            "================",
            f"Run time (computer local time): {run_at}",
            f"Input: {input_path}",
            f"Input providers: {original_input_count}",
            f"Input candidate endpoints: {original_endpoint_count}",
            f"Run provider limit: {effective_limit if effective_limit is not None else 'none'}",
            f"Run limit: {effective_limit if effective_limit is not None else 'none'}",
            f"Selected providers: {selected_provider_count}",
            f"Checked endpoint records: {checked_count}",
            f"Checked records: {checked_count}",
            f"Unique URL requests: {unique_request_count}",
            f"Providers with at least one reachable endpoint: {providers_with_reachable_endpoint}",
            f"Providers with at least one parseable JSON endpoint: {providers_with_json_endpoint}",
            "",
            "Endpoint results:",
            *result_lines,
            "",
            "Outputs:",
            f"- All checked entry points for Module 3: {checked_jsonl}",
            f"- Parseable JSON endpoints: {discovery_ready_jsonl}",
            f"- HTML/restricted/manual-review endpoints: {manual_review_jsonl}",
            f"- Unavailable endpoints: {unavailable_jsonl}",
            f"- Human-readable endpoint table: {checked_csv}",
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
