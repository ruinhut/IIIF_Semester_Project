"""Translate Registry and manual source documents into provider records.

The official IIIF Registry is itself a Change Discovery collection. This file
walks its pages, interprets each activity as a provider-feed observation, and
normalizes varying label/actor shapes into the single Module 1 data model.
It does not fetch Manifests or test provider endpoints; those are later stages.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence
from urllib.parse import urljoin, urlparse

from .fetch import JsonFetcher
from .models import EndpointCandidate, ProviderRecord, SourceProvenance, canonicalize_url, stable_provider_id


ACTIVE_ACTIVITY_TYPES = {"add", "create", "update"}
REMOVED_ACTIVITY_TYPES = {"delete", "remove"}


def utc_now() -> str:
    """Return a compact UTC timestamp for provenance and run summaries."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_registry(
    source: str,
    fetcher: JsonFetcher,
    *,
    max_pages: int = 100,
    observed_at: Optional[str] = None,
) -> list[ProviderRecord]:
    """Read a Change Discovery registry collection or page.

    The function follows ``first`` and then ``next`` links. A visited-set and
    ``max_pages`` guard prevent cycles or unbounded crawling.
    """

    if max_pages <= 0:
        raise ValueError("max_pages must be positive")
    observed_at = observed_at or utc_now()
    document = fetcher.load(source)
    if not isinstance(document, Mapping):
        raise ValueError("Registry source must contain a JSON object")

    doc_type = document.get("type")
    if doc_type == "OrderedCollection":
        # Prefer forward traversal from ``first``. The IIIF specification only
        # requires ``last``, so backwards traversal is supported as a fallback.
        first_reference = _link_id(document.get("first"))
        page_reference = first_reference or _link_id(document.get("last"))
        if not page_reference:
            raise ValueError("Registry OrderedCollection has neither first nor last page")
        page_reference = _resolve_reference(source, page_reference)
        traversal_link = "next" if first_reference else "prev"
    elif doc_type == "OrderedCollectionPage":
        page_reference = source
        traversal_link = "next"
    elif "streams" in document:
        return _parse_legacy_registry_record(document, source, observed_at)
    else:
        raise ValueError(f"Unsupported registry document type: {doc_type!r}")

    # Load pages before parsing activities. This lets backwards traversal be
    # restored to chronological order before later observations replace older
    # observations for the same endpoint.
    pages: list[tuple[str, Mapping[str, Any]]] = []
    visited: set[str] = set()
    for _ in range(max_pages):
        if page_reference in visited:
            raise ValueError(f"Cycle detected in registry pages at {page_reference}")
        visited.add(page_reference)

        page = fetcher.load(page_reference)
        if not isinstance(page, Mapping) or page.get("type") != "OrderedCollectionPage":
            raise ValueError(f"Expected OrderedCollectionPage at {page_reference}")
        items = page.get("orderedItems")
        if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
            raise ValueError(f"orderedItems must be an array at {page_reference}")
        pages.append((page_reference, page))

        next_reference = _link_id(page.get(traversal_link))
        if not next_reference:
            break
        page_reference = _resolve_reference(page_reference, next_reference)
    else:
        raise ValueError(f"Registry exceeds max_pages={max_pages}")

    # When only ``last`` is available, pages were read newest to oldest.
    # Restore chronological order so that deduplication keeps the latest event.
    if traversal_link == "prev":
        pages.reverse()

    records: list[ProviderRecord] = []
    for page_url, page in pages:
        for activity in page["orderedItems"]:
            if isinstance(activity, Mapping):
                record = _record_from_activity(
                    activity,
                    source_url=source,
                    page_url=page_url,
                    observed_at=observed_at,
                )
                if record is not None:
                    records.append(record)

    return deduplicate_records(records)


