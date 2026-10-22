"""IIIF Presentation Manifest structural validation and media inventory."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from .models import (
    CanvasResource,
    ValidationIssue,
    ValidationResult,
    canonicalize_url,
)


def validate_manifest(value: Any) -> ValidationResult:
    """Validate a decoded JSON value as a Presentation 2 or 3 Manifest."""

    result = ValidationResult()
    if not isinstance(value, Mapping):
        result.issues.append(
            ValidationIssue("json_not_object", "The JSON root must be an object")
        )
        return result

    result.context_values = _context_values(value.get("@context"))
    result.declared_type = _resource_type(value)
    result.declared_id = _resource_id(value)

    if not _is_manifest_type(result.declared_type):
        result.issues.append(
            ValidationIssue(
                "not_manifest",
                f"Top-level type is {result.declared_type or 'missing'}, not Manifest",
            )
        )
        return result

    if not result.declared_id:
        result.issues.append(
            ValidationIssue("missing_id", "Manifest requires id or @id")
        )
    else:
        try:
            result.declared_id = canonicalize_url(result.declared_id)
        except ValueError as exc:
            result.issues.append(
                ValidationIssue("invalid_id", str(exc), path="id/@id")
            )

    result.presentation_version = _presentation_version(result.context_values, value)
    legacy_contexts = {"http://www.shared-canvas.org/ns/context.json", "https://www.shared-canvas.org/ns/context.json"}
    if any(context in legacy_contexts for context in result.context_values):
        result.source_format = "legacy_shared_canvas"
        result.issues.append(ValidationIssue(
            "legacy_shared_canvas_context",
            "Legacy Shared Canvas source retained unchanged; sequences use the Presentation-2-compatible parser, not a claim of modern Presentation 2 conformance",
            severity="warning", path="@context"))
    if not result.context_values:
        result.issues.append(
            ValidationIssue(
                "missing_context",
                "Manifest has no @context; version was inferred from its structure",
                severity="review",
                path="@context",
            )
        )
    elif result.presentation_version is None:
        result.issues.append(
            ValidationIssue(
                "unknown_context",
                "No supported IIIF Presentation 2 or 3 context was found",
                severity="review",
                path="@context",
            )
        )

    if result.presentation_version == "3":
        canvases = _presentation_3_canvases(value, result)
    elif result.presentation_version == "2":
        canvases = _presentation_2_canvases(value, result)
    elif isinstance(value.get("items"), list):
        result.presentation_version = "3"
        canvases = _presentation_3_canvases(value, result)
    elif isinstance(value.get("sequences"), list):
        result.presentation_version = "2"
        canvases = _presentation_2_canvases(value, result)
    else:
        result.issues.append(
            ValidationIssue(
                "unsupported_manifest_structure",
                "Manifest has neither Presentation 3 items nor Presentation 2 sequences",
            )
        )
        canvases = []

    _inventory_manifest(value, canvases, result)

    if result.canvas_count == 0:
        result.issues.append(
            ValidationIssue(
                "no_canvases",
                "Manifest contains no usable Canvas",
                severity="review",
            )
        )
    if result.image_body_count == 0:
        result.issues.append(
            ValidationIssue(
                "no_image_bodies",
                "Manifest contains no image body for downstream extraction",
                severity="review",
            )
        )

    if any(issue.severity == "error" for issue in result.issues):
        result.status = "invalid"
    elif any(issue.severity == "review" for issue in result.issues):
        result.status = "manual_review"
    else:
        result.status = "valid"
    return result


def _presentation_version(contexts: list[str], value: Mapping[str, Any]) -> Optional[str]:
    lowered = [item.casefold() for item in contexts]
    if any("/presentation/3/" in item for item in lowered):
        return "3"
    if any("/presentation/2/" in item for item in lowered):
        return "2"
    if "items" in value and "sequences" not in value:
        return "3"
    if "sequences" in value:
        return "2"
    return None


def _presentation_3_canvases(
    manifest: Mapping[str, Any], result: ValidationResult
) -> list[Mapping[str, Any]]:
    items = manifest.get("items")
    if not isinstance(items, list):
        result.issues.append(
            ValidationIssue(
                "invalid_items",
                "Presentation 3 Manifest items must be an array",
                path="items",
            )
        )
        return []
    canvases: list[Mapping[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            result.issues.append(
                ValidationIssue(
                    "invalid_canvas",
                    "Canvas entry must be an object",
                    severity="review",
                    path=f"items[{index}]",
                )
            )
            continue
        item_type = _resource_type(item)
        if item_type != "Canvas":
            result.issues.append(
                ValidationIssue(
                    "unexpected_item_type",
                    f"Expected Canvas, got {item_type or 'missing type'}",
                    severity="review",
                    path=f"items[{index}]",
                )
            )
            continue
        canvases.append(item)
    return canvases


def _presentation_2_canvases(
    manifest: Mapping[str, Any], result: ValidationResult
) -> list[Mapping[str, Any]]:
    sequences = manifest.get("sequences")
    if not isinstance(sequences, list):
        result.issues.append(
            ValidationIssue(
                "invalid_sequences",
                "Presentation 2 Manifest sequences must be an array",
                path="sequences",
            )
        )
        return []
    canvases: list[Mapping[str, Any]] = []
    for sequence_index, sequence in enumerate(sequences):
        if not isinstance(sequence, Mapping):
            result.issues.append(
                ValidationIssue(
                    "invalid_sequence",
                    "Sequence entry must be an object",
                    severity="review",
                    path=f"sequences[{sequence_index}]",
                )
            )
            continue
        values = sequence.get("canvases")
        if not isinstance(values, list):
            result.issues.append(
                ValidationIssue(
                    "invalid_canvases",
                    "Sequence canvases must be an array",
                    severity="review",
                    path=f"sequences[{sequence_index}].canvases",
                )
            )
            continue
        for canvas_index, canvas in enumerate(values):
            if isinstance(canvas, Mapping):
                canvases.append(canvas)
            else:
                result.issues.append(
                    ValidationIssue(
                        "invalid_canvas",
                        "Canvas entry must be an object",
                        severity="review",
                        path=(
                            f"sequences[{sequence_index}]."
                            f"canvases[{canvas_index}]"
                        ),
                    )
                )
    return canvases


def _inventory_manifest(
    manifest: Mapping[str, Any],
    canvases: list[Mapping[str, Any]],
    result: ValidationResult,
) -> None:
    body_urls: set[str] = set()
    image_urls: set[str] = set()
    service_urls: set[str] = set()
    auxiliary_urls: set[str] = set()

    _add_link_values(auxiliary_urls, manifest.get("rendering"))
    _add_link_values(auxiliary_urls, manifest.get("seeAlso"))
    result.rights_values = sorted(
        {
            item
            for name in ("rights", "license")
            for item in _link_values(manifest.get(name))
        }
    )

    for canvas_index, canvas in enumerate(canvases):
        canvas_id = _resource_id(canvas)
        if canvas_id:
            try:
                canvas_id = canonicalize_url(canvas_id, preserve_fragment=True)
            except ValueError:
                result.issues.append(
                    ValidationIssue(
                        "invalid_canvas_id",
                        f"Canvas ID is not an absolute HTTP(S) URL: {canvas_id!r}",
                        severity="review",
                        path=f"canvas[{canvas_index}]",
                    )
                )
        else:
            result.issues.append(
                ValidationIssue(
                    "missing_canvas_id",
                    "Canvas has no id or @id",
                    severity="review",
                    path=f"canvas[{canvas_index}]",
                )
            )

        label = _label_text(canvas.get("label"))
        _add_link_values(auxiliary_urls, canvas.get("rendering"))
        _add_link_values(auxiliary_urls, canvas.get("seeAlso"))
        bodies = _canvas_bodies(canvas, result.presentation_version)

        if not bodies:
            result.canvas_resources.append(
                CanvasResource(
                    canvas_index=canvas_index,
                    canvas_id=canvas_id,
                    canvas_label=label,
                    body_id=None,
                    body_type=None,
                    body_format=None,
                )
            )

        for body in bodies:
            body_id = _resource_id(body)
            body_type = _resource_type(body) or None
            body_format = _optional_string(body.get("format"))
            canonical_body: Optional[str] = None
            if body_id:
                try:
                    canonical_body = canonicalize_url(body_id)
                    body_urls.add(canonical_body)
                except ValueError:
                    result.issues.append(
                        ValidationIssue(
                            "invalid_body_id",
                            f"Body ID is not an absolute HTTP(S) URL: {body_id!r}",
                            severity="review",
                            path=f"canvas[{canvas_index}]",
                        )
                    )

            is_image = (
                str(body_type or "").casefold() == "image"
                or str(body_format or "").casefold().startswith("image/")
            )
            if canonical_body and is_image:
                image_urls.add(canonical_body)

            services: list[str] = []
            for service in _as_list(body.get("service", body.get("services"))):
                service_id = _resource_id(service)
                if not service_id:
                    continue
                try:
                    canonical_service = canonicalize_url(service_id)
                except ValueError:
                    result.issues.append(
                        ValidationIssue(
                            "invalid_service_id",
                            f"Image service ID is invalid: {service_id!r}",
                            severity="review",
                            path=f"canvas[{canvas_index}]",
                        )
                    )
                    continue
                services.append(canonical_service)
                service_urls.add(canonical_service)

            result.canvas_resources.append(
                CanvasResource(
                    canvas_index=canvas_index,
                    canvas_id=canvas_id,
                    canvas_label=label,
                    body_id=canonical_body,
                    body_type=body_type,
                    body_format=body_format,
                    image_service_urls=tuple(sorted(set(services))),
                )
            )

    result.canvas_count = len(canvases)
    result.content_body_count = len(body_urls)
    result.image_body_count = len(image_urls)
    result.image_service_count = len(service_urls)
    result.auxiliary_file_count = len(auxiliary_urls)


def _canvas_bodies(
    canvas: Mapping[str, Any], version: Optional[str]
) -> list[Mapping[str, Any]]:
    values: list[Any] = []
    if version == "3" or "items" in canvas:
        for page in _as_list(canvas.get("items")):
            if not isinstance(page, Mapping):
                continue
            for annotation in _as_list(page.get("items")):
                if isinstance(annotation, Mapping):
                    values.extend(_as_list(annotation.get("body")))
    if version == "2" or "images" in canvas:
        for annotation in _as_list(canvas.get("images")):
            if isinstance(annotation, Mapping):
                values.extend(
                    _as_list(annotation.get("resource", annotation.get("body")))
                )
    output: list[Mapping[str, Any]] = []
    for value in values:
        output.extend(_iter_bodies(value))
    return output


def _iter_bodies(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, list):
        return [body for item in value for body in _iter_bodies(item)]
    if not isinstance(value, Mapping):
        return []
    if _resource_type(value) == "Choice":
        return [
            body
            for item in _as_list(value.get("items", value.get("item")))
            for body in _iter_bodies(item)
        ]
    return [value]


def _context_values(value: Any) -> list[str]:
    output: list[str] = []
    for item in _as_list(value):
        if isinstance(item, str) and item.strip():
            output.append(item.strip())
    return output


def _resource_id(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, Mapping):
        candidate = value.get("id", value.get("@id"))
        if candidate is not None:
            return str(candidate).strip() or None
    return None


def _resource_type(value: Any) -> Optional[str]:
    if not isinstance(value, Mapping):
        return None
    candidate = value.get("type", value.get("@type"))
    if isinstance(candidate, list):
        candidate = candidate[0] if candidate else None
    if candidate is None:
        return None
    return str(candidate).split(":")[-1]


def _is_manifest_type(value: Optional[str]) -> bool:
    return str(value or "").casefold() == "manifest"


def _label_text(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list):
        parts = [text for item in value if (text := _label_text(item))]
        return " | ".join(parts) or None
    if isinstance(value, Mapping):
        parts = [
            text
            for language_value in value.values()
            if (text := _label_text(language_value))
        ]
        return " | ".join(parts) or None
    return None


def _link_values(value: Any) -> list[str]:
    output: list[str] = []
    for item in _as_list(value):
        identifier = _resource_id(item)
        if not identifier:
            continue
        try:
            output.append(canonicalize_url(identifier))
        except ValueError:
            continue
    return output


def _add_link_values(target: set[str], value: Any) -> None:
    target.update(_link_values(value))


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
