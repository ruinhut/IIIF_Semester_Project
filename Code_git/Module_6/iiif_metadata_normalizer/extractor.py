"""Extract raw IIIF metadata and conservatively normalize core fields."""

from __future__ import annotations

from html import unescape
import re
import unicodedata
from typing import Any, Iterable, Mapping, Optional


_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_YEAR_RE = re.compile(r"(?<!\d)([+-]?\d{4})(?!\d)")
_ISO_DATE_RE = re.compile(
    r"^([+-]?\d{4})(?:-(\d{2})(?:-(\d{2}))?)?(?:T.*)?$"
)
_CENTURY_RE = re.compile(r"(?<!\d)(\d{1,2})(?:st|nd|rd|th)\s+century", re.I)

FIELD_TERMS = {
    "title": ("title", "titre", "titel", "name"),
    "description": ("description", "summary", "abstract", "note"),
    "creator": (
        "creator", "author", "artist", "maker", "contributor", "auteur", "k\u00fcnstler"
    ),
    "date": (
        "date", "year", "created", "creation", "issued", "publication",
        "century", "\u5e74\u4ee3", "\u65e5\u671f"
    ),
    "place": (
        "place", "location", "spatial", "geographic", "provenance",
        "lieu", "ort", "\u5730\u70b9"
    ),
    "subject": ("subject", "keyword", "topic", "th\u00e8me", "schlagwort", "\u4e3b\u9898"),
    "type": ("type", "genre", "material", "format"),
    "language": ("language", "langue", "sprache", "\u8bed\u8a00"),
    "identifier": (
        "identifier", "shelfmark", "call number", "inventory", "accession",
        "ark", "cote", "signatur", "fragmentarium id"
    ),
}

LANGUAGE_CODES = {
    "english": "en",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "spanish": "es",
    "dutch": "nl",
    "latin": "la",
    "greek": "el",
    "arabic": "ar",
    "chinese": "zh",
    "russian": "ru",
    "ukrainian": "uk",
    "yiddish": "yi",
    "hebrew": "he",
    "polish": "pl",
}


