"""Apply deterministic provider selection rules to the full census.

Selection is kept separate from harvesting so a user can change the provider
subset without downloading the Registry again.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional
from urllib.parse import urlsplit

from .models import ProviderRecord


@dataclass(frozen=True)
class SelectionCriteria:
    """Filters used to choose the providers passed to Module 2.

    Empty include lists mean "include all". Exclusions are applied after all
    inclusion tests. Selection is sorted so the same input gives the same run.
    """

    include_provider_ids: tuple[str, ...] = field(default_factory=tuple)
    include_exact_names: tuple[str, ...] = field(default_factory=tuple)
    include_name_keywords: tuple[str, ...] = field(default_factory=tuple)
    include_hosts: tuple[str, ...] = field(default_factory=tuple)
    exclude_name_keywords: tuple[str, ...] = field(default_factory=tuple)
    exclude_hosts: tuple[str, ...] = field(default_factory=tuple)
    record_statuses: tuple[str, ...] = ("active",)
    limit: Optional[int] = None

    def __post_init__(self) -> None:
        if self.limit is not None and self.limit <= 0:
            raise ValueError("selection limit must be positive or null")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SelectionCriteria":
        limit = value.get("limit")
        return cls(
            include_provider_ids=_strings(value.get("include_provider_ids", [])),
            include_exact_names=_strings(value.get("include_exact_names", [])),
            include_name_keywords=_strings(value.get("include_name_keywords", [])),
            include_hosts=_strings(value.get("include_hosts", [])),
            exclude_name_keywords=_strings(value.get("exclude_name_keywords", [])),
            exclude_hosts=_strings(value.get("exclude_hosts", [])),
            record_statuses=_strings(value.get("record_statuses", ["active"])),
            limit=int(limit) if limit is not None else None,
        )


def select_providers(
    records: Iterable[ProviderRecord], criteria: SelectionCriteria
) -> list[ProviderRecord]:
    """Filter, stably sort, and optionally limit provider records."""

    selected = [record for record in records if _matches(record, criteria)]
    selected.sort(key=lambda item: (item.name.casefold(), item.provider_id))
    if criteria.limit is not None:
        return selected[: criteria.limit]
    return selected


def _matches(record: ProviderRecord, criteria: SelectionCriteria) -> bool:
    """Return whether one provider satisfies all inclusion/exclusion rules."""

    name = record.name.casefold()
    hosts = {
        (urlsplit(candidate.url).hostname or "").casefold()
        for candidate in record.endpoints
    }
    ids = {value.casefold() for value in criteria.include_provider_ids}
    exact_names = {value.casefold() for value in criteria.include_exact_names}
    included_names = tuple(value.casefold() for value in criteria.include_name_keywords)
    included_hosts = tuple(value.casefold() for value in criteria.include_hosts)
    excluded_names = tuple(value.casefold() for value in criteria.exclude_name_keywords)
    excluded_hosts = tuple(value.casefold() for value in criteria.exclude_hosts)
    statuses = {value.casefold() for value in criteria.record_statuses}

    # Inclusion rules narrow the candidate set; exclusion rules then remove
    # explicitly unwanted providers. Empty inclusion lists mean no restriction.
    if statuses and record.record_status.casefold() not in statuses:
        return False
    if ids and record.provider_id.casefold() not in ids:
        return False
    if exact_names and name not in exact_names:
        return False
    if included_names and not any(keyword in name for keyword in included_names):
        return False
    if included_hosts and not any(
        _host_matches(host, allowed)
        for allowed in included_hosts
        for host in hosts
    ):
        return False
    if excluded_names and any(keyword in name for keyword in excluded_names):
        return False
    if excluded_hosts and any(
        _host_matches(host, blocked)
        for blocked in excluded_hosts
        for host in hosts
    ):
        return False
    return True


def _host_matches(host: str, rule: str) -> bool:
    """Match an exact host or any of its subdomains."""

    rule = rule.strip().casefold().lstrip(".")
    return bool(rule) and (host == rule or host.endswith(f".{rule}"))


def _strings(value: Any) -> tuple[str, ...]:
    """Validate a JSON array of strings used by selection configuration."""

    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("selection list values must be JSON arrays")
    return tuple(str(item).strip() for item in value if str(item).strip())
