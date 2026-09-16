"""Orchestrate the complete Module 1 workflow.

The pipeline is intentionally thin: it coordinates specialized functions from
``fetch``, ``registry``, ``selector``, and ``store`` without duplicating their
logic. This is the main file to read to understand the execution order.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .fetch import JsonFetcher
from .registry import deduplicate_records, read_manual_records, read_registry, utc_now
from .selector import SelectionCriteria, select_providers
from .store import write_csv, write_json, write_jsonl


@dataclass(frozen=True)
class PipelineResult:
    all_provider_count: int
    selected_provider_count: int
    output_directory: Path
    all_providers_jsonl: Path
    selected_providers_jsonl: Path
    providers_csv: Path
    run_summary_json: Path


def run_pipeline(config_path: Path) -> PipelineResult:
    """Run census, normalization, selection, and export from one config file."""

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
    observed_at = utc_now()

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
        source_reports.append({"kind": "manual", "source": source, "records": len(source_records)})

    # Step 4: Create one canonical census, then apply the run-specific filters.
    all_records = deduplicate_records(records)
    criteria = SelectionCriteria.from_mapping(_mapping(config.get("selection", {}), "selection"))
    selected_records = select_providers(all_records, criteria)

    # Step 5: Resolve the output directory and materialize the data contract
    # consumed by people and by Module 2.
    output_value = str(config.get("output_directory", "data/output"))
    output_directory = Path(output_value)
    if not output_directory.is_absolute():
        output_directory = (base_directory / output_directory).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    all_jsonl = output_directory / "providers.jsonl"
    selected_jsonl = output_directory / "selected_providers.jsonl"
    csv_path = output_directory / "providers.csv"
    summary_path = output_directory / "run_summary.json"
    write_jsonl(all_jsonl, all_records)
    write_jsonl(selected_jsonl, selected_records)
    write_csv(csv_path, all_records)
    write_json(
        summary_path,
        {
            "module": "IIIF Provider Census and Selector",
            "schema_version": "1.0",
            "run_at": observed_at,
            "source_reports": source_reports,
            "provider_count_before_deduplication": len(records),
            "all_provider_count": len(all_records),
            "selected_provider_count": len(selected_records),
            "outputs": {
                "providers_jsonl": str(all_jsonl),
                "selected_providers_jsonl": str(selected_jsonl),
                "providers_csv": str(csv_path),
            },
        },
    )

    return PipelineResult(
        all_provider_count=len(all_records),
        selected_provider_count=len(selected_records),
        output_directory=output_directory,
        all_providers_jsonl=all_jsonl,
        selected_providers_jsonl=selected_jsonl,
        providers_csv=csv_path,
        run_summary_json=summary_path,
    )


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
