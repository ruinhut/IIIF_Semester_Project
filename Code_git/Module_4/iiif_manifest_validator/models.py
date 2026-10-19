"""Data contracts for Module 3 handoff records and Module 4 results."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Optional
from urllib.parse import urlsplit, urlunsplit


MODULE_4_SCHEMA_VERSION = "1.0"


def canonicalize_url(value: str, *, preserve_fragment: bool = False) -> str:
    """Normalize a transport URL, retaining fragments for logical Canvas IDs."""

    text = str(value).strip()
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
    return urlunsplit((parts.scheme.lower(), host, parts.path or "/", parts.query,
                       parts.fragment if preserve_fragment else ""))


def stable_manifest_id(manifest_url: str) -> str:
    canonical = canonicalize_url(manifest_url)
    digest = sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"manifest-{digest}"


@dataclass(frozen=True)
class ManifestInputRecord:
    """One deduplicated Manifest URL emitted by Module 3."""

    data: Mapping[str, Any]

    def __post_init__(self) -> None:
        copied = deepcopy(dict(self.data))
        manifest_url = canonicalize_url(str(copied.get("manifest_url", "")))
        manifest_id = str(copied.get("manifest_id", "")).strip()
        if not manifest_id:
            raise ValueError("Module 3 record requires a non-empty manifest_id")
        expected_id = stable_manifest_id(manifest_url)
        if manifest_id != expected_id:
            raise ValueError(
                f"manifest_id {manifest_id!r} does not match URL-derived ID {expected_id!r}"
            )
        resource_type = str(copied.get("resource_type", "Manifest"))
        if resource_type.casefold() != "manifest":
            raise ValueError("Module 3 handoff resource_type must be Manifest")
        providers = copied.get("providers", [])
        evidence = copied.get("discovery_evidence", [])
        if not isinstance(providers, list):
            raise ValueError("providers must be an array")
        if not isinstance(evidence, list):
            raise ValueError("discovery_evidence must be an array")
        copied["manifest_id"] = manifest_id
        copied["manifest_url"] = manifest_url
        copied["resource_type"] = "Manifest"
        copied.setdefault("providers", [])
        copied.setdefault("discovery_evidence", [])
        object.__setattr__(self, "data", copied)

    @property
    def manifest_id(self) -> str:
        return str(self.data["manifest_id"])

    @property
    def manifest_url(self) -> str:
        return str(self.data["manifest_url"])

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(dict(self.data))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ManifestInputRecord":
        if not isinstance(value, Mapping):
            raise ValueError("Manifest handoff record must be a JSON object")
        return cls(value)


@dataclass(frozen=True)
class ValidationIssue:
    """One structural problem or review reason."""

    code: str
    message: str
    severity: str = "error"
    path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CanvasResource:
    """One Canvas/body observation for OCR and media handoff."""

    canvas_index: int
    canvas_id: Optional[str]
    canvas_label: Optional[str]
    body_id: Optional[str]
    body_type: Optional[str]
    body_format: Optional[str]
    image_service_urls: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["image_service_urls"] = list(self.image_service_urls)
        return result


@dataclass
class ValidationResult:
    """Structural validation and media inventory for one JSON document."""

    status: str = "invalid"
    presentation_version: Optional[str] = None
    source_format: Optional[str] = None
    declared_id: Optional[str] = None
    declared_type: Optional[str] = None
    context_values: list[str] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    canvas_resources: list[CanvasResource] = field(default_factory=list)
    canvas_count: int = 0
    content_body_count: int = 0
    image_body_count: int = 0
    image_service_count: int = 0
    auxiliary_file_count: int = 0
    rights_values: list[str] = field(default_factory=list)

    def summary_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "presentation_version": self.presentation_version,
            "source_format": self.source_format,
            "declared_id": self.declared_id,
            "declared_type": self.declared_type,
            "context_values": list(self.context_values),
            "issues": [item.to_dict() for item in self.issues],
            "canvas_count": self.canvas_count,
            "content_body_count": self.content_body_count,
            "image_body_count": self.image_body_count,
            "image_service_count": self.image_service_count,
            "auxiliary_file_count": self.auxiliary_file_count,
            "rights_values": list(self.rights_values),
        }
