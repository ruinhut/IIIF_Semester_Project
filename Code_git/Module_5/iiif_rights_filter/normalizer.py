"""Normalize and classify Creative Commons, RightsStatements, and local terms."""

from __future__ import annotations

from html import unescape
import re
from typing import Optional
from urllib.parse import urlsplit

from .extractor import ExtractedEvidence
from .models import RightsEvidence


_URI_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_RIGHTS_ID_CASE = {
    "inc": "InC",
    "inc-ow-eu": "InC-OW-EU",
    "inc-ruu": "InC-RUU",
    "noc-cr": "NoC-CR",
    "noc-nc": "NoC-NC",
    "noc-oklr": "NoC-OKLR",
    "noc-us": "NoC-US",
    "cne": "CNE",
    "nkc": "NKC",
    "und": "UND",
}


def classify_evidence(value: ExtractedEvidence) -> RightsEvidence:
    """Normalize one extracted value and attach a conservative category."""

    normalized = normalize_rights_value(value.raw_value)
    category, rule = classify_normalized_value(normalized)
    return RightsEvidence(
        evidence_type=value.evidence_type,
        json_path=value.json_path,
        raw_value=value.raw_value,
        normalized_value=normalized,
        category=category,
        matched_rule=rule,
        decisive=value.decisive,
        resource_type=value.resource_type,
        resource_id=value.resource_id,
        source_label=value.source_label,
    )


def normalize_rights_value(value: str) -> str:
    """Canonicalize known rights URIs while retaining readable local statements."""

    text = unescape(str(value)).strip()
    embedded = _URI_RE.findall(text)
    if _looks_like_uri(text):
        uri = text.rstrip(".,;)")
        canonical = _canonical_known_uri(uri)
        if canonical:
            return canonical
        return _canonical_generic_uri(uri)
    if len(embedded) == 1:
        canonical = _canonical_known_uri(embedded[0].rstrip(".,;)") )
        if canonical:
            return canonical
    plain = _TAG_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", plain).strip()


def classify_normalized_value(value: str) -> tuple[str, str]:
    """Map a normalized value to a stable evidence category and rule ID."""

    lowered = value.casefold()
    cc_match = re.search(
        r"creativecommons\.org/(licenses|publicdomain)/([^/]+)/([0-9.]+)/?",
        lowered,
    )
    if cc_match:
        family, code, _version = cc_match.groups()
        if family == "publicdomain" and code in {"zero", "mark"}:
            return "public_domain", f"cc_{code}"
        if code in {"by", "by-sa"}:
            return "open_license", f"cc_{code}"
        return "noncommercial_or_limited", f"cc_{code}"

    rights_match = re.search(
        r"rightsstatements\.org/vocab/([^/]+)/([0-9.]+)/?", lowered
    )
    if rights_match:
        statement_id = rights_match.group(1)
        if statement_id.startswith("inc"):
            return "in_copyright", f"rightsstatements_{statement_id}"
        if statement_id == "nkc":
            return "no_known_copyright", "rightsstatements_nkc"
        if statement_id.startswith("noc"):
            return "noncommercial_or_limited", f"rightsstatements_{statement_id}"
        return "unknown", f"rightsstatements_{statement_id}"

    if re.search(r"\bcc\s*0\b|creative commons zero", lowered):
        return "public_domain", "text_cc0"
    if "public domain" in lowered:
        return "public_domain", "text_public_domain"
    if re.search(r"\bcc\s*by(?:\s|-)*sa\b", lowered):
        return "open_license", "text_cc_by_sa"
    if re.search(r"\bcc\s*by\b", lowered) and not re.search(
        r"\b(?:nc|nd)\b", lowered
    ):
        return "open_license", "text_cc_by"
    if re.search(r"\bcc\s*by(?:\s|-)*(?:nc|nd)", lowered):
        return "noncommercial_or_limited", "text_cc_limited"
    if "non-commercial" in lowered or "noncommercial" in lowered:
        return "noncommercial_or_limited", "text_noncommercial"
    if "no derivatives" in lowered or "no-derivatives" in lowered:
        return "noncommercial_or_limited", "text_no_derivatives"
    if (
        "no known copyright" in lowered
        or "no known restrictions on use" in lowered
        or "no known restrictions to use" in lowered
    ):
        return "no_known_copyright", "text_no_known_copyright"
    if "all rights reserved" in lowered or "in copyright" in lowered:
        return "in_copyright", "text_in_copyright"
    if _looks_like_uri(value):
        return "institutional_terms", "unrecognized_terms_uri"
    if value.strip():
        return "institutional_terms", "unrecognized_terms_text"
    return "unknown", "empty_value"


def _canonical_known_uri(value: str) -> Optional[str]:
    try:
        parts = urlsplit(value)
    except ValueError:
        return None
    host = (parts.hostname or "").casefold()
    segments = [segment for segment in parts.path.split("/") if segment]
    if host in {"creativecommons.org", "www.creativecommons.org"}:
        lowered = [segment.casefold() for segment in segments]
        if len(lowered) >= 3 and lowered[0] == "licenses":
            return f"https://creativecommons.org/licenses/{lowered[1]}/{lowered[2]}/"
        if len(lowered) >= 3 and lowered[0] == "publicdomain":
            return f"https://creativecommons.org/publicdomain/{lowered[1]}/{lowered[2]}/"
    if host in {"rightsstatements.org", "www.rightsstatements.org"}:
        lowered = [segment.casefold() for segment in segments]
        if len(lowered) >= 3 and lowered[0] in {"vocab", "page", "data"}:
            identifier = _RIGHTS_ID_CASE.get(lowered[1], segments[1])
            return f"https://rightsstatements.org/vocab/{identifier}/{segments[2]}/"
    return None


def _canonical_generic_uri(value: str) -> str:
    try:
        parts = urlsplit(value)
    except ValueError:
        return value.strip()
    if not parts.scheme or not parts.netloc:
        return value.strip()
    scheme = parts.scheme.casefold()
    host = (parts.hostname or "").casefold()
    if parts.port:
        host = f"{host}:{parts.port}"
    path = parts.path or "/"
    return f"{scheme}://{host}{path}"


def _looks_like_uri(value: str) -> bool:
    stripped = value.strip()
    return bool(re.fullmatch(r"https?://\S+", stripped, re.IGNORECASE))
