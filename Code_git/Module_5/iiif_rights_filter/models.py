"""Data contracts for Module 4 inputs, rights evidence, and policy results."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional


MODULE_5_SCHEMA_VERSION = "2.0"
RIGHTS_CATEGORIES = (
    "public_domain",
    "open_license",
    "noncommercial_or_limited",
    "in_copyright",
    "no_known_copyright",
    "institutional_terms",
    "unknown",
    "conflicting",
)
POLICY_DECISIONS = ("allow", "exclude")
RIGHTS_DISPLAY_LABELS = {
    "public_domain": {"en": "Public domain", "zh": "公共领域"},
    "open_license": {"en": "Open license", "zh": "开放许可"},
    "noncommercial_or_limited": {"en": "Restricted reuse", "zh": "限制性使用"},
    "in_copyright": {"en": "In copyright", "zh": "版权保护中"},
    "no_known_copyright": {"en": "No known copyright", "zh": "无已知版权限制"},
    "institutional_terms": {"en": "Institutional terms", "zh": "机构使用条款"},
    "unknown": {"en": "Unknown rights", "zh": "未知版权"},
    "conflicting": {"en": "Conflicting rights information", "zh": "版权信息冲突"},
}


@dataclass(frozen=True)
class Module4ManifestRecord:
    """One structurally valid Manifest record emitted by Module 4."""

    data: Mapping[str, Any]

    def __post_init__(self) -> None:
        copied = deepcopy(dict(self.data))
        manifest_id = str(copied.get("manifest_id", "")).strip()
        manifest_url = str(copied.get("manifest_url", "")).strip()
        if not manifest_id or not manifest_url:
            raise ValueError("Module 4 record requires manifest_id and manifest_url")
        if str(copied.get("module_4_schema_version", "")).strip() != "1.0":
            raise ValueError("Unsupported or missing module_4_schema_version")
        validation = copied.get("structural_validation")
        if not isinstance(validation, Mapping):
            raise ValueError("Module 4 record requires structural_validation")
        if str(validation.get("status", "")).casefold() != "valid":
            raise ValueError("Module 5 accepts only structurally valid Manifests")
        raw_manifest = copied.get("raw_manifest")
        if not isinstance(raw_manifest, Mapping):
            raise ValueError("Module 4 record requires raw_manifest metadata")
        raw_path = str(raw_manifest.get("raw_manifest_path", "")).strip()
        if not raw_path:
            raise ValueError("raw_manifest.raw_manifest_path is required")
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

    def provider_names(self) -> list[str]:
        return [
            str(item.get("provider_name", "")).strip()
            for item in self.data.get("providers", [])
            if isinstance(item, Mapping) and item.get("provider_name")
        ]

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(dict(self.data))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Module4ManifestRecord":
        if not isinstance(value, Mapping):
            raise ValueError("Module 4 handoff record must be a JSON object")
        return cls(value)


@dataclass(frozen=True)
class RightsEvidence:
    """One rights-related value and its exact location in a Manifest."""

    evidence_type: str
    json_path: str
    raw_value: str
    normalized_value: str
    category: str
    matched_rule: str
    decisive: bool
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    source_label: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RightsPolicy:
    """A versioned mapping from evidence categories to public-reuse decisions."""

    policy_version: str
    category_decisions: Mapping[str, str]
    description: str = ""

    def __post_init__(self) -> None:
        version = str(self.policy_version).strip()
        if not version:
            raise ValueError("policy_version cannot be empty")
        decisions = dict(self.category_decisions)
        missing = sorted(set(RIGHTS_CATEGORIES) - set(decisions))
        extra = sorted(set(decisions) - set(RIGHTS_CATEGORIES))
        if missing or extra:
            raise ValueError(
                f"Policy categories do not match the schema; missing={missing}, extra={extra}"
            )
        invalid = {
            category: decision
            for category, decision in decisions.items()
            if decision not in POLICY_DECISIONS
        }
        if invalid:
            raise ValueError(f"Invalid policy decisions: {invalid}")
        object.__setattr__(self, "policy_version", version)
        object.__setattr__(self, "category_decisions", decisions)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RightsPolicy":
        if not isinstance(value, Mapping):
            raise ValueError("Rights policy must be a JSON object")
        decisions = value.get("category_decisions")
        if not isinstance(decisions, Mapping):
            raise ValueError("category_decisions must be a JSON object")
        return cls(
            policy_version=str(value.get("policy_version", "")),
            description=str(value.get("description", "")),
            category_decisions={str(k): str(v) for k, v in decisions.items()},
        )


@dataclass
class RightsAssessment:
    """Rights result for one Manifest, including all retained evidence."""

    category: str
    decision: str
    policy_version: str
    policy_rule: str
    assessed_at: str
    evidence: list[RightsEvidence] = field(default_factory=list)
    effective_categories: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        public_reuse_eligible = self.decision == "allow"
        return {
            "category": self.category,
            "decision": self.decision,
            "decision_scope": "public_reuse",
            "research_status": "retained",
            "usage_permissions": {
                "retain_url_and_metadata": True,
                "academic_analysis": True,
                "public_distribution": public_reuse_eligible,
                "commercial_use": public_reuse_eligible,
            },
            "public_reuse_eligible": public_reuse_eligible,
            "display_label": dict(RIGHTS_DISPLAY_LABELS[self.category]),
            "policy_version": self.policy_version,
            "policy_rule": self.policy_rule,
            "assessed_at": self.assessed_at,
            "evidence_count": len(self.evidence),
            "decisive_evidence_count": sum(item.decisive for item in self.evidence),
            "effective_categories": list(self.effective_categories),
            "reason_codes": list(self.reason_codes),
            "evidence": [item.to_dict() for item in self.evidence],
        }