def extract_and_normalize(
    document: Mapping[str, Any],
    handoff: Mapping[str, Any],
    *,
    language_priority: list[str],
    normalized_at: str,
) -> dict[str, Any]:
    """Build a provider-independent metadata record from a Manifest."""

    if _resource_type(document).casefold() != "manifest":
        raise ValueError("Raw JSON is not an IIIF Manifest")

    raw_entries: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = {
        name: [] for name in FIELD_TERMS
    }
    for index, entry in enumerate(_as_list(document.get("metadata"))):
        if not isinstance(entry, Mapping):
            continue
        labels = text_values(entry.get("label"), f"$.metadata[{index}].label")
        values = text_values(entry.get("value"), f"$.metadata[{index}].value")
        label = _preferred_text(labels, language_priority)
        raw_entries.append(
            {
                "index": index,
                "label": label,
                "label_values": labels,
                "values": values,
                "json_path": f"$.metadata[{index}]",
            }
        )
        field = classify_label(label or "")
        if field:
            grouped[field].extend(
                _with_source_label(item, label) for item in values
            )

    title_values = text_values(document.get("label"), "$.label")
    title_values.extend(grouped["title"])
    description_key = "summary" if "summary" in document else "description"
    description_values = text_values(
        document.get(description_key), f"$.{description_key}"
    )
    description_values.extend(grouped["description"])

    declared_id = _resource_id(document) or str(handoff.get("manifest_url", ""))
    identifier_values = [
        {
            "value": declared_id,
            "language": None,
            "json_path": "$.id/@id",
            "source_label": "Manifest identifier",
            "scheme": "uri",
        }
    ]
    identifier_values.extend(
        {**item, "scheme": "metadata"} for item in grouped["identifier"]
    )

    date_values = [
        {**item, "normalization": normalize_date(item["value"])}
        for item in _deduplicate_texts(grouped["date"])
    ]
    place_values = [
        {**item, "normalized": normalize_place(item["value"])}
        for item in _deduplicate_texts(grouped["place"])
    ]
    language_values = [
        {**item, "code": normalize_language(item["value"])}
        for item in _deduplicate_texts(grouped["language"])
    ]

    providers = [
        {
            "provider_id": str(item.get("provider_id", "")),
            "provider_name": str(item.get("provider_name", "")),
        }
        for item in handoff.get("providers", [])
        if isinstance(item, Mapping)
    ]
    rights = dict(handoff.get("rights_assessment", {}))
    source = {
        "manifest_id": str(handoff.get("manifest_id", "")),
        "manifest_url": str(handoff.get("manifest_url", "")),
        "declared_manifest_id": declared_id,
        "presentation_version": handoff.get(
            "structural_validation", {}
        ).get("presentation_version"),
        "providers": providers,
        "discovery_evidence": list(handoff.get("discovery_evidence", [])),
    }
    normalized = {
        "identifier": {
            "primary": declared_id,
            "values": _deduplicate_by_value(identifier_values),
        },
        "title": text_field(title_values, language_priority),
        "description": text_field(description_values, language_priority),
        "creators": _deduplicate_texts(grouped["creator"]),
        "dates": date_values,
        "places": place_values,
        "subjects": _deduplicate_texts(grouped["subject"]),
        "types": _deduplicate_texts(grouped["type"]),
        "languages": language_values,
        "rights": {
            "category": rights.get("category"),
            "decision": rights.get("decision"),
            "decision_scope": rights.get("decision_scope"),
            "research_status": rights.get("research_status"),
            "usage_permissions": dict(rights.get("usage_permissions", {})),
            "public_reuse_eligible": bool(
                rights.get("public_reuse_eligible", False)
            ),
            "display_label": dict(rights.get("display_label", {})),
            "policy_version": rights.get("policy_version"),
            "evidence": list(rights.get("evidence", [])),
        },
        "source": source,
    }

    missing_fields: list[str] = []
    warnings: list[str] = []
    if not normalized["identifier"]["primary"]:
        missing_fields.append("identifier")
    if not date_values:
        missing_fields.append("date")
    elif not any(item["normalization"]["normalized"] for item in date_values):
        warnings.append("date_present_but_not_normalized")
    if not any(item["normalized"] for item in place_values):
        missing_fields.append("place")
    if rights.get("decision") != "allow":
        missing_fields.append("rights")
    if not source["manifest_url"] or not providers:
        missing_fields.append("source")
    if not normalized["title"]["preferred"]:
        warnings.append("title_missing")

    return {
        "manifest_id": str(handoff["manifest_id"]),
        "manifest_url": str(handoff["manifest_url"]),
        "resource_type": "Manifest",
        "presentation_version": source["presentation_version"],
        "normalized_metadata": normalized,
        "raw_metadata": raw_entries,
        "quality": {
            "status": "complete" if not missing_fields else "partial",
            "missing_fields": sorted(set(missing_fields)),
            "warnings": sorted(set(warnings)),
        },
        "normalization": {
            "normalized_at": normalized_at,
            "language_priority": list(language_priority),
        },
        "pipeline_versions": {
            "module_3": handoff.get("module_3_schema_version"),
            "module_4": handoff.get("module_4_schema_version"),
            "module_5": handoff.get("module_5_schema_version"),
        },
    }


def text_values(value: Any, path: str) -> list[dict[str, Any]]:
    """Flatten IIIF 2 strings/value objects and IIIF 3 language maps."""

    output: list[dict[str, Any]] = []
    if value is None:
        return output
    if isinstance(value, str):
        cleaned = clean_text(value)
        return (
            [{"value": cleaned, "language": None, "json_path": path}]
            if cleaned
            else []
        )
    if isinstance(value, (int, float, bool)):
        return [{"value": str(value), "language": None, "json_path": path}]
    if isinstance(value, list):
        for index, item in enumerate(value):
            output.extend(text_values(item, f"{path}[{index}]"))
        return output
    if not isinstance(value, Mapping):
        return output
    if "@value" in value:
        cleaned = clean_text(str(value.get("@value", "")))
        return (
            [
                {
                    "value": cleaned,
                    "language": _optional_text(value.get("@language")),
                    "json_path": path,
                }
            ]
            if cleaned
            else []
        )
    identifier = value.get("id", value.get("@id"))
    if isinstance(identifier, str) and identifier.strip():
        return [
            {
                "value": identifier.strip(),
                "language": None,
                "json_path": path,
            }
        ]

    ignored = {"type", "@type", "format", "profile", "@context", "language"}
    for key, item in value.items():
        if key in ignored:
            continue
        if key == "value":
            output.extend(text_values(item, f"{path}.value"))
            continue
        language = key if _looks_like_language_key(key) else None
        nested = text_values(item, f"{path}.{key}")
        if language:
            nested = [
                {**entry, "language": entry.get("language") or language}
                for entry in nested
            ]
        output.extend(nested)
    return output


def text_field(
    values: Iterable[Mapping[str, Any]], language_priority: list[str]
) -> dict[str, Any]:
    deduplicated = _deduplicate_texts(values)
    return {
        "preferred": _preferred_text(deduplicated, language_priority),
        "values": deduplicated,
    }


