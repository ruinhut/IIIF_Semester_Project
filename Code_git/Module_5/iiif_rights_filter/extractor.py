"""Extract rights evidence from all relevant levels of an IIIF Manifest."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional


RIGHTS_LABEL_TERMS = (
    "right",
    "rights",
    "copyright",
    "license",
    "licence",
    "usage",
    "reuse",
    "terms of use",
    "conditions of use",
    "conditions d'utilisation",
    "conditions d’utilisation",
)


@dataclass(frozen=True)
class ExtractedEvidence:
    """Unclassified evidence preserving its original value and JSON path."""

    evidence_type: str
    json_path: str
    raw_value: str
    decisive: bool
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    source_label: Optional[str] = None


def extract_rights_evidence(document: Any) -> list[ExtractedEvidence]:
    """Collect direct rights fields, rights metadata, and attribution notices."""

    if not isinstance(document, Mapping):
        raise ValueError("Manifest JSON root must be an object")

    output: list[ExtractedEvidence] = []
    stack: list[tuple[Any, str]] = [(document, "$")]
    while stack:
        value, path = stack.pop()
        if isinstance(value, Mapping):
            resource_type = _resource_type(value)
            resource_id = _resource_id(value)

            for field_name in ("rights", "license"):
                if field_name in value:
                    output.extend(
                        _make_evidence(
                            value[field_name],
                            evidence_type=field_name,
                            json_path=f"{path}.{field_name}",
                            decisive=True,
                            resource_type=resource_type,
                            resource_id=resource_id,
                        )
                    )

            if "requiredStatement" in value:
                output.extend(
                    _required_statement_evidence(
                        value["requiredStatement"],
                        f"{path}.requiredStatement",
                        resource_type,
                        resource_id,
                    )
                )

            if "attribution" in value:
                output.extend(
                    _make_evidence(
                        value["attribution"],
                        evidence_type="attribution",
                        json_path=f"{path}.attribution",
                        decisive=False,
                        resource_type=resource_type,
                        resource_id=resource_id,
                    )
                )

            if "metadata" in value:
                output.extend(
                    _metadata_evidence(
                        value["metadata"], path, resource_type, resource_id
                    )
                )

            ignored = {
                "rights",
                "license",
                "requiredStatement",
                "attribution",
                "metadata",
            }
            for key, child in reversed(list(value.items())):
                if key not in ignored and isinstance(child, (Mapping, list)):
                    stack.append((child, f"{path}.{key}"))
        elif isinstance(value, list):
            for index in range(len(value) - 1, -1, -1):
                child = value[index]
                if isinstance(child, (Mapping, list)):
                    stack.append((child, f"{path}[{index}]"))

    return _deduplicate(output)


def _required_statement_evidence(
    value: Any,
    path: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
) -> list[ExtractedEvidence]:
    if not isinstance(value, Mapping):
        return _make_evidence(
            value,
            evidence_type="required_statement",
            json_path=path,
            decisive=False,
            resource_type=resource_type,
            resource_id=resource_id,
        )
    labels = _text_values(value.get("label"))
    label = " | ".join(labels) or None
    decisive = _is_rights_label(label or "")
    return _make_evidence(
        value.get("value"),
        evidence_type="required_statement",
        json_path=f"{path}.value",
        decisive=decisive,
        resource_type=resource_type,
        resource_id=resource_id,
        source_label=label,
    )


def _metadata_evidence(
    value: Any,
    parent_path: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
) -> list[ExtractedEvidence]:
    output: list[ExtractedEvidence] = []
    if not isinstance(value, list):
        return output
    for index, entry in enumerate(value):
        if not isinstance(entry, Mapping):
            continue
        labels = _text_values(entry.get("label"))
        label = " | ".join(labels)
        if not _is_rights_label(label):
            continue
        output.extend(
            _make_evidence(
                entry.get("value"),
                evidence_type="metadata_rights",
                json_path=f"{parent_path}.metadata[{index}].value",
                decisive=True,
                resource_type=resource_type,
                resource_id=resource_id,
                source_label=label or None,
            )
        )
    return output


def _make_evidence(
    value: Any,
    *,
    evidence_type: str,
    json_path: str,
    decisive: bool,
    resource_type: Optional[str],
    resource_id: Optional[str],
    source_label: Optional[str] = None,
) -> list[ExtractedEvidence]:
    return [
        ExtractedEvidence(
            evidence_type=evidence_type,
            json_path=json_path,
            raw_value=text,
            decisive=decisive,
            resource_type=resource_type,
            resource_id=resource_id,
            source_label=source_label,
        )
        for text in _text_values(value)
        if text.strip()
    ]


def _text_values(value: Any) -> list[str]:
    """Flatten common IIIF link, language-map, and HTML text structures."""

    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, list):
        return [text for item in value for text in _text_values(item)]
    if isinstance(value, Mapping):
        identifier = value.get("id", value.get("@id"))
        if isinstance(identifier, str) and identifier.strip():
            return [identifier.strip()]
        output: list[str] = []
        for key, item in value.items():
            if key not in {
                "type",
                "@type",
                "format",
                "profile",
                "language",
                "@language",
                "@context",
            }:
                output.extend(_text_values(item))
        return output
    return []


def _is_rights_label(value: str) -> bool:
    lowered = value.casefold()
    return any(term in lowered for term in RIGHTS_LABEL_TERMS)


def _resource_type(value: Mapping[str, Any]) -> Optional[str]:
    candidate = value.get("type", value.get("@type"))
    if isinstance(candidate, list):
        candidate = candidate[0] if candidate else None
    return str(candidate).split(":")[-1] if candidate else None


def _resource_id(value: Mapping[str, Any]) -> Optional[str]:
    candidate = value.get("id", value.get("@id"))
    return str(candidate).strip() if candidate else None


def _deduplicate(values: Iterable[ExtractedEvidence]) -> list[ExtractedEvidence]:
    output: list[ExtractedEvidence] = []
    seen: set[tuple[str, str, str, bool]] = set()
    for value in values:
        key = (
            value.evidence_type,
            value.json_path,
            value.raw_value,
            value.decisive,
        )
        if key not in seen:
            seen.add(key)
            output.append(value)
    return output