def read_manual_records(
    source: str,
    fetcher: JsonFetcher,
    *,
    observed_at: Optional[str] = None,
) -> list[ProviderRecord]:
    """Read supplementary catalogues without discarding any listed endpoint."""

    observed_at = observed_at or utc_now()
    document = fetcher.load(source)
    source_metadata: Mapping[str, Any] = {}
    if isinstance(document, Mapping):
        items = document.get("providers")
        metadata_value = document.get("source") or {}
        if not isinstance(metadata_value, Mapping):
            raise ValueError("Manual source metadata must be a JSON object")
        source_metadata = metadata_value
    else:
        items = document
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise ValueError("Manual source must be an array or an object with a providers array")

    records: list[ProviderRecord] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise ValueError(f"Manual provider at index {index} must be an object")
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValueError(f"Manual provider at index {index} requires name")

        provenance = SourceProvenance(
            source_type=str(source_metadata.get("source_type") or "manual"),
            source_url=str(source_metadata.get("source_url") or source),
            source_page_url=_optional_text(item.get("source_page_url")),
            observed_at=observed_at,
        )
        endpoint_values = item.get("endpoints", [])
        if endpoint_values is None:
            endpoint_values = []
        if not isinstance(endpoint_values, Sequence) or isinstance(
            endpoint_values, (str, bytes)
        ):
            raise ValueError(f"Manual provider at index {index} endpoints must be an array")
        endpoints = [
            EndpointCandidate.from_mapping(value, default_source=provenance)
            for value in endpoint_values
            if isinstance(value, Mapping)
        ]
        legacy_endpoint = str(item.get("discovery_endpoint", "")).strip()
        if legacy_endpoint and not endpoints:
            endpoints.append(
                EndpointCandidate(
                    url=legacy_endpoint,
                    endpoint_role=str(item.get("endpoint_role") or _role_from_type(str(item.get("discovery_type", "unknown")))),
                    discovery_type=str(item.get("discovery_type", "unknown")),
                    label=_optional_text(item.get("stream_label")),
                    verification_status=str(item.get("endpoint_verification", "unverified")),
                    source=provenance,
                )
            )
        if not endpoints:
            raise ValueError(
                f"Manual provider at index {index} requires discovery_endpoint or endpoints"
            )

        institution_url = _optional_text(item.get("institution_url"))
        rights_values = tuple(str(value) for value in item.get("rights_values", []))
        rights_status = str(
            item.get("rights_status") or ("declared" if rights_values else "unknown")
        )
        estimated = item.get("estimated_size")
        primary = endpoints[0]
        records.append(
            ProviderRecord(
                provider_id=str(
                    item.get("provider_id")
                    or stable_provider_id(institution_url or primary.url)
                ),
                name=name,
                institution_url=institution_url,
                discovery_endpoint=primary.url,
                discovery_type=primary.discovery_type,
                stream_label=_optional_text(item.get("stream_label")) or primary.label,
                collection_focus=_optional_text(item.get("collection_focus")),
                estimated_size=int(estimated) if estimated is not None else None,
                rights_status=rights_status,
                rights_values=rights_values,
                record_status=str(item.get("record_status", "active")),
                last_checked_at=_optional_text(item.get("last_checked_at")),
                source=provenance,
                raw_source_record=dict(item),
                endpoints=tuple(endpoints),
            )
        )
    return deduplicate_records(records)


def deduplicate_records(records: Iterable[ProviderRecord]) -> list[ProviderRecord]:
    """Merge observations of the same evidenced institution and keep all routes.

    A matching name by itself is never enough. Records merge through a stable
    provider ID, a canonical institution URL, or an already-shared endpoint.
    """

    merged: dict[str, ProviderRecord] = {}
    endpoint_owner: dict[str, str] = {}
    provider_owner: dict[str, str] = {}
    institution_owner: dict[str, str] = {}

    for record in records:
        institution_key = (
            canonicalize_url(record.institution_url)
            if record.institution_url
            else None
        )
        owner = provider_owner.get(record.provider_id)
        if owner is None and institution_key:
            owner = institution_owner.get(institution_key)
        if owner is None:
            owner = next(
                (
                    endpoint_owner[candidate.url]
                    for candidate in record.endpoints
                    if candidate.url in endpoint_owner
                ),
                None,
            )
        if owner is None:
            owner = record.provider_id
            merged[owner] = record
        else:
            merged[owner] = _merge_provider_records(merged[owner], record)

        current = merged[owner]
        provider_owner[record.provider_id] = owner
        provider_owner[current.provider_id] = owner
        if institution_key:
            institution_owner[institution_key] = owner
        if current.institution_url:
            institution_owner[canonicalize_url(current.institution_url)] = owner
        for candidate in current.endpoints:
            endpoint_owner[candidate.url] = owner

    return sorted(
        merged.values(),
        key=lambda item: (item.name.casefold(), item.provider_id),
    )


