"""Data models for the provider census and its candidate endpoints."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Optional
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = "2.0"


def canonicalize_url(value: str) -> str:
    """Validate and normalize an absolute HTTP(S) URL."""

    value = value.strip()
    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise ValueError(f"Expected an absolute HTTP(S) URL, got: {value!r}")
    if parts.username or parts.password:
        raise ValueError("URLs containing credentials are not accepted")
    host = (parts.hostname or "").lower()
    port = parts.port
    if port and not (
        (parts.scheme.lower() == "http" and port == 80)
        or (parts.scheme.lower() == "https" and port == 443)
    ):
        host = f"{host}:{port}"
    return urlunsplit((parts.scheme.lower(), host, parts.path or "/", parts.query, ""))


def stable_provider_id(identity_url: str) -> str:
    """Build a repeatable provider identifier from institutional evidence.

    Callers should prefer the institution URL. The endpoint remains a safe
    compatibility fallback when a source does not identify the institution.
    """

    canonical = canonicalize_url(identity_url)
    return f"provider-{sha256(canonical.encode('utf-8')).hexdigest()[:16]}"


@dataclass(frozen=True)
class SourceProvenance:
    """Where and when a provider or endpoint was observed."""

    source_type: str
    source_url: str
    source_page_url: Optional[str] = None
    activity_type: Optional[str] = None
    observed_at: Optional[str] = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SourceProvenance":
        return cls(
            source_type=str(value.get("source_type", "unknown")),
            source_url=str(value.get("source_url", "")),
            source_page_url=_optional_string(value.get("source_page_url")),
            activity_type=_optional_string(value.get("activity_type")),
            observed_at=_optional_string(value.get("observed_at")),
        )


@dataclass(frozen=True)
class EndpointCandidate:
    """One candidate route supplied for an institution.

    endpoint_role is deliberately open text. A provider can have any number of
    routes and new roles do not require a schema change.
    """

    url: str
    endpoint_role: str = "unclassified"
    discovery_type: str = "unknown"
    label: Optional[str] = None
    verification_status: str = "unverified"
    source: SourceProvenance = field(
        default_factory=lambda: SourceProvenance("unknown", "")
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "url", canonicalize_url(self.url))
        if not self.endpoint_role.strip():
            raise ValueError("endpoint_role must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
        *,
        default_source: SourceProvenance | None = None,
    ) -> "EndpointCandidate":
        source_value = value.get("source")
        if isinstance(source_value, Mapping):
            source = SourceProvenance.from_mapping(source_value)
        else:
            source = default_source or SourceProvenance("unknown", "")
        return cls(
            url=str(value.get("url", value.get("discovery_endpoint", ""))),
            endpoint_role=str(value.get("endpoint_role", "unclassified")),
            discovery_type=str(value.get("discovery_type", "unknown")),
            label=_optional_string(value.get("label", value.get("stream_label"))),
            verification_status=str(
                value.get(
                    "verification_status",
                    value.get("endpoint_verification", "unverified"),
                )
            ),
            source=source,
        )


@dataclass(frozen=True)
class ProviderRecord:
    """One institution plus every candidate route currently known for it.

    Legacy single-endpoint fields remain as a projection of the first endpoint
    so existing downstream readers can migrate without losing compatibility.
    """

    provider_id: str
    name: str
    institution_url: Optional[str]
    discovery_endpoint: str
    discovery_type: str = "OrderedCollection"
    stream_label: Optional[str] = None
    collection_focus: Optional[str] = None
    estimated_size: Optional[int] = None
    rights_status: str = "unknown"
    rights_values: tuple[str, ...] = field(default_factory=tuple)
    record_status: str = "active"
    last_checked_at: Optional[str] = None
    source: SourceProvenance = field(
        default_factory=lambda: SourceProvenance("unknown", "")
    )
    raw_source_record: Mapping[str, Any] = field(default_factory=dict)
    endpoints: tuple[EndpointCandidate, ...] = field(default_factory=tuple)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        canonical_endpoint = canonicalize_url(self.discovery_endpoint)
        object.__setattr__(self, "discovery_endpoint", canonical_endpoint)
        if self.institution_url:
            object.__setattr__(
                self, "institution_url", canonicalize_url(self.institution_url)
            )
        if not self.name.strip():
            raise ValueError("Provider name must not be empty")
        if self.estimated_size is not None and self.estimated_size < 0:
            raise ValueError("estimated_size must be non-negative or null")
        if self.record_status not in {"active", "removed"}:
            raise ValueError("record_status must be 'active' or 'removed'")
        if self.rights_status not in {"unknown", "declared", "mixed"}:
            raise ValueError("rights_status must be unknown, declared, or mixed")

        candidates = self.endpoints or (
            EndpointCandidate(
                url=canonical_endpoint,
                endpoint_role=_role_from_type(self.discovery_type),
                discovery_type=self.discovery_type,
                label=self.stream_label,
                verification_status="unverified",
                source=self.source,
            ),
        )
        unique: list[EndpointCandidate] = []
        seen: set[tuple[str, str]] = set()
        for candidate in candidates:
            key = (candidate.url, candidate.endpoint_role.casefold())
            if key not in seen:
                unique.append(candidate)
                seen.add(key)
        object.__setattr__(self, "endpoints", tuple(unique))
        primary = unique[0]
        object.__setattr__(self, "discovery_endpoint", primary.url)
        object.__setattr__(self, "discovery_type", primary.discovery_type)
        if not self.provider_id.strip():
            object.__setattr__(
                self,
                "provider_id",
                stable_provider_id(self.institution_url or primary.url),
            )

    @property
    def endpoint_count(self) -> int:
        return len(self.endpoints)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rights_values"] = list(self.rights_values)
        data["endpoints"] = [candidate.to_dict() for candidate in self.endpoints]
        return data

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProviderRecord":
        source_value = value.get("source") or {}
        if not isinstance(source_value, Mapping):
            raise ValueError("source must be a JSON object")
        source = SourceProvenance.from_mapping(source_value)
        endpoints_value = value.get("endpoints", [])
        if endpoints_value is None:
            endpoints_value = []
        if not isinstance(endpoints_value, list):
            raise ValueError("endpoints must be a JSON array")
        endpoints = tuple(
            EndpointCandidate.from_mapping(item, default_source=source)
            for item in endpoints_value
            if isinstance(item, Mapping)
        )
        endpoint = str(
            value.get("discovery_endpoint")
            or (endpoints[0].url if endpoints else "")
        )
        raw_value = value.get("raw_source_record") or {}
        if not isinstance(raw_value, Mapping):
            raise ValueError("raw_source_record must be a JSON object")
        estimated = value.get("estimated_size")
        identity = _optional_string(value.get("institution_url")) or endpoint
        return cls(
            provider_id=str(
                value.get("provider_id") or stable_provider_id(identity)
            ),
            name=str(value["name"]),
            institution_url=_optional_string(value.get("institution_url")),
            discovery_endpoint=endpoint,
            discovery_type=str(value.get("discovery_type", "unknown")),
            stream_label=_optional_string(value.get("stream_label")),
            collection_focus=_optional_string(value.get("collection_focus")),
            estimated_size=int(estimated) if estimated is not None else None,
            rights_status=str(value.get("rights_status", "unknown")),
            rights_values=tuple(str(item) for item in value.get("rights_values", [])),
            record_status=str(value.get("record_status", "active")),
            last_checked_at=_optional_string(value.get("last_checked_at")),
            source=source,
            raw_source_record=dict(raw_value),
            endpoints=endpoints,
            schema_version=str(value.get("schema_version", SCHEMA_VERSION)),
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


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
