"""Data contracts for Module 2 input records and endpoint-check results."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional
from urllib.parse import urlsplit


MODULE_2_SCHEMA_VERSION = "1.0"

CHECK_RESULTS = {
    "reachable_json",
    "reachable_non_json",
    "invalid_json",
    "response_too_large",
    "restricted",
    "temporary_failure",
    "unreachable",
}


def validate_http_url(value: str) -> str:
    """Require an absolute HTTP(S) URL without changing Module 1's value."""

    text = value.strip()
    parts = urlsplit(text)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise ValueError(f"Expected an absolute HTTP(S) URL, got: {value!r}")
    if parts.username or parts.password:
        raise ValueError("URLs containing credentials are not accepted")
    return text


@dataclass(frozen=True)
class ProviderInputRecord:
    """A validated Module 1 record preserved verbatim for downstream use."""

    data: Mapping[str, Any]

    def __post_init__(self) -> None:
        copied = deepcopy(dict(self.data))
        for field_name in ("provider_id", "name", "discovery_endpoint"):
            if field_name not in copied or not str(copied[field_name]).strip():
                raise ValueError(f"Module 1 record requires a non-empty {field_name}")
        validate_http_url(str(copied["discovery_endpoint"]))
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
    def discovery_type(self) -> str:
        return str(self.data.get("discovery_type", "unknown"))

    def to_dict(self) -> dict[str, Any]:
        """Return an independent JSON-compatible copy of the Module 1 record."""

        return deepcopy(dict(self.data))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProviderInputRecord":
        """Build a Module 2 input record from one decoded JSON object."""

        if not isinstance(value, Mapping):
            raise ValueError("provider record must be a JSON object")
        return cls(data=value)


@dataclass(frozen=True)
class RedirectHop:
    """One HTTP redirect observed while resolving an entry point."""

    from_url: str
    status_code: int
    to_url: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RedirectHop":
        return cls(
            from_url=str(value["from_url"]),
            status_code=int(value["status_code"]),
            to_url=str(value["to_url"]),
        )


@dataclass(frozen=True)
class EndpointCheck:
    """The complete observable result of checking one candidate entry point."""

    requested_url: str
    final_url: Optional[str]
    checked_at: str
    check_result: str
    status_code: Optional[int] = None
    redirect_chain: tuple[RedirectHop, ...] = field(default_factory=tuple)
    content_type: Optional[str] = None
    response_time_ms: int = 0
    response_bytes: int = 0
    body_truncated: bool = False
    json_parseable: Optional[bool] = None
    json_resource_type: Optional[str] = None
    attempt_count: int = 1
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        validate_http_url(self.requested_url)
        if self.final_url is not None:
            validate_http_url(self.final_url)
        if self.check_result not in CHECK_RESULTS:
            raise ValueError(f"Unknown check_result: {self.check_result}")
        if self.status_code is not None and not 100 <= self.status_code <= 599:
            raise ValueError("status_code must be a valid three-digit HTTP status")
        if self.response_time_ms < 0 or self.response_bytes < 0:
            raise ValueError("response measurements must be non-negative")
        if self.attempt_count < 1:
            raise ValueError("attempt_count must be positive")
        if self.json_parseable not in {None, True, False}:
            raise ValueError("json_parseable must be true, false, or null")
        if self.check_result == "reachable_json" and self.json_parseable is not True:
            raise ValueError("reachable_json requires json_parseable=true")
        if self.check_result == "invalid_json" and self.json_parseable is not False:
            raise ValueError("invalid_json requires json_parseable=false")

    def to_dict(self) -> dict[str, Any]:
        """Convert the check to a JSON-serializable dictionary."""

        return asdict(self)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EndpointCheck":
        """Reconstruct and validate a stored endpoint check."""

        redirects_value = value.get("redirect_chain", [])
        if not isinstance(redirects_value, list):
            raise ValueError("redirect_chain must be a JSON array")
        return cls(
            requested_url=str(value["requested_url"]),
            final_url=_optional_string(value.get("final_url")),
            checked_at=str(value["checked_at"]),
            check_result=str(value["check_result"]),
            status_code=_optional_int(value.get("status_code")),
            redirect_chain=tuple(RedirectHop.from_mapping(item) for item in redirects_value),
            content_type=_optional_string(value.get("content_type")),
            response_time_ms=int(value.get("response_time_ms", 0)),
            response_bytes=int(value.get("response_bytes", 0)),
            body_truncated=bool(value.get("body_truncated", False)),
            json_parseable=value.get("json_parseable"),
            json_resource_type=_optional_string(value.get("json_resource_type")),
            attempt_count=int(value.get("attempt_count", 1)),
            error_type=_optional_string(value.get("error_type")),
            error_message=_optional_string(value.get("error_message")),
        )


@dataclass(frozen=True)
class CheckedProviderRecord:
    """A Module 1 provider record plus the non-destructive Module 2 check."""

    provider: ProviderInputRecord
    endpoint_check: EndpointCheck
    module_2_schema_version: str = MODULE_2_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Preserve all Module 1 fields and append Module 2-owned fields."""

        data = self.provider.to_dict()
        data["endpoint_check"] = self.endpoint_check.to_dict()
        data["module_2_schema_version"] = self.module_2_schema_version
        return data

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CheckedProviderRecord":
        """Reconstruct a checked provider from one stored JSON object."""

        if not isinstance(value, Mapping):
            raise ValueError("checked provider record must be a JSON object")
        check_value = value.get("endpoint_check")
        if not isinstance(check_value, Mapping):
            raise ValueError("endpoint_check must be a JSON object")
        provider_value = dict(value)
        provider_value.pop("endpoint_check", None)
        version = str(provider_value.pop("module_2_schema_version", MODULE_2_SCHEMA_VERSION))
        return cls(
            provider=ProviderInputRecord.from_mapping(provider_value),
            endpoint_check=EndpointCheck.from_mapping(check_value),
            module_2_schema_version=version,
        )


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    return int(value)