def _merge_provider_records(
    earlier: ProviderRecord, later: ProviderRecord
) -> ProviderRecord:
    """Combine two evidenced observations while preferring later metadata."""

    endpoints: dict[tuple[str, str], EndpointCandidate] = {}
    order: list[tuple[str, str]] = []
    for candidate in (*earlier.endpoints, *later.endpoints):
        key = (candidate.url, candidate.endpoint_role.casefold())
        if key not in endpoints:
            order.append(key)
        endpoints[key] = candidate
    merged_endpoints = tuple(endpoints[key] for key in order)

    rights_values = tuple(dict.fromkeys((*earlier.rights_values, *later.rights_values)))
    if earlier.rights_status == later.rights_status:
        rights_status = later.rights_status
    elif "unknown" in {earlier.rights_status, later.rights_status}:
        rights_status = (
            later.rights_status
            if later.rights_status != "unknown"
            else earlier.rights_status
        )
    else:
        rights_status = "mixed"

    observations: list[Mapping[str, Any]] = []
    for raw in (earlier.raw_source_record, later.raw_source_record):
        nested = raw.get("observations") if isinstance(raw, Mapping) else None
        if isinstance(nested, list):
            observations.extend(item for item in nested if isinstance(item, Mapping))
        elif raw:
            observations.append(raw)

    return ProviderRecord(
        provider_id=earlier.provider_id,
        name=later.name or earlier.name,
        institution_url=later.institution_url or earlier.institution_url,
        discovery_endpoint=merged_endpoints[0].url,
        discovery_type=merged_endpoints[0].discovery_type,
        stream_label=later.stream_label or earlier.stream_label,
        collection_focus=later.collection_focus or earlier.collection_focus,
        estimated_size=(
            later.estimated_size
            if later.estimated_size is not None
            else earlier.estimated_size
        ),
        rights_status=rights_status,
        rights_values=rights_values,
        record_status=later.record_status,
        last_checked_at=later.last_checked_at or earlier.last_checked_at,
        source=later.source,
        raw_source_record={"observations": observations},
        endpoints=merged_endpoints,
    )


def _role_from_type(discovery_type: str) -> str:
    normalized = discovery_type.casefold()
    if "orderedcollection" in normalized or "activity" in normalized:
        return "change_discovery"
    if normalized == "collection" or "presentation" in normalized:
        return "presentation_collection"
    if normalized == "manifest":
        return "manifest"
    if "website" in normalized:
        return "institution_website"
    return "unclassified"


def _record_from_activity(
    activity: Mapping[str, Any],
    *,
    source_url: str,
    page_url: str,
    observed_at: str,
) -> Optional[ProviderRecord]:
    """Convert one Registry activity into one normalized provider record."""

    activity_type = str(activity.get("type", "Update"))
    normalized_type = activity_type.casefold()
    if normalized_type not in ACTIVE_ACTIVITY_TYPES | REMOVED_ACTIVITY_TYPES:
        return None

    object_value = activity.get("object")
    if isinstance(object_value, str):
        object_value = {"id": object_value, "type": "OrderedCollection"}
    if not isinstance(object_value, Mapping):
        return None
    endpoint = _link_id(object_value)
    if not endpoint:
        return None
    endpoint = _resolve_reference(page_url, endpoint)

    # Provider identity belongs to ``actor`` while the discovery feed belongs
    # to ``object``. Some Registry records use more than one actor object.
    actors = _as_mapping_list(activity.get("actor"))
    provider_name = next((_extract_label(actor) for actor in actors if _extract_label(actor)), None)
    institution_url = next((_link_id(actor) for actor in actors if _link_id(actor)), None)
    stream_label = _extract_label(object_value)
    if not provider_name:
        provider_name = stream_label or _host_name(endpoint)

    rights_values = _rights_values(object_value.get("rights"))
    total_items = object_value.get("totalItems")
    estimated_size = int(total_items) if isinstance(total_items, int) and total_items >= 0 else None
    raw_copy = dict(activity)
    return ProviderRecord(
        provider_id=stable_provider_id(institution_url or endpoint),
        name=provider_name,
        institution_url=institution_url,
        discovery_endpoint=endpoint,
        discovery_type=str(object_value.get("type", "OrderedCollection")),
        stream_label=stream_label,
        collection_focus=stream_label,
        estimated_size=estimated_size,
        rights_status="declared" if rights_values else "unknown",
        rights_values=rights_values,
        record_status="removed" if normalized_type in REMOVED_ACTIVITY_TYPES else "active",
        source=SourceProvenance(
            source_type="iiif_registry",
            source_url=source_url,
            source_page_url=page_url,
            activity_type=activity_type,
            observed_at=observed_at,
        ),
        raw_source_record=raw_copy,
    )


