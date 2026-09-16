"""Data models for the provider census.

Only Python's standard library is used so that the module can run in a clean
Python 3.10 installation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Optional
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = "1.0"


def canonicalize_url(value: str) -> str:
    """Validate and normalize an HTTP(S) URL for identity and filtering.

    Host names and schemes are case-insensitive, default ports are removed,
    and fragments are discarded because they do not identify a registry feed.
    """

    value = value.strip()
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ValueError(f"Expected an absolute HTTP(S) URL, got: {value!r}")

    host = (parts.hostname or "").lower()
    port = parts.port
    if port and not ((parts.scheme == "http" and port == 80) or (parts.scheme == "https" and port == 443)):
        host = f"{host}:{port}"
    if parts.username or parts.password:
        raise ValueError("URLs containing credentials are not accepted")

    return urlunsplit((parts.scheme.lower(), host, parts.path or "/", parts.query, ""))


def stable_provider_id(discovery_endpoint: str) -> str:
    """Build a repeatable identifier from the canonical discovery endpoint."""

    canonical = canonicalize_url(discovery_endpoint)
    return f"provider-{sha256(canonical.encode('utf-8')).hexdigest()[:16]}"


@dataclass(frozen=True)
class SourceProvenance:
    """Where and when one provider record was observed."""

    source_type: str
    source_url: str
    source_page_url: Optional[str] = None
    activity_type: Optional[str] = None
    observed_at: Optional[str] = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SourceProvenance":
        """Reconstruct provenance from one decoded JSON object."""

        return cls(
            source_type=str(value.get("source_type", "unknown")),
            source_url=str(value.get("source_url", "")),
            source_page_url=_optional_string(value.get("source_page_url")),
            activity_type=_optional_string(value.get("activity_type")),
            observed_at=_optional_string(value.get("observed_at")),
        )


@dataclass(frozen=True)
class ProviderRecord:
    """Canonical provider record emitted by Module 1.

    Unknown values remain explicit rather than being guessed. The raw source
    record and provenance are retained so every normalized field is auditable.
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
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        # Frozen dataclasses prevent accidental changes after validation. The
        # normalized URLs are therefore assigned through object.__setattr__.
        canonical_endpoint = canonicalize_url(self.discovery_endpoint)
        object.__setattr__(self, "discovery_endpoint", canonical_endpoint)

        if self.institution_url:
            object.__setattr__(self, "institution_url", canonicalize_url(self.institution_url))
        if not self.name.strip():
            raise ValueError("Provider name must not be empty")
        if self.estimated_size is not None and self.estimated_size < 0:
            raise ValueError("estimated_size must be non-negative or null")
        if self.record_status not in {"active", "removed"}:
            raise ValueError("record_status must be 'active' or 'removed'")
        if self.rights_status not in {"unknown", "declared", "mixed"}:
            raise ValueError("rights_status must be unknown, declared, or mixed")

    def to_dict(self) -> dict[str, Any]:
        """Convert the record into a JSON-serializable dictionary."""

        data = asdict(self)
        data["rights_values"] = list(self.rights_values)
        return data

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProviderRecord":
        """Validate and reconstruct one record read from JSONL storage."""

        endpoint = str(value["discovery_endpoint"])
        source_value = value.get("source") or {}
        if not isinstance(source_value, Mapping):
            raise ValueError("source must be a JSON object")
        raw_value = value.get("raw_source_record") or {}
        if not isinstance(raw_value, Mapping):
            raise ValueError("raw_source_record must be a JSON object")

        estimated = value.get("estimated_size")
        return cls(
            provider_id=str(value.get("provider_id") or stable_provider_id(endpoint)),
            name=str(value["name"]),
            institution_url=_optional_string(value.get("institution_url")),
            discovery_endpoint=endpoint,
            discovery_type=str(value.get("discovery_type", "OrderedCollection")),
            stream_label=_optional_string(value.get("stream_label")),
            collection_focus=_optional_string(value.get("collection_focus")),
            estimated_size=int(estimated) if estimated is not None else None,
            rights_status=str(value.get("rights_status", "unknown")),
            rights_values=tuple(str(item) for item in value.get("rights_values", [])),
            record_status=str(value.get("record_status", "active")),
            last_checked_at=_optional_string(value.get("last_checked_at")),
            source=SourceProvenance.from_mapping(source_value),
            raw_source_record=dict(raw_value),
            schema_version=str(value.get("schema_version", SCHEMA_VERSION)),
        )


def _optional_string(value: Any) -> Optional[str]:
    """Convert an optional value to stripped text without inventing content."""

    if value is None:
        return None
    text = str(value).strip()
    return text or None
