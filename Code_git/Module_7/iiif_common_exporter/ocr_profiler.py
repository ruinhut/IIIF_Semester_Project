"""Build metadata-grounded OCR profiles and representative page candidates."""

from __future__ import annotations

from collections import Counter, defaultdict
import re
import unicodedata
from typing import Any, Iterable, Mapping

from .models import OCR_PROFILE_SCHEMA_VERSION

_CONTROLLED_SCRIPT_LABELS = ("script", "script type")
_DESCRIPTIVE_SCRIPT_LABELS = ("hand", "hands", "hand(s)")
_SCRIPT_PATTERNS = (
    ("Ashkenazic square script", ("ashkenazic square",)),
    ("Sefardi semi-cursive script", ("sefardi semi-cursive",)),
    ("Northern Textualis", ("northern textualis",)),
    ("Gothic script", ("gothic script",)),
    ("Cursiva", ("cursiva",)),
    ("Nasta'liq", ("nasta",)),
    ("Maghribi", ("maghrib",)),
    ("Naskh", ("naskh",)),
    ("Anglicana formata", ("anglicana formata",)),
    ("Italian textura formata", ("italian textura",)),
    ("French textura", ("french textura",)),
    ("Italian semi-cursive script", ("italian semi-cursive",)),
    ("Italian cursive script", ("italian cursive",)),
    ("Oriental semi-cursive script", ("oriental semi-cursive",)),
    ("Littera rotunda", ("littera rotunda",)),
    ("Carolingian minuscule", ("carolingian minuscule", "caroline script")),
    ("Continental uncial", ("continental uncial",)),
    ("Cursive majuscule", ("cursive majuscule",)),
    ("Devanagari", ("devanagari",)),
)
_HANDWRITTEN_TERMS = (
    "handwritten", "manuscript", "manuscrit", "handschrift", "autograph",
    "cursiva", "textualis", "caroline", "uncial", "minuscule",
    "majuscule", "secretary hand", "book hand", "documentary hand",
)
_PRINTED_TERMS = (
    "printed", "print", "imprime", "imprimé", "druck", "typograph",
    "newspaper", "periodical", "incunabul", "broadside",
)
_VISUAL_TERMS = (
    "painting", "sculpture", "photograph", "drawing", "coin", "medal",
    "ceramic", "artwork",
)
_TYPEFACE_FEATURES = {
    "fraktur": ("fraktur",),
    "blackletter": ("blackletter", "black letter", "gothic type"),
    "long_s": ("long s", "long-s", "long ſ"),
    "ligatures": ("ligature", "ligatures"),
}
_SCAN_FLAGS = (
    "microfilm", "bleed_through", "damaged_pages", "blur", "skew",
    "low_contrast",
)
_ADMINISTRATIVE_DATE_TERMS = (
    "record created", "record modified", "online since", "digitized",
    "digitised", "date added", "last updated", "harvested",
)
_NON_OBJECT_PRODUCTION_LABEL_TERMS = (
    "provenance", "record origin", "collection", "bibliography",
    "reference", "catalogue", "catalog",
)
_LANGUAGE_ALIASES = {
    "english": "en", "eng": "en", "english, middle (1100-1500)": "enm",
    "french": "fr", "french, middle (ca. 1400-1600)": "frm",
    "anglo-norman": "xno", "german": "de", "deutsch": "de",
    "italian": "it", "spanish": "es", "dutch": "nl",
    "middle dutch": "dum", "latin": "la", "latein": "la",
    "greek": "el", "arabic": "ar", "hebrew": "he",
    "judeo-arabic": "jrb", "persian": "fa", "sanskrit": "sa",
    "korean": "ko", "chinese": "zh", "nahuatl languages": "nah",
    "no linguistic content": "zxx",
}