def _parse_legacy_registry_record(
    document: Mapping[str, Any], source: str, observed_at: str
) -> list[ProviderRecord]:
    """Support the older Registry document containing a ``streams`` array."""

    institution = document.get("institution")
    if not isinstance(institution, Mapping):
        institution = {}
    name = _extract_label(institution) or _extract_label(document) or _host_name(str(document.get("id", source)))
    institution_url = _link_id(institution) or _optional_text(document.get("id"))
    streams = document.get("streams")
    if not isinstance(streams, Sequence) or isinstance(streams, (str, bytes)):
        raise ValueError("Legacy registry record has no streams array")

    records: list[ProviderRecord] = []
    for stream in streams:
        if not isinstance(stream, Mapping):
            continue
        endpoint = _link_id(stream)
        if not endpoint:
            continue
        endpoint = _resolve_reference(source, endpoint)
        stream_label = _extract_label(stream)
        records.append(
            ProviderRecord(
                provider_id=stable_provider_id(institution_url or endpoint),
                name=name,
                institution_url=institution_url,
                discovery_endpoint=endpoint,
                stream_label=stream_label,
                collection_focus=stream_label,
                source=SourceProvenance(
                    source_type="iiif_registry_legacy",
                    source_url=source,
                    observed_at=observed_at,
                ),
                raw_source_record=dict(document),
            )
        )
    return deduplicate_records(records)


def _extract_label(value: Mapping[str, Any]) -> Optional[str]:
    """Extract human-readable text from common IIIF label representations."""

    for key in ("label", "name", "nameMap", "summary"):
        label = _language_value(value.get(key))
        if label:
            return label

    # The live registry currently includes one actor as a language map with a
    # sibling type property rather than nesting it under label.
    language_map = {key: item for key, item in value.items() if key not in {"id", "type"}}
    return _language_value(language_map)


def _language_value(value: Any) -> Optional[str]:
    """Return the first useful string from a string, array, or language map."""

    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            result = _language_value(item)
            if result:
                return result
    if isinstance(value, Mapping):
        preferred_keys = ("en", "none", "@none")
        for key in preferred_keys:
            if key in value:
                result = _language_value(value[key])
                if result:
                    return result
        for item in value.values():
            result = _language_value(item)
            if result:
                return result
    return None


def _rights_values(value: Any) -> tuple[str, ...]:
    """Normalize an optional rights value to an immutable sequence of URIs."""

    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _as_mapping_list(value: Any) -> list[Mapping[str, Any]]:
    """Treat a single JSON object and an array of objects uniformly."""

    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _link_id(value: Any) -> Optional[str]:
    """Read an IIIF link supplied as a URI string or an object with ``id``."""

    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, Mapping):
        identifier = value.get("id") or value.get("@id")
        return _optional_text(identifier)
    return None


def _resolve_reference(base: str, reference: str) -> str:
    """Resolve relative page links for both HTTP URLs and local test files."""

    if urlparse(reference).scheme in {"http", "https"}:
        return reference
    if urlparse(base).scheme in {"http", "https"}:
        return urljoin(base, reference)
    return str((Path(base).resolve().parent / reference).resolve())


def _host_name(url: str) -> str:
    """Use the URL host as a conservative fallback provider name."""

    parsed = urlparse(url)
    return parsed.hostname or url


def _optional_text(value: Any) -> Optional[str]:
    """Return stripped text or ``None`` for a missing/empty value."""

    if value is None:
        return None
    text = str(value).strip()
    return text or None
