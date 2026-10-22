"""Data contracts for Module 5 research inputs and Module 6 outputs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping


MODULE_6_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class Module5ResearchRecord:
    """One research-retained Manifest emitted by Module 5 schema 2.0."""

    data: Mapping[str, Any]

    def __post_init__(self) -> None:
        copied = deepcopy(dict(self.data))
        for name in ("manifest_id", "manifest_url"):
            if not str(copied.get(name, "")).strip():
                raise ValueError(f"Module 5 record requires {name}")
        if str(copied.get("module_5_schema_version", "")) != "2.0":
            raise ValueError("Unsupported or missing module_5_schema_version")
        assessment = copied.get("rights_assessment")
        if not isinstance(assessment, Mapping):
            raise ValueError("Module 5 record requires rights_assessment")
        if assessment.get("research_status") != "retained":
            raise ValueError("Module 6 accepts only research-retained Module 5 records")
        usage = assessment.get("usage_permissions")
        if not isinstance(usage, Mapping):
            raise ValueError("Module 5 record requires usage_permissions")
        if usage.get("retain_url_and_metadata") is not True:
            raise ValueError("Module 5 record does not permit URL/metadata retention")
        if usage.get("academic_analysis") is not True:
            raise ValueError("Module 5 record does not permit academic analysis")
        raw = copied.get("raw_manifest")
        if not isinstance(raw, Mapping) or not str(
            raw.get("raw_manifest_path", "")
        ).strip():
            raise ValueError("Module 5 record requires raw Manifest metadata")
        object.__setattr__(self, "data", copied)

    @property
    def manifest_id(self) -> str:
        return str(self.data["manifest_id"])

    @property
    def manifest_url(self) -> str:
        return str(self.data["manifest_url"])

    @property
    def raw_manifest_path(self) -> str:
        return str(self.data["raw_manifest"]["raw_manifest_path"])

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Module5ResearchRecord":
        if not isinstance(value, Mapping):
            raise ValueError("Module 5 handoff record must be a JSON object")
        return cls(value)


def stable_resource_id(resource: Mapping[str, Any]) -> str:
    """Create a stable ID for one Manifest/Canvas/body observation."""

    parts = [
        str(resource.get("manifest_id", "")),
        str(resource.get("canvas_index", "")),
        str(resource.get("canvas_id", "")),
        str(resource.get("body_id", "")),
        "|".join(str(item) for item in resource.get("image_service_urls", [])),
    ]
    digest = sha256("\n".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"resource-{digest}"
