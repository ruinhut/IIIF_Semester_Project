"""Module 6 input contract and Module 7 schema constants."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


RECORD_SCHEMA_VERSION = "iiif-time-atlas-record-0.1"
MEDIA_SCHEMA_VERSION = "iiif-time-atlas-media-0.1"
OCR_PROFILE_SCHEMA_VERSION = "iiif-ocr-profile-0.1"
REFERENCE_TEXT_SCHEMA_VERSION = "iiif-ocr-reference-0.1"


@dataclass(frozen=True)
class Module6Record:
    data: Mapping[str, Any]

    def __post_init__(self) -> None:
        copied = deepcopy(dict(self.data))
        if copied.get("module_6_schema_version") != "1.0":
            raise ValueError("Unsupported or missing module_6_schema_version")
        if not str(copied.get("manifest_id", "")).strip():
            raise ValueError("Module 6 record requires manifest_id")
        if not isinstance(copied.get("normalized_metadata"), Mapping):
            raise ValueError("Module 6 record requires normalized_metadata")
        object.__setattr__(self, "data", copied)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Module6Record":
        if not isinstance(value, Mapping):
            raise ValueError("Module 6 record must be a JSON object")
        return cls(value)
