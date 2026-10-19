"""Load and match persistent provider-discovery knowledge."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


@dataclass(frozen=True)
class ProviderKnowledge:
    """A reviewed investigation plus executable discovery skills."""

    provider_id: Optional[str]
    provider_name: Optional[str]
    investigation_id: str
    investigation_document: Optional[str]
    skills: tuple[Mapping[str, Any], ...]


def read_knowledge_base(path: Path) -> list[ProviderKnowledge]:
    """Read the versioned machine-readable knowledge base."""

    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read discovery knowledge base {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise ValueError("discovery knowledge base must be a JSON object")
    if str(value.get("knowledge_base_version", "")).strip() != "1.0":
        raise ValueError("discovery knowledge base requires version 1.0")
    providers = value.get("providers")
    if not isinstance(providers, list):
        raise ValueError("discovery knowledge base must contain a providers array")

    output: list[ProviderKnowledge] = []
    for index, item in enumerate(providers):
        if not isinstance(item, Mapping):
            raise ValueError(f"knowledge providers[{index}] must be an object")
        provider_id = _optional_string(item.get("provider_id"))
        provider_name = _optional_string(item.get("provider_name"))
        if not provider_id and not provider_name:
            raise ValueError(
                f"knowledge providers[{index}] needs provider_id or provider_name"
            )
        investigation_id = str(item.get("investigation_id", "")).strip()
        if not investigation_id:
            raise ValueError(
                f"knowledge providers[{index}] needs investigation_id"
            )
        raw_skills = item.get("skills")
        if not isinstance(raw_skills, list) or not raw_skills:
            raise ValueError(
                f"knowledge providers[{index}] needs a non-empty skills array"
            )
        skills: list[Mapping[str, Any]] = []
        for skill_index, skill in enumerate(raw_skills):
            if not isinstance(skill, Mapping):
                raise ValueError(
                    f"knowledge providers[{index}].skills[{skill_index}] must be an object"
                )
            skills.append(dict(skill))
        output.append(
            ProviderKnowledge(
                provider_id=provider_id,
                provider_name=provider_name,
                investigation_id=investigation_id,
                investigation_document=_optional_string(
                    item.get("investigation_document")
                ),
                skills=tuple(skills),
            )
        )
    return output


def knowledge_for_provider(
    provider_id: str,
    provider_name: str,
    entries: Sequence[ProviderKnowledge],
) -> Optional[ProviderKnowledge]:
    """Match by stable provider ID first, then exact case-insensitive name."""

    for entry in entries:
        if entry.provider_id and entry.provider_id == provider_id:
            return entry
    folded_name = provider_name.casefold()
    for entry in entries:
        if entry.provider_name and entry.provider_name.casefold() == folded_name:
            return entry
    return None


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