def classify_label(label: str) -> Optional[str]:
    normalized = _normalized_label(label)
    for field, terms in FIELD_TERMS.items():
        if any(term in normalized for term in terms):
            return field
    return None


def normalize_date(value: str) -> dict[str, Any]:
    """Normalize only explicit ISO-like dates, years, ranges, and centuries."""

    text = clean_text(value)
    lowered = text.casefold()
    approximate = any(
        token in lowered for token in ("circa", "ca.", "c.", "approx")
    )
    iso = _ISO_DATE_RE.fullmatch(text)
    if iso:
        year = int(iso.group(1))
        month = int(iso.group(2)) if iso.group(2) else None
        day = int(iso.group(3)) if iso.group(3) else None
        normalized = f"{year:04d}"
        precision = "year"
        if month is not None:
            normalized += f"-{month:02d}"
            precision = "month"
        if day is not None:
            normalized += f"-{day:02d}"
            precision = "day"
        return {
            "normalized": normalized,
            "start_year": year,
            "end_year": year,
            "precision": precision,
            "approximate": approximate,
        }

    years = [int(item) for item in _YEAR_RE.findall(text)]
    if len(years) >= 2:
        start, end = years[0], years[1]
        if start > end:
            start, end = end, start
        return {
            "normalized": f"{start:04d}/{end:04d}",
            "start_year": start,
            "end_year": end,
            "precision": "year_range",
            "approximate": approximate,
        }
    if len(years) == 1:
        year = years[0]
        return {
            "normalized": f"{year:04d}",
            "start_year": year,
            "end_year": year,
            "precision": "year",
            "approximate": approximate,
        }

    century = _CENTURY_RE.search(text)
    if century:
        number = int(century.group(1))
        start, end = (number - 1) * 100 + 1, number * 100
        return {
            "normalized": f"{start:04d}/{end:04d}",
            "start_year": start,
            "end_year": end,
            "precision": "century",
            "approximate": True,
        }
    return {
        "normalized": None,
        "start_year": None,
        "end_year": None,
        "precision": "unparsed",
        "approximate": approximate,
    }


def normalize_place(value: str) -> Optional[str]:
    cleaned = clean_text(value)
    if cleaned.casefold() in {
        "",
        "unknown",
        "unk",
        "n/a",
        "not known",
        "not available",
        "none",
        "-",
    }:
        return None
    return cleaned


def normalize_language(value: str) -> Optional[str]:
    cleaned = clean_text(value).casefold()
    if cleaned in LANGUAGE_CODES:
        return LANGUAGE_CODES[cleaned]
    return cleaned if re.fullmatch(r"[a-z]{2,3}", cleaned) else None


def clean_text(value: str) -> str:
    return _SPACE_RE.sub(" ", _TAG_RE.sub(" ", unescape(str(value)))).strip()


def _preferred_text(
    values: list[Mapping[str, Any]], language_priority: list[str]
) -> Optional[str]:
    if not values:
        return None
    for language in language_priority:
        for item in values:
            if (
                str(item.get("language") or "und").casefold()
                == language.casefold()
                and item.get("value")
            ):
                return str(item["value"])
    return str(values[0]["value"]) if values[0].get("value") else None


def _with_source_label(
    value: Mapping[str, Any], label: Optional[str]
) -> dict[str, Any]:
    return {**dict(value), "source_label": label}


def _deduplicate_texts(
    values: Iterable[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, Optional[str], Optional[str]]] = set()
    for item in values:
        text = clean_text(str(item.get("value", "")))
        if not text:
            continue
        key = (
            text.casefold(),
            _optional_text(item.get("language")),
            _optional_text(item.get("source_label")),
        )
        if key not in seen:
            row = dict(item)
            row["value"] = text
            output.append(row)
            seen.add(key)
    return output


def _deduplicate_by_value(
    values: Iterable[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in values:
        key = str(item.get("value", "")).strip().casefold()
        if key and key not in seen:
            output.append(dict(item))
            seen.add(key)
    return output


def _normalized_label(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return _SPACE_RE.sub(" ", without_marks).strip()


def _looks_like_language_key(value: str) -> bool:
    return value == "none" or bool(
        re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]+)*", value)
    )


def _optional_text(value: Any) -> Optional[str]:
    text = str(value).strip() if value is not None else ""
    return text or None


def _resource_type(value: Mapping[str, Any]) -> str:
    candidate = value.get("type", value.get("@type", ""))
    if isinstance(candidate, list):
        candidate = candidate[0] if candidate else ""
    return str(candidate).split(":")[-1]


def _resource_id(value: Mapping[str, Any]) -> Optional[str]:
    candidate = value.get("id", value.get("@id"))
    return str(candidate).strip() if candidate else None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]
