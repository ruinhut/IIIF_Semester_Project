"""Data contracts for Module 2 inputs and Module 3 discovery outputs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Optional
from urllib.parse import urlsplit, urlunsplit


MODULE_3_SCHEMA_VERSION = "2.1"


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
    canonical = canonicalize_url(manifest_url)
    digest = sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"manifest-{digest}"


@dataclass(frozen=True)
class ProviderInputRecord:
    """One provider with every Module 2 endpoint check grouped together."""

    data: Mapping[str, Any]
    _routes: tuple[Mapping[str, Any], ...] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        copied = deepcopy(dict(self.data))
        for name in ("provider_id", "name"):
            if name not in copied or not str(copied[name]).strip():
                raise ValueError(f"Module 2 record requires a non-empty {name}")

        route_values = copied.get("endpoint_checks")
        if route_values is None:
            check = copied.get("endpoint_check")
            if not isinstance(check, Mapping):
                raise ValueError(
                    "Module 2 record requires endpoint_check or endpoint_checks"
                )
            candidate = copied.get("endpoint_candidate")
            if not isinstance(candidate, Mapping):
                endpoint = str(copied.get("discovery_endpoint", "")).strip()
                if not endpoint:
                    raise ValueError(
                        "Module 2 record requires a non-empty discovery_endpoint"
                    )
                candidate = {
                    "url": endpoint,
                    "endpoint_role": _role_from_type(
                        str(copied.get("discovery_type", "unknown"))
                    ),
                    "discovery_type": str(
                        copied.get("discovery_type", "unknown")
                    ),
                }
            route_values = [
                {
                    "endpoint_candidate": dict(candidate),
                    "endpoint_check": dict(check),
                }
            ]
        if not isinstance(route_values, list) or not route_values:
            raise ValueError("endpoint_checks must be a non-empty JSON array")

        routes: list[dict[str, Any]] = []
        for index, route in enumerate(route_values):
            if not isinstance(route, Mapping):
                raise ValueError(f"endpoint_checks[{index}] must be an object")
            candidate = route.get("endpoint_candidate")
            check = route.get("endpoint_check")
            if not isinstance(candidate, Mapping) or not isinstance(check, Mapping):
                raise ValueError(
                    f"endpoint_checks[{index}] requires endpoint_candidate and endpoint_check"
                )
            url = str(
                candidate.get(
                    "url", check.get("requested_url", "")
                )
            ).strip()
            canonicalize_url(url)
            if not str(check.get("check_result", "")).strip():
                raise ValueError(
                    f"endpoint_checks[{index}].endpoint_check requires check_result"
                )
            candidate_copy = deepcopy(dict(candidate))
            candidate_copy["url"] = url
            candidate_copy.setdefault("endpoint_role", "unclassified")
            candidate_copy.setdefault("discovery_type", "unknown")
            routes.append(
                {
                    "endpoint_candidate": candidate_copy,
                    "endpoint_check": deepcopy(dict(check)),
                }
            )

        first = routes[0]
        if not str(copied.get("discovery_endpoint", "")).strip():
            copied["discovery_endpoint"] = first["endpoint_candidate"]["url"]
        if not str(copied.get("discovery_type", "")).strip():
            copied["discovery_type"] = first["endpoint_candidate"].get(
                "discovery_type", "unknown"
            )
        object.__setattr__(self, "data", copied)
        object.__setattr__(self, "_routes", tuple(routes))

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
    def endpoint_routes(self) -> tuple[Mapping[str, Any], ...]:
        return self._routes

    @property
    def endpoint_check(self) -> Mapping[str, Any]:
        return self.endpoint_routes[0]["endpoint_check"]  # type: ignore[return-value]

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
    manifest_url: str
    evidence: DiscoveryEvidence

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "manifest_url", canonicalize_url(self.manifest_url)
        )


@dataclass(frozen=True)
class ResolvedEndpoint:
    endpoint_url: str
    resource_type: str
    resolution_method: str
    source_url: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "endpoint_url", canonicalize_url(self.endpoint_url)
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscoveryIssue:
    url: str
    issue_type: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderDiscoveryResult:
    """All Module 3 observations for one institution."""

    provider: ProviderInputRecord
    status: str = "unresolved"
    manifests: list[ManifestFinding] = field(default_factory=list)
    resolved_endpoints: list[ResolvedEndpoint] = field(default_factory=list)
    issues: list[DiscoveryIssue] = field(default_factory=list)
    html_pages_visited: int = 0
    stream_pages_visited: int = 0
    collections_visited: int = 0
    knowledge_application: list[Mapping[str, Any]] = field(default_factory=list)
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = self.provider.to_dict()
        data["module_3_schema_version"] = MODULE_3_SCHEMA_VERSION
        data["resource_discovery"] = {
            "status": self.status,
            "input_endpoint_count": len(self.provider.endpoint_routes),
            "manifest_count": len(
                {item.manifest_url for item in self.manifests}
            ),
            "resolved_endpoints": [
                item.to_dict() for item in self.resolved_endpoints
            ],
            "issues": [item.to_dict() for item in self.issues],
            "html_pages_visited": self.html_pages_visited,
            "stream_pages_visited": self.stream_pages_visited,
            "collections_visited": self.collections_visited,
            "knowledge_application": [
                deepcopy(dict(item)) for item in self.knowledge_application
            ],
            "truncated": self.truncated,
        }
        return data


def manifest_record(
    manifest_url: str, evidence: list[DiscoveryEvidence]
) -> dict[str, Any]:
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
            {
                "provider_id": provider_id,
                "provider_name": providers[provider_id],
            }
            for provider_id in sorted(providers)
        ],
        "discovery_evidence": evidence_rows,
        "module_3_schema_version": MODULE_3_SCHEMA_VERSION,
    }


def _role_from_type(discovery_type: str) -> str:
    value = discovery_type.casefold()
    if "orderedcollection" in value or "activity" in value:
        return "change_discovery"
    if value == "collection":
        return "presentation_collection"
    if value == "manifest":
        return "manifest"
    if "website" in value:
        return "institution_website"
    return "unclassified"
