"""Data contracts for Module 2 inputs and Module 3 discovery outputs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Optional
from urllib.parse import urlsplit, urlunsplit


MODULE_3_SCHEMA_VERSION = "1.0"


def canonicalize_url(value: str) -> str:
    """Validate and normalize an HTTP(S) URL for stable deduplication."""

    text = value.strip()
    parts = urlsplit(text)
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


def stable_manifest_id(manifest_url: str) -> str:
    """Create a repeatable identifier from a canonical Manifest URL."""

    canonical = canonicalize_url(manifest_url)
    digest = sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"manifest-{digest}"


@dataclass(frozen=True)
class ProviderInputRecord:
    """One Module 2 record preserved in full for traceability."""

    data: Mapping[str, Any]

    def __post_init__(self) -> None:
        copied = deepcopy(dict(self.data))
        for name in ("provider_id", "name", "discovery_endpoint"):
            if name not in copied or not str(copied[name]).strip():
                raise ValueError(f"Module 2 record requires a non-empty {name}")
        canonicalize_url(str(copied["discovery_endpoint"]))
        check = copied.get("endpoint_check")
        if not isinstance(check, Mapping):
            raise ValueError("Module 2 record requires an endpoint_check object")
        if not str(check.get("check_result", "")).strip():
            raise ValueError("endpoint_check requires check_result")
        object.__setattr__(self, "data", copied)

    @property
    def provider_id(self) -> str:
        return str(self.data["provider_id"])

    @property
    def name(self) -> str:
        return str(self.data["name"])

    @property
    def discovery_endpoint(self) -> str:
        return str(self.data["discovery_endpoint"])

    @property
    def endpoint_check(self) -> Mapping[str, Any]:
        return self.data["endpoint_check"]  # type: ignore[return-value]

    @property
    def check_result(self) -> str:
        return str(self.endpoint_check["check_result"])

    @property
    def final_url(self) -> str:
        value = self.endpoint_check.get("final_url")
        return str(value) if value else self.discovery_endpoint

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(dict(self.data))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProviderInputRecord":
        if not isinstance(value, Mapping):
            raise ValueError("provider record must be a JSON object")
        return cls(value)


@dataclass(frozen=True)
class DiscoveryEvidence:
    """Provenance for one observation of a Manifest URL."""

    provider_id: str
    provider_name: str
    discovery_method: str
    source_url: str
    activity_type: Optional[str] = None
    activity_time: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ManifestFinding:
    """One Manifest URL observed through one provider and one method."""

    manifest_url: str
    evidence: DiscoveryEvidence

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifest_url", canonicalize_url(self.manifest_url))


@dataclass(frozen=True)
class ResolvedEndpoint:
    """A fetched URL confirmed as a machine-readable IIIF resource."""

    endpoint_url: str
    resource_type: str
    resolution_method: str
    source_url: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "endpoint_url", canonicalize_url(self.endpoint_url))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscoveryIssue:
    """A recoverable failure retained instead of silently dropping a provider."""

    url: str
    issue_type: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderDiscoveryResult:
    """All Module 3 observations for one provider."""

    provider: ProviderInputRecord
    status: str = "unresolved"
    manifests: list[ManifestFinding] = field(default_factory=list)
    resolved_endpoints: list[ResolvedEndpoint] = field(default_factory=list)
    issues: list[DiscoveryIssue] = field(default_factory=list)
    html_pages_visited: int = 0
    stream_pages_visited: int = 0
    collections_visited: int = 0
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = self.provider.to_dict()
        data["module_3_schema_version"] = MODULE_3_SCHEMA_VERSION
        data["resource_discovery"] = {
            "status": self.status,
            "manifest_count": len({item.manifest_url for item in self.manifests}),
            "resolved_endpoints": [item.to_dict() for item in self.resolved_endpoints],
            "issues": [item.to_dict() for item in self.issues],
            "html_pages_visited": self.html_pages_visited,
            "stream_pages_visited": self.stream_pages_visited,
            "collections_visited": self.collections_visited,
            "truncated": self.truncated,
        }
        return data


def manifest_record(manifest_url: str, evidence: list[DiscoveryEvidence]) -> dict[str, Any]:
    """Build one deduplicated Module 4 handoff record."""

    canonical = canonicalize_url(manifest_url)
    providers: dict[str, str] = {}
    evidence_rows: list[dict[str, Any]] = []
    seen_evidence: set[tuple[Any, ...]] = set()
    for item in evidence:
        providers[item.provider_id] = item.provider_name
        key = (
            item.provider_id,
            item.discovery_method,
            item.source_url,
            item.activity_type,
            item.activity_time,
        )
        if key not in seen_evidence:
            evidence_rows.append(item.to_dict())
            seen_evidence.add(key)
    return {
        "manifest_id": stable_manifest_id(canonical),
        "manifest_url": canonical,
        "resource_type": "Manifest",
        "providers": [
            {"provider_id": provider_id, "provider_name": providers[provider_id]}
            for provider_id in sorted(providers)
        ],
        "discovery_evidence": evidence_rows,
        "module_3_schema_version": MODULE_3_SCHEMA_VERSION,
    }

