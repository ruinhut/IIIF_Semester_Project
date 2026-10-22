"""Orchestrate Module 3 endpoint resolution and Manifest discovery."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from .discovery import DiscoveryLimits, ResourceDiscoverer
from .fetch import HttpFetcher
from .knowledge import knowledge_for_provider, read_knowledge_base
from .models import DiscoveryEvidence, ProviderDiscoveryResult, ProviderInputRecord, manifest_record
from .store import read_provider_jsonl, write_jsonl, write_provider_csv, write_text


@dataclass(frozen=True)
class CuratedProviderEntry:
    provider_id: Optional[str]
    provider_name: Optional[str]
    entry_points: tuple[str, ...]
    html_seeds: tuple[str, ...]


@dataclass(frozen=True)
class PipelineResult:
    input_provider_count: int
    input_endpoint_count: int
    processed_provider_count: int
    provider_status_counts: Mapping[str, int]
    unique_manifest_count: int
    knowledge_skill_run_count: int
    knowledge_resolved_provider_count: int
    provider_discovery_jsonl: Path
    resolved_endpoints_jsonl: Path
    manifest_urls_jsonl: Path
    unresolved_providers_jsonl: Path
    provider_summary_csv: Path
    log_txt: Path


def run_pipeline(
    config_path: Path,
    *,
    limit: int | None = None,
    run_time: datetime | None = None,
) -> PipelineResult:
    """Run Module 3 and produce the complete documented output contract."""

    config_path = config_path.resolve()
    config = _read_config(config_path)
    base_directory = config_path.parent
    input_value = str(config.get("input_jsonl", "")).strip()
    if not input_value:
        raise ValueError("input_jsonl must be configured")
    input_path = _resolve_path(input_value, base_directory)
    checked_records = read_provider_jsonl(input_path)
    input_endpoint_count = sum(
        len(record.endpoint_routes) for record in checked_records
    )
    providers = _group_provider_records(checked_records)
    input_provider_count = len(providers)

    limits_config = _mapping(config.get("limits", {}), "limits")
    configured_provider_limit = _optional_positive_int(
        limits_config.get("max_providers"), "max_providers"
    )
    effective_limit = limit if limit is not None else configured_provider_limit
    if effective_limit is not None:
        if effective_limit < 1:
            raise ValueError("limit must be positive")
        providers = providers[:effective_limit]

    network = _mapping(config.get("network", {}), "network")
    fetcher = HttpFetcher(
        timeout_seconds=float(network.get("timeout_seconds", 15)),
        retries=int(network.get("retries", 1)),
        backoff_seconds=float(network.get("backoff_seconds", 0.5)),
        max_response_bytes=int(network.get("max_response_bytes", 4 * 1024 * 1024)),
        user_agent=str(
            network.get(
                "user_agent",
                "iiif-resource-discovery/0.1 (+EPFL DHLAB academic research)",
            )
        ),
    )
    discovery_limits = DiscoveryLimits(
        max_stream_pages_per_provider=int(
            limits_config.get("max_stream_pages_per_provider", 5)
        ),
        max_collections_per_provider=int(
            limits_config.get("max_collections_per_provider", 20)
        ),
        max_html_pages_per_provider=int(
            limits_config.get("max_html_pages_per_provider", 3)
        ),
        max_html_depth=int(limits_config.get("max_html_depth", 1)),
        max_candidates_per_html_page=int(
            limits_config.get("max_candidates_per_html_page", 50)
        ),
        max_machine_candidates_per_provider=int(
            limits_config.get("max_machine_candidates_per_provider", 20)
        ),
        max_manifests_per_provider=int(
            limits_config.get("max_manifests_per_provider", 100)
        ),
    )
    html_config = _mapping(config.get("html_discovery", {}), "html_discovery")
    platform_config = _mapping(
        config.get("platform_discovery", {}), "platform_discovery"
    )
    discoverer = ResourceDiscoverer(
        fetcher,
        limits=discovery_limits,
        html_enabled=bool(html_config.get("enabled", True)),
        same_host_only=bool(html_config.get("same_host_only", True)),
        html_delay_seconds=float(html_config.get("delay_between_pages_seconds", 0.1)),
        omeka_s_probe_enabled=bool(
            platform_config.get("omeka_s_probe_enabled", True)
        ),
    )

    curated_path_value = str(config.get("curated_endpoints", "")).strip()
    curated_entries = (
        _read_curated(_resolve_path(curated_path_value, base_directory))
        if curated_path_value
        else []
    )
    knowledge_path_value = str(config.get("knowledge_base", "")).strip()
    knowledge_entries = (
        read_knowledge_base(_resolve_path(knowledge_path_value, base_directory))
        if knowledge_path_value
        else []
    )
    provider_results: list[ProviderDiscoveryResult] = []
    for provider in providers:
        curated = _curated_for_provider(provider, curated_entries)
        knowledge = knowledge_for_provider(
            provider.provider_id, provider.name, knowledge_entries
        )
        result = discoverer.discover(
            provider,
            curated_entry_points=curated.entry_points if curated else (),
            curated_html_seeds=curated.html_seeds if curated else (),
            knowledge_skills=knowledge.skills if knowledge else (),
            investigation_id=knowledge.investigation_id if knowledge else None,
        )
        provider_results.append(result)

    provider_reports = [result.to_dict() for result in provider_results]
    unresolved_reports = [
        report
        for result, report in zip(provider_results, provider_reports)
        if result.status != "manifests_found"
    ]
    resolved_rows = _resolved_endpoint_rows(provider_results)
    manifest_rows = _deduplicated_manifest_rows(provider_results)
    status_counts = Counter(result.status for result in provider_results)
    knowledge_skill_run_count = sum(
        1
        for result in provider_results
        for audit in result.knowledge_application
        if audit.get("status") != "skipped_existing_manifests"
    )
    knowledge_resolved_provider_count = sum(
        1
        for result in provider_results
        if any(
            audit.get("status") == "manifests_found"
            for audit in result.knowledge_application
        )
    )

    output_directory = _resolve_path(
        str(config.get("output_directory", "data/output")), base_directory
    )
    log_directory = _resolve_path(str(config.get("log_directory", "data/log")), base_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    log_directory.mkdir(parents=True, exist_ok=True)
    local_run_time = _local_run_time(run_time)
    run_at = local_run_time.isoformat(timespec="seconds")

    provider_discovery_jsonl = output_directory / "provider_discovery.jsonl"
    resolved_endpoints_jsonl = output_directory / "resolved_endpoints.jsonl"
    manifest_urls_jsonl = output_directory / "manifest_urls.jsonl"
    unresolved_providers_jsonl = output_directory / "unresolved_providers.jsonl"
    provider_summary_csv = output_directory / "provider_discovery.csv"
    log_txt = log_directory / f"Module3_{local_run_time.strftime('%Y-%m-%d_%H-%M-%S')}_log.txt"

    write_jsonl(provider_discovery_jsonl, provider_reports)
    write_jsonl(resolved_endpoints_jsonl, resolved_rows)
    write_jsonl(manifest_urls_jsonl, manifest_rows)
    write_jsonl(unresolved_providers_jsonl, unresolved_reports)
    write_provider_csv(provider_summary_csv, provider_reports)
    write_text(
        log_txt,
        _format_run_log(
            run_at=run_at,
            input_path=input_path,
            input_provider_count=input_provider_count,
            input_endpoint_count=input_endpoint_count,
            effective_limit=effective_limit,
            processed_provider_count=len(provider_results),
            status_counts=status_counts,
            unique_manifest_count=len(manifest_rows),
            resolved_endpoint_count=len(resolved_rows),
            knowledge_skill_run_count=knowledge_skill_run_count,
            knowledge_resolved_provider_count=knowledge_resolved_provider_count,
            truncated_provider_count=sum(1 for result in provider_results if result.truncated),
            provider_discovery_jsonl=provider_discovery_jsonl,
            resolved_endpoints_jsonl=resolved_endpoints_jsonl,
            manifest_urls_jsonl=manifest_urls_jsonl,
            unresolved_providers_jsonl=unresolved_providers_jsonl,
            provider_summary_csv=provider_summary_csv,
        ),
    )

    return PipelineResult(
        input_provider_count=input_provider_count,
        input_endpoint_count=input_endpoint_count,
        processed_provider_count=len(provider_results),
        provider_status_counts=dict(sorted(status_counts.items())),
        unique_manifest_count=len(manifest_rows),
        knowledge_skill_run_count=knowledge_skill_run_count,
        knowledge_resolved_provider_count=knowledge_resolved_provider_count,
        provider_discovery_jsonl=provider_discovery_jsonl,
        resolved_endpoints_jsonl=resolved_endpoints_jsonl,
        manifest_urls_jsonl=manifest_urls_jsonl,
        unresolved_providers_jsonl=unresolved_providers_jsonl,
        provider_summary_csv=provider_summary_csv,
        log_txt=log_txt,
    )


def _group_provider_records(
    records: Sequence[ProviderInputRecord],
) -> list[ProviderInputRecord]:
    """Combine Module 2 endpoint rows into one institution-level work item."""

    grouped: dict[str, dict[str, Any]] = {}
    route_keys: dict[str, set[tuple[str, str, str]]] = {}
    order: list[str] = []
    for record in records:
        provider_id = record.provider_id
        if provider_id not in grouped:
            base = record.to_dict()
            base["endpoint_checks"] = []
            grouped[provider_id] = base
            route_keys[provider_id] = set()
            order.append(provider_id)
        elif grouped[provider_id].get("name") != record.name:
            raise ValueError(
                f"provider_id {provider_id!r} is associated with multiple names"
            )

        for route in record.endpoint_routes:
            candidate = route["endpoint_candidate"]
            check = route["endpoint_check"]
            key = (
                str(candidate.get("url", "")),
                str(candidate.get("endpoint_role", "unclassified")),
                str(check.get("checked_at", "")),
            )
            if key not in route_keys[provider_id]:
                grouped[provider_id]["endpoint_checks"].append(
                    {
                        "endpoint_candidate": dict(candidate),
                        "endpoint_check": dict(check),
                    }
                )
                route_keys[provider_id].add(key)

    return [
        ProviderInputRecord.from_mapping(grouped[provider_id])
        for provider_id in order
    ]


def _deduplicated_manifest_rows(
    results: Sequence[ProviderDiscoveryResult],
) -> list[dict[str, Any]]:
    evidence_by_url: dict[str, list[DiscoveryEvidence]] = defaultdict(list)
    for result in results:
        for finding in result.manifests:
            evidence_by_url[finding.manifest_url].append(finding.evidence)
    return [
        manifest_record(url, evidence_by_url[url]) for url in sorted(evidence_by_url)
    ]


def _resolved_endpoint_rows(
    results: Sequence[ProviderDiscoveryResult],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        for endpoint in result.resolved_endpoints:
            rows.append(
                {
                    "provider_id": result.provider.provider_id,
                    "provider_name": result.provider.name,
                    **endpoint.to_dict(),
                    "module_3_schema_version": "2.0",
                }
            )
    return rows


def _read_curated(path: Path) -> list[CuratedProviderEntry]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read curated endpoints {path}: {exc}") from exc
    if not isinstance(value, Mapping) or not isinstance(value.get("providers"), list):
        raise ValueError("curated endpoints must contain a providers array")
    output: list[CuratedProviderEntry] = []
    for index, item in enumerate(value["providers"]):
        if not isinstance(item, Mapping):
            raise ValueError(f"curated providers[{index}] must be an object")
        provider_id = _optional_string(item.get("provider_id"))
        provider_name = _optional_string(item.get("provider_name", item.get("name")))
        if not provider_id and not provider_name:
            raise ValueError(f"curated providers[{index}] needs provider_id or provider_name")
        output.append(
            CuratedProviderEntry(
                provider_id=provider_id,
                provider_name=provider_name,
                entry_points=_string_array(item.get("entry_points", []), "entry_points"),
                html_seeds=_string_array(item.get("html_seeds", []), "html_seeds"),
            )
        )
    return output


def _curated_for_provider(
    provider: ProviderInputRecord, entries: Sequence[CuratedProviderEntry]
) -> Optional[CuratedProviderEntry]:
    for entry in entries:
        if entry.provider_id and entry.provider_id == provider.provider_id:
            return entry
    for entry in entries:
        if entry.provider_name and entry.provider_name.casefold() == provider.name.casefold():
            return entry
    return None


def _format_run_log(
    *,
    run_at: str,
    input_path: Path,
    input_provider_count: int,
    input_endpoint_count: int,
    effective_limit: int | None,
    processed_provider_count: int,
    status_counts: Mapping[str, int],
    unique_manifest_count: int,
    resolved_endpoint_count: int,
    knowledge_skill_run_count: int,
    knowledge_resolved_provider_count: int,
    truncated_provider_count: int,
    provider_discovery_jsonl: Path,
    resolved_endpoints_jsonl: Path,
    manifest_urls_jsonl: Path,
    unresolved_providers_jsonl: Path,
    provider_summary_csv: Path,
) -> str:
    status_lines = [f"- {name}: {count}" for name, count in sorted(status_counts.items())]
    if not status_lines:
        status_lines = ["- (no providers processed)"]
    return "\n".join(
        [
            "Module 3 Run Log",
            "================",
            f"Run time (computer local time): {run_at}",
            f"Input: {input_path}",
            f"Input providers after grouping: {input_provider_count}",
            f"Input checked endpoint records: {input_endpoint_count}",
            f"Run limit: {effective_limit if effective_limit is not None else 'none'}",
            f"Processed providers: {processed_provider_count}",
            f"Resolved machine endpoints: {resolved_endpoint_count}",
            f"Unique Manifest URLs: {unique_manifest_count}",
            f"Knowledge skill runs: {knowledge_skill_run_count}",
            f"Providers resolved by knowledge skills: {knowledge_resolved_provider_count}",
            f"Providers stopped by a configured limit: {truncated_provider_count}",
            "",
            "Provider results:",
            *status_lines,
            "",
            "Outputs:",
            f"- Provider discovery reports: {provider_discovery_jsonl}",
            f"- Resolved machine endpoints: {resolved_endpoints_jsonl}",
            f"- Manifest URLs for Module 4: {manifest_urls_jsonl}",
            f"- Providers without discovered Manifests: {unresolved_providers_jsonl}",
            f"- Human-readable provider summary: {provider_summary_csv}",
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


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_array(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return tuple(str(item) for item in value)


def _local_run_time(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now().astimezone()
    if value.tzinfo is None:
        return value.astimezone()
    return value
