"""Orchestrate the complete Module 1 workflow.

The pipeline is intentionally thin: it coordinates specialized functions from
``fetch``, ``registry``, ``selector``, and ``store`` without duplicating their
logic. This is the main file to read to understand the execution order.
"""

from __future__ import annotations

import json
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fetch import JsonFetcher
from .models import ProviderRecord
from .registry import deduplicate_records, read_manual_records, read_registry
from .selector import SelectionCriteria, select_providers
from .store import write_csv, write_jsonl, write_text


@dataclass(frozen=True)
class PipelineResult:
    all_provider_count: int
    all_endpoint_count: int
    selected_provider_count: int
    selected_endpoint_count: int
    output_directory: Path
    all_providers_jsonl: Path
    selected_providers_jsonl: Path
    providers_csv: Path
    log_txt: Path


def run_pipeline(
    config_path: Path,
    *,
    institution_selection: Sequence[str],
    run_time: datetime | None = None,
) -> PipelineResult:
    """Run the workflow with an explicit human-provided institution choice."""

    # Step 1: Read the run configuration and resolve all relative paths from
    # the configuration file's directory, not from an arbitrary shell path.
    config_path = config_path.resolve()
    config = _read_config(config_path)
    base_directory = config_path.parent

    network = _mapping(config.get("network", {}), "network")
    fetcher = JsonFetcher(
        timeout_seconds=float(network.get("timeout_seconds", 20)),
        retries=int(network.get("retries", 2)),
    )
    max_pages = int(network.get("max_registry_pages", 100))
    local_run_time = _local_run_time(run_time)
    observed_at = local_run_time.isoformat(timespec="seconds")

    # Step 2: Harvest every configured IIIF Registry source. At this point the
    # records are already normalized into ProviderRecord objects.
    records = []
    source_reports: list[dict[str, Any]] = []
    for source in _source_list(config.get("registry_sources", []), "registry_sources"):
        resolved = _resolve_local_source(source, base_directory)
        source_records = read_registry(
            resolved, fetcher, max_pages=max_pages, observed_at=observed_at
        )
        records.extend(source_records)
        source_reports.append({"kind": "iiif_registry", "source": source, "records": len(source_records)})

    # Step 3: Add curated manual providers after Registry records. If both
    # sources describe the same endpoint, the later manual entry can override
    # incomplete registry metadata during the global deduplication below.
    for source in _source_list(config.get("manual_sources", []), "manual_sources"):
        resolved = _resolve_local_source(source, base_directory)
        source_records = read_manual_records(resolved, fetcher, observed_at=observed_at)
        records.extend(source_records)
        source_types = sorted({record.source.source_type for record in source_records})
        public_sources = sorted({record.source.source_url for record in source_records})
        source_reports.append(
            {
                "kind": ", ".join(source_types) if source_types else "manual",
                "source": ", ".join(public_sources) if public_sources else source,
                "input": source,
                "records": len(source_records),
            }
        )

    # Step 4: Create one canonical census, then apply the run-specific filters.
    all_records = deduplicate_records(records)
    criteria, selection_label, requested_names = _selection_for_run(institution_selection)
    selected_records = select_providers(all_records, criteria)
    _validate_requested_names(requested_names, all_records, selected_records)
    all_endpoint_count = sum(record.endpoint_count for record in all_records)
    selected_endpoint_count = sum(record.endpoint_count for record in selected_records)

    # Step 5: Keep exchange data and execution logs in separate directories.
    # ``data/output`` is the contract consumed by people and Module 2, while
    # ``data/log`` keeps timestamped operational records from each run.
    output_directory = _resolve_directory(
        str(config.get("output_directory", "data/output")), base_directory
    )
    log_directory = _resolve_directory(
        str(config.get("log_directory", "data/log")), base_directory
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    log_directory.mkdir(parents=True, exist_ok=True)

    all_jsonl = output_directory / "providers.jsonl"
    selected_jsonl = output_directory / "selected_providers.jsonl"
    csv_path = output_directory / "providers.csv"
    log_path = log_directory / f"Module1_{local_run_time.strftime('%Y-%m-%d_%H-%M-%S')}_log.txt"
    write_jsonl(all_jsonl, all_records)
    write_jsonl(selected_jsonl, selected_records)
    write_csv(csv_path, all_records)
    write_text(
        log_path,
        _format_run_log(
            run_at=observed_at,
            selection_label=selection_label,
            source_reports=source_reports,
            count_before_deduplication=len(records),
            all_provider_count=len(all_records),
            all_endpoint_count=all_endpoint_count,
            selected_provider_count=len(selected_records),
            selected_endpoint_count=selected_endpoint_count,
            all_jsonl=all_jsonl,
            selected_jsonl=selected_jsonl,
            csv_path=csv_path,
        ),
    )

    return PipelineResult(
        all_provider_count=len(all_records),
        all_endpoint_count=all_endpoint_count,
        selected_provider_count=len(selected_records),
        selected_endpoint_count=selected_endpoint_count,
        output_directory=output_directory,
        all_providers_jsonl=all_jsonl,
        selected_providers_jsonl=selected_jsonl,
        providers_csv=csv_path,
        log_txt=log_path,
    )


def _local_run_time(value: datetime | None) -> datetime:
    """Return an aware local datetime used by both provenance and log names."""

    if value is None:
        return datetime.now().astimezone()
    if value.tzinfo is None:
        return value.astimezone()
    return value


def _selection_for_run(
    institution_selection: Sequence[str],
) -> tuple[SelectionCriteria, str, tuple[str, ...]]:
    """Build criteria only from the institution names chosen for this run."""

    names = tuple(dict.fromkeys(name.strip() for name in institution_selection if name.strip()))
    if not names:
        raise ValueError("At least one non-empty --institution value is required")
    all_requested = [name for name in names if name.casefold() == "all"]
    if all_requested:
        if len(names) != 1:
            raise ValueError("Use --institution all by itself; do not combine it with institution names")
        return SelectionCriteria(record_statuses=("active",)), "all active institutions", ()

    return (
        SelectionCriteria(include_exact_names=names, record_statuses=("active",)),
        ", ".join(names),
        names,
    )


def _validate_requested_names(
    requested_names: Sequence[str],
    all_records: Sequence[ProviderRecord],
    selected_records: Sequence[ProviderRecord],
) -> None:
    """Reject unknown or inactive explicit names instead of silently selecting none."""

    if not requested_names:
        return
    selected_names = {record.name.casefold() for record in selected_records}
    missing = [name for name in requested_names if name.casefold() not in selected_names]
    if not missing:
        return
    available = sorted(
        {record.name for record in all_records if record.record_status == "active"},
        key=str.casefold,
    )
    available_text = ", ".join(available) if available else "(none)"
    raise ValueError(
        f"Unknown or inactive institution name(s): {', '.join(missing)}. "
        f"Available active institutions: {available_text}"
    )


def _format_run_log(
    *,
    run_at: str,
    selection_label: str,
    source_reports: Sequence[Mapping[str, Any]],
    count_before_deduplication: int,
    all_provider_count: int,
    all_endpoint_count: int,
    selected_provider_count: int,
    selected_endpoint_count: int,
    all_jsonl: Path,
    selected_jsonl: Path,
    csv_path: Path,
) -> str:
    """Format a concise plain-text account of one completed Module 1 run."""

    source_lines = []
    for report in source_reports:
        input_note = ""
        if report.get("input") and report["input"] != report["source"]:
            input_note = f"; local input: {report['input']}"
        source_lines.append(
            f"- {report['kind']}: {report['source']} "
            f"({report['records']} record(s){input_note})"
        )
    if not source_lines:
        source_lines = ["- (no sources configured)"]
    lines = [
        "Module 1 Run Log",
        "================",
        f"Run time (computer local time): {run_at}",
        f"Institution selection: {selection_label}",
        "",
        "Sources:",
        *source_lines,
        "",
        f"Records before deduplication: {count_before_deduplication}",
        f"Known providers after evidence-based merging: {all_provider_count}",
        f"Candidate endpoints retained: {all_endpoint_count}",
        f"Selected providers: {selected_provider_count}",
        f"Selected candidate endpoints: {selected_endpoint_count}",
        "",
        "Outputs:",
        f"- Full provider census: {all_jsonl}",
        f"- Selected providers for Module 2: {selected_jsonl}",
        f"- Human-readable table: {csv_path}",
    ]
    return "\n".join(lines)


def _read_config(path: Path) -> Mapping[str, Any]:
    """Read the top-level JSON configuration object."""

    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read configuration {path}: {exc}") from exc
    return _mapping(value, "configuration")


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    """Require a decoded JSON value to be an object."""

    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _source_list(value: Any, name: str) -> list[str]:
    """Require a source setting to be an array and convert entries to text."""

    if not isinstance(value, list):
        raise ValueError(f"{name} must be a JSON array")
    return [str(item) for item in value]


def _resolve_local_source(source: str, base_directory: Path) -> str:
    """Keep remote URLs unchanged and resolve local paths against the config."""

    if source.startswith(("http://", "https://", "file://")):
        return source
    path = Path(source)
    if not path.is_absolute():
        path = base_directory / path
    return str(path.resolve())


def _resolve_directory(value: str, base_directory: Path) -> Path:
    """Resolve an output or log directory against the configuration file."""

    path = Path(value)
    if not path.is_absolute():
        path = base_directory / path
    return path.resolve()
