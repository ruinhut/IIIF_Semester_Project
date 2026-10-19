"""Extract institution-provided OCR or transcription links from IIIF Manifests."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Iterable, Mapping

from .extractor import clean_text, text_values


def extract_reference_text_resources(
    document: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return page- or Manifest-aligned text resources declared by a provider.

    The function records provider declarations only.  It does not treat ordinary
    descriptive metadata as OCR and it does not claim that institutional OCR is
    manually corrected ground truth.
    """

    manifest_id = str(handoff.get("manifest_id", ""))
    manifest_url = str(handoff.get("manifest_url", ""))
    providers = [
        {
            "provider_id": str(item.get("provider_id", "")),
            "provider_name": str(item.get("provider_name", "")),
        }
        for item in handoff.get("providers", [])
        if isinstance(item, Mapping)
    ]
    rights = handoff.get("rights_assessment", {})
    output: list[dict[str, Any]] = []

    # IIIF Presentation 2 canvases.
    for sequence in _as_list(document.get("sequences")):
        if not isinstance(sequence, Mapping):
            continue
        for canvas_index, canvas in enumerate(_as_list(sequence.get("canvases"))):
            if not isinstance(canvas, Mapping):
                continue
            output.extend(_from_see_also(
                canvas.get("seeAlso"),
                manifest_id=manifest_id,
                manifest_url=manifest_url,
                providers=providers,
                rights=rights,
                canvas_index=canvas_index,
                canvas_id=_identifier(canvas),
                canvas_label=_label(canvas.get("label")),
                source_kind="canvas_seeAlso",
                alignment_scope="canvas",
            ))

    # IIIF Presentation 3 canvases and supplementing AnnotationPages.
    for canvas_index, canvas in enumerate(_as_list(document.get("items"))):
        if not isinstance(canvas, Mapping) or _resource_type(canvas) != "canvas":
            continue
        canvas_id = _identifier(canvas)
        canvas_label = _label(canvas.get("label"))
        output.extend(_from_see_also(
            canvas.get("seeAlso"),
            manifest_id=manifest_id,
            manifest_url=manifest_url,
            providers=providers,
            rights=rights,
            canvas_index=canvas_index,
            canvas_id=canvas_id,
            canvas_label=canvas_label,
            source_kind="canvas_seeAlso",
            alignment_scope="canvas",
        ))
        for page in _as_list(canvas.get("annotations")):
            if not isinstance(page, Mapping):
                continue
            for annotation in _as_list(page.get("items")):
                if not isinstance(annotation, Mapping):
                    continue
                purposes = {
                    str(value).casefold()
                    for value in _as_list(
                        annotation.get("motivation", annotation.get("purpose"))
                    )
                }
                if purposes and not purposes.intersection(
                    {"supplementing", "commenting", "transcribing"}
                ):
                    continue
                for body in _as_list(annotation.get("body", annotation.get("resource"))):
                    if isinstance(body, Mapping) and _is_reference_text(body):
                        output.append(_row(
                            body,
                            manifest_id=manifest_id,
                            manifest_url=manifest_url,
                            providers=providers,
                            rights=rights,
                            canvas_index=canvas_index,
                            canvas_id=canvas_id,
                            canvas_label=canvas_label,
                            source_kind="canvas_annotation",
                            alignment_scope="canvas",
                            motivation=sorted(purposes),
                        ))

    # Manifest-level OCR packages are retained, but explicitly marked as
    # document-aligned so they cannot be mistaken for page-level pairs.
    output.extend(_from_see_also(
        document.get("seeAlso"),
        manifest_id=manifest_id,
        manifest_url=manifest_url,
        providers=providers,
        rights=rights,
        canvas_index=None,
        canvas_id=None,
        canvas_label=None,
        source_kind="manifest_seeAlso",
        alignment_scope="manifest",
    ))
    return _deduplicate(output)


def _from_see_also(
    value: Any,
    **context: Any,
) -> list[dict[str, Any]]:
    return [
        _row(item, **context)
        for item in _as_list(value)
        if isinstance(item, Mapping) and _is_reference_text(item, require_reference_signal=True)
    ]