def build_ocr_profile(
    source_record: Mapping[str, Any],
    common_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Create one conservative OCR profile from normalized and raw metadata."""

    obj = common_record["object"]
    source = common_record["source"]
    entries = _metadata_evidence(source_record.get("raw_metadata", []))
    searchable = _searchable_evidence(entries, obj)
    scripts = _script_values(entries)
    production = _production_method(searchable)
    typeface_features = _reported_typeface_features(searchable)
    date_profile = _date_profile(obj.get("dates", []))
    languages = _language_values(source_record, obj)

    return {
        "schema_version": OCR_PROFILE_SCHEMA_VERSION,
        "record_id": common_record["record_id"],
        "manifest_url": source["manifest_url"],
        "provider_names": [
            item.get("provider_name")
            for item in source.get("providers", [])
            if item.get("provider_name")
        ],
        "title": obj.get("title"),
        "languages": languages,
        "date_profile": date_profile,
        "scripts": scripts,
        "document_types": [
            {
                "value": item.get("value"),
                "source_label": item.get("source_label"),
            }
            for item in obj.get("types", [])
            if item.get("value")
        ],
        "production_method": production,
        "historical_typography": {
            "assessment_status": "metadata_only",
            "reported_features": typeface_features,
            "note": (
                "Features are reported only when explicit metadata evidence is "
                "present. An empty list does not mean that the feature is absent."
            ),
        },
        "scan_quality": {
            "assessment_status": "not_assessed_no_image_pixels",
            "flags": {name: "unknown" for name in _SCAN_FLAGS},
            "note": (
                "Module 7 receives image references, not decoded image pixels; "
                "microfilm, bleed-through, damage, blur, skew and contrast require "
                "image sampling or downstream inspection."
            ),
        },
        "media_count": common_record["media_count"],
        "metadata_coverage": {
            "language_reported": bool(languages),
            "date_normalized": date_profile["start_year"] is not None,
            "script_reported": bool(scripts),
            "production_method_classified": production["category"] != "unknown",
            "scan_quality_assessed": False,
        },
        "rights": {
            "research_status": common_record["rights"].get("research_status"),
            "academic_analysis_allowed": bool(
                common_record["rights"]
                .get("usage_permissions", {})
                .get("academic_analysis", False)
            ),
            "public_reuse_eligible": bool(
                common_record["rights"].get("public_reuse_eligible", False)
            ),
        },
    }


def summarize_ocr_profiles(
    profiles: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate the per-record profiles with explicit counting definitions."""

    rows = list(profiles)
    language_records: Counter[str] = Counter()
    language_media: Counter[str] = Counter()
    century_records: Counter[str] = Counter()
    century_media: Counter[str] = Counter()
    script_records: Counter[str] = Counter()
    production_records: Counter[str] = Counter()
    provider_records: Counter[str] = Counter()
    typography_records: Counter[str] = Counter()
    coverage: Counter[str] = Counter()
    start_years: list[int] = []
    end_years: list[int] = []

    for row in rows:
        media_count = int(row.get("media_count", 0))
        language_keys = {
            str(item.get("code") or item.get("raw") or "unknown").strip()
            for item in row.get("languages", [])
            if str(item.get("code") or item.get("raw") or "").strip()
        } or {"unknown"}
        for key in language_keys:
            language_records[key] += 1
            language_media[key] += media_count

        date = row.get("date_profile", {})
        start, end = date.get("start_year"), date.get("end_year")
        if isinstance(start, int):
            start_years.append(start)
        if isinstance(end, int):
            end_years.append(end)
        century = str(date.get("primary_century_label") or "unknown")
        century_records[century] += 1
        century_media[century] += media_count

        scripts = {
            str(item.get("value", "")).strip()
            for item in row.get("scripts", [])
            if str(item.get("value", "")).strip()
        } or {"unknown"}
        script_records.update(scripts)
        production_records[str(
            row.get("production_method", {}).get("category", "unknown")
        )] += 1
        provider_records.update(set(row.get("provider_names", [])) or {"unknown"})
        typography_records.update(
            set(row.get("historical_typography", {}).get(
                "reported_features", []
            ))
        )
        for key, present in row.get("metadata_coverage", {}).items():
            if present:
                coverage[key] += 1

    return {
        "schema_version": OCR_PROFILE_SCHEMA_VERSION,
        "record_count": len(rows),
        "media_count": sum(int(row.get("media_count", 0)) for row in rows),
        "date_range": {
            "earliest_year": min(start_years) if start_years else None,
            "latest_year": max(end_years) if end_years else None,
        },
        "language_distribution": {
            "record_counts": _counter_dict(language_records),
            "media_weighted_counts": _counter_dict(language_media),
            "definition": (
                "A multilingual record contributes once to each reported language; "
                "media-weighted counts use that record's media_count."
            ),
        },
        "primary_century_distribution": {
            "record_counts": _counter_dict(century_records),
            "media_weighted_counts": _counter_dict(century_media),
            "definition": "Primary century is derived from the midpoint of the normalized date range.",
        },
        "script_distribution": {
            "record_counts": _counter_dict(script_records),
            "definition": "Only explicit script-labelled metadata is counted.",
        },
        "production_method_distribution": {
            "record_counts": _counter_dict(production_records),
            "definition": "Metadata-based classification: printed, handwritten, mixed, visual_or_non_textual, or unknown.",
        },
        "reported_historical_typography": {
            "record_counts": _counter_dict(typography_records),
            "definition": "Explicit metadata mentions only; absence is not evidence that a feature is absent.",
        },
        "provider_distribution": {
            "record_counts": _counter_dict(provider_records),
        },
        "metadata_coverage": {
            key: {"count": coverage[key], "rate": _rate(coverage[key], len(rows))}
            for key in (
                "language_reported", "date_normalized", "script_reported",
                "production_method_classified", "scan_quality_assessed",
            )
        },
        "scan_quality": {
            "assessed_records": coverage["scan_quality_assessed"],
            "unassessed_records": len(rows) - coverage["scan_quality_assessed"],
            "reason": "Image pixels are not analyzed by the current Module 7 run.",
        },
        "limitations": [
            "Language, script and production method depend on provider-supplied metadata and may be missing.",
            "Fraktur, long s and ligatures are not marked absent unless image inspection has been performed.",
            "Microfilm, bleed-through, damage, blur, skew and contrast require pixel-level assessment.",
            "Counts describe the bounded harvested sample, not complete institutional collections.",
        ],
    }


def select_ground_truth_candidates(
    profiles: Iterable[Mapping[str, Any]],
    media_rows: Iterable[Mapping[str, Any]],
    *,
    max_records: int = 24,
    pages_per_record: int = 3,
    max_records_per_provider: int = 4,
) -> list[dict[str, Any]]:
    """Select a deterministic, diversity-oriented set of page candidates."""

    if max_records < 0 or pages_per_record < 1 or max_records_per_provider < 1:
        raise ValueError(
            "max_records must be non-negative; page and provider limits must be positive"
        )
    media_by_record: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for media in media_rows:
        media_by_record[str(media.get("record_id", ""))].append(media)
    for values in media_by_record.values():
        values.sort(key=lambda item: (int(item.get("sequence", 0)), str(item.get("resource_id", ""))))

    remaining = [
        row for row in profiles
        if media_by_record.get(str(row.get("record_id", "")))
    ]
    remaining.sort(key=lambda item: str(item.get("record_id", "")))
    selected: list[Mapping[str, Any]] = []
    covered: set[str] = set()
    provider_counts: Counter[str] = Counter()
    while remaining and len(selected) < max_records:
        eligible = [
            row for row in remaining
            if provider_counts[_primary_provider(row)] < max_records_per_provider
        ]
        if not eligible:
            break
        ranked = sorted(
            eligible,
            key=lambda row: (
                -sum(
                    _facet_weight(facet)
                    for facet in _profile_facets(row)
                    if facet not in covered
                ),
                str(row.get("record_id", "")),
            ),
        )
        chosen = ranked[0]
        selected.append(chosen)
        covered.update(_profile_facets(chosen))
        provider_counts[_primary_provider(chosen)] += 1
        remaining.remove(chosen)

    output: list[dict[str, Any]] = []
    for profile in selected:
        record_id = str(profile["record_id"])
        media = media_by_record[record_id]
        facets = sorted(_profile_facets(profile))
        production_category = str(
            profile.get("production_method", {}).get("category", "unknown")
        )
        candidate_status = (
            "metadata_supported_ocr_candidate"
            if production_category in {"printed", "handwritten", "mixed"}
            else "visual_triage_required"
        )
        for media_row in _evenly_spaced(media, pages_per_record):
            output.append({
                "candidate_id": f"ocr-candidate-{len(output) + 1:04d}",
                "record_id": record_id,
                "manifest_url": profile["manifest_url"],
                "provider_names": list(profile.get("provider_names", [])),
                "title": profile.get("title"),
                "languages": list(profile.get("languages", [])),
                "date_profile": dict(profile.get("date_profile", {})),
                "scripts": list(profile.get("scripts", [])),
                "production_method": dict(profile.get("production_method", {})),
                "reported_typeface_features": list(
                    profile.get("historical_typography", {}).get(
                        "reported_features", []
                    )
                ),
                "scan_quality_assessment_status": profile.get(
                    "scan_quality", {}
                ).get("assessment_status"),
                "candidate_status": candidate_status,
                "selection_facets": facets,
                "resource_id": media_row.get("resource_id"),
                "sequence": media_row.get("sequence"),
                "canvas_id": media_row.get("canvas", {}).get("id"),
                "canvas_label": media_row.get("canvas", {}).get("label"),
                "image_id": media_row.get("image", {}).get("id"),
                "image_source_id": media_row.get("image", {}).get("source_id"),
                "image_download_url": media_row.get("image", {}).get(
                    "download_url"
                ),
                "image_info_json_url": media_row.get("image", {}).get(
                    "info_json_url"
                ),
                "image_service_urls": list(
                    media_row.get("image", {}).get("service_urls", [])
                ),
                "rights": dict(media_row.get("rights", {})),
            })
    return output


def _metadata_evidence(value: Any) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    if not isinstance(value, list):
        return output
    for entry in value:
        if not isinstance(entry, Mapping):
            continue
        label = str(entry.get("label") or "").strip()
        for item in entry.get("values", []):
            if not isinstance(item, Mapping):
                continue
            text = str(item.get("value") or "").strip()
            if text:
                output.append({
                    "source_label": label,
                    "value": text,
                    "json_path": str(item.get("json_path") or entry.get("json_path") or ""),
                })
    return output


def _searchable_evidence(
    entries: list[dict[str, str]], obj: Mapping[str, Any]
) -> list[dict[str, str]]:
    output = list(entries)
    for item in obj.get("types", []):
        if isinstance(item, Mapping) and item.get("value"):
            output.append({
                "source_label": str(item.get("source_label") or "Normalized type"),
                "value": str(item["value"]),
                "json_path": str(item.get("json_path") or "$.object.types"),
            })
    return output


def _script_values(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in entries:
        label = _fold(item["source_label"])
        if label in _CONTROLLED_SCRIPT_LABELS:
            values = _extract_script_names(item["value"]) or [item["value"]]
        elif label in _DESCRIPTIVE_SCRIPT_LABELS:
            values = _extract_script_names(item["value"])
        else:
            values = []
        for value in values:
            key = _fold(value)
            if key and key not in seen:
                seen.add(key)
                output.append({
                    "source_label": item["source_label"],
                    "value": value,
                    "raw_value": item["value"],
                    "json_path": item["json_path"],
                })
    return output


def _extract_script_names(value: str) -> list[str]:
    """Map provider spelling variants to stable, human-readable labels."""

    folded_value = _fold(value)
    return [
        name for name, terms in _SCRIPT_PATTERNS
        if any(term in folded_value for term in terms)
    ]


def _language_values(
    source_record: Mapping[str, Any], obj: Mapping[str, Any]
) -> list[dict[str, Any]]:
    source_languages = source_record.get("normalized_metadata", {}).get(
        "languages", []
    )
    candidates = source_languages if isinstance(source_languages, list) else []
    if not candidates:
        candidates = obj.get("languages", [])
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidates:
        if not isinstance(item, Mapping):
            continue
        raw = str(item.get("value", item.get("raw", ""))).strip()
        code = str(item.get("code") or "").strip().casefold()
        if code == "eng":
            code = "en"
        if not code:
            code = _LANGUAGE_ALIASES.get(_fold(raw), "")
        key = code or _fold(raw)
        if not key or key in seen:
            continue
        seen.add(key)
        output.append({"raw": raw or None, "code": code or None})
    recognized = [item for item in output if item["code"]]
    return recognized or output


def _production_method(entries: list[dict[str, str]]) -> dict[str, Any]:
    object_evidence = [
        item for item in entries
        if not any(
            term in _fold(item["source_label"])
            for term in _NON_OBJECT_PRODUCTION_LABEL_TERMS
        )
    ]
    handwritten = _matching_evidence(object_evidence, _HANDWRITTEN_TERMS)
    printed = _matching_evidence(object_evidence, _PRINTED_TERMS)
    visual = _matching_evidence(object_evidence, _VISUAL_TERMS)
    if handwritten and printed:
        category = "mixed"
        evidence = handwritten + printed
    elif handwritten:
        category = "handwritten"
        evidence = handwritten
    elif printed:
        category = "printed"
        evidence = printed
    elif visual:
        category = "visual_or_non_textual"
        evidence = visual
    else:
        category = "unknown"
        evidence = []
    return {
        "category": category,
        "confidence": "metadata_inferred" if evidence else "unknown",
        "evidence": _deduplicate_evidence(evidence),
        "note": "Classification is based on metadata terms and has not been visually verified.",
    }


def _reported_typeface_features(entries: list[dict[str, str]]) -> list[str]:
    found: list[str] = []
    combined = "\n".join(
        f"{item['source_label']} {item['value']}" for item in entries
    )
    folded = _fold(combined)
    for feature, terms in _TYPEFACE_FEATURES.items():
        if any(_fold(term) in folded for term in terms):
            found.append(feature)
    return found


def _date_profile(values: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    original_rows = list(values)
    rows = [
        item for item in original_rows
        if not any(
            term in _fold(str(item.get("source_label") or ""))
            for term in _ADMINISTRATIVE_DATE_TERMS
        )
    ]
    starts = [item.get("start_year") for item in rows if isinstance(item.get("start_year"), int)]
    ends = [item.get("end_year") for item in rows if isinstance(item.get("end_year"), int)]
    start = min(starts) if starts else None
    end = max(ends) if ends else None
    centuries: list[int] = []
    if start is not None and end is not None and start > 0 and end > 0:
        centuries = list(range(_century(start), _century(end) + 1))
    midpoint = None if start is None or end is None else (start + end) // 2
    primary = _century(midpoint) if isinstance(midpoint, int) and midpoint > 0 else None
    return {
        "raw_values": [item.get("raw") for item in rows if item.get("raw")],
        "start_year": start,
        "end_year": end,
        "centuries": centuries,
        "century_labels": [_ordinal(value) for value in centuries],
        "primary_century": primary,
        "primary_century_label": _ordinal(primary) if primary else None,
    }


def _profile_facets(profile: Mapping[str, Any]) -> set[str]:
    facets = {
        f"production:{profile.get('production_method', {}).get('category', 'unknown')}",
        f"century:{profile.get('date_profile', {}).get('primary_century_label') or 'unknown'}",
    }
    facets.update(f"provider:{item}" for item in profile.get("provider_names", []))
    facets.update(
        f"language:{item.get('code') or item.get('raw') or 'unknown'}"
        for item in profile.get("languages", [])
    )
    facets.update(f"script:{item.get('value')}" for item in profile.get("scripts", []))
    facets.update(
        f"typeface:{item}"
        for item in profile.get("historical_typography", {}).get(
            "reported_features", []
        )
    )
    return facets


def _primary_provider(profile: Mapping[str, Any]) -> str:
    providers = profile.get("provider_names", [])
    return str(providers[0]) if providers else "unknown"


def _facet_weight(facet: str) -> int:
    if facet.startswith("provider:"):
        return 20
    if facet.startswith(("script:", "typeface:")):
        return 5
    if facet.startswith("production:"):
        return 4
    if facet.startswith("language:"):
        return 3
    return 2


def _evenly_spaced(values: list[Mapping[str, Any]], count: int) -> list[Mapping[str, Any]]:
    if len(values) <= count:
        return list(values)
    if count == 1:
        return [values[len(values) // 2]]
    indices = {
        round(index * (len(values) - 1) / (count - 1))
        for index in range(count)
    }
    return [values[index] for index in sorted(indices)]


def _matching_evidence(
    entries: list[dict[str, str]], terms: Iterable[str]
) -> list[dict[str, str]]:
    folded_terms = tuple(_fold(term) for term in terms)
    return [
        item for item in entries
        if any(term in _fold(f"{item['source_label']} {item['value']}") for term in folded_terms)
    ]


def _deduplicate_evidence(values: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for value in values:
        key = (
            str(value.get("source_label", "")),
            str(value.get("value", "")),
            str(value.get("json_path", "")),
        )
        if key not in seen:
            seen.add(key)
            output.append(dict(value))
    return output


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value)).casefold()
    return re.sub(r"\s+", " ", "".join(
        char for char in normalized if not unicodedata.combining(char)
    )).strip()


def _century(year: int) -> int:
    return (year - 1) // 100 + 1


def _ordinal(value: int) -> str:
    suffix = "th" if 10 <= value % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix} century"


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def _rate(count: int, total: int) -> float:
    return round(count / total * 100, 2) if total else 0.0