def _row(value: Mapping[str, Any], **context: Any) -> dict[str, Any]:
    source_url = _identifier(value)
    inline_text = value.get("value") if isinstance(value.get("value"), str) else None
    media_type = str(value.get("format", "")).strip() or None
    body_type = str(value.get("type", value.get("@type", ""))).strip() or None
    profile = value.get("profile")
    language = value.get("language", value.get("@language"))
    label = _label(value.get("label"))
    signature = "\n".join([
        str(context.get("manifest_id", "")),
        str(context.get("canvas_index", "")),
        str(context.get("canvas_id", "")),
        str(source_url or inline_text or ""),
        str(media_type or ""),
    ])
    reference_id = f"reference-{sha256(signature.encode('utf-8')).hexdigest()[:20]}"
    rights = context.get("rights") if isinstance(context.get("rights"), Mapping) else {}
    usage = rights.get("usage_permissions") if isinstance(rights.get("usage_permissions"), Mapping) else {}
    return {
        "reference_text_id": reference_id,
        "manifest_id": context.get("manifest_id"),
        "manifest_url": context.get("manifest_url"),
        "canvas_index": context.get("canvas_index"),
        "canvas_id": context.get("canvas_id"),
        "canvas_label": context.get("canvas_label"),
        "alignment_scope": context.get("alignment_scope"),
        "source_kind": context.get("source_kind"),
        "source_url": source_url,
        "inline_text": clean_text(inline_text) if inline_text else None,
        "format": media_type,
        "type": body_type,
        "label": label,
        "language": language,
        "profile": profile,
        "motivation": context.get("motivation", []),
        "providers": context.get("providers", []),
        "rights_category": rights.get("category"),
        "research_status": rights.get("research_status"),
        "academic_analysis_allowed": usage.get("academic_analysis") is True,
    }


def _is_reference_text(value: Mapping[str, Any], *, require_reference_signal: bool = False) -> bool:
    media_type = str(value.get("format", "")).casefold()
    resource_type = _resource_type(value)
    label = _label(value.get("label")).casefold()
    profile = str(value.get("profile", "")).casefold()
    identifier = str(_identifier(value) or "").casefold()
    purpose = " ".join(
        str(item).casefold()
        for item in _as_list(value.get("purpose", value.get("motivation")))
    )
    signals = " ".join((media_type, label, profile, identifier, purpose))
    if any(term in signals for term in ("ocr", "hocr", "alto", "transcript", "full text", "fulltext")):
        return True
    # seeAlso is also used for catalogue pages. HTML alone is not OCR evidence;
    # explicitly supplementing inline TextualBodies keep their existing handling.
    if require_reference_signal and media_type.split(";", 1)[0].strip() in {"text/html", "application/xhtml+xml"}:
        return False
    # XML is a serialization format, not evidence of recognized page text.
    # Keep descriptive seeAlso resources in the raw Manifest, outside OCR pairs.
    if media_type.split(";", 1)[0].strip() in {"text/xml", "application/xml"}:
        return False
    if any(term in label for term in ("descriptive metadata", "bibliographic metadata", "dublin core", "marc record")):
        return False
    if resource_type in {"text", "textualbody"}:
        return True
    return media_type.startswith("text/")


def _deduplicate(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        key = str(row["reference_text_id"])
        if key not in seen:
            output.append(row)
            seen.add(key)
    return output


def _identifier(value: Mapping[str, Any]) -> str | None:
    candidate = value.get("id", value.get("@id"))
    return str(candidate).strip() if candidate else None


def _resource_type(value: Mapping[str, Any]) -> str:
    candidate = value.get("type", value.get("@type", ""))
    if isinstance(candidate, list):
        candidate = candidate[0] if candidate else ""
    return str(candidate).split(":")[-1].casefold()


def _label(value: Any) -> str:
    values = text_values(value, "$.label")
    return str(values[0]["value"]) if values else ""


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]
