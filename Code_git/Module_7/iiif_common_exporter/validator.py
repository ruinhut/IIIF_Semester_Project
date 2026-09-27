"""Deterministic validation for provisional common records."""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlparse

from .models import MEDIA_SCHEMA_VERSION, RECORD_SCHEMA_VERSION


def validate_record(record: Mapping[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    _equal(issues, record, "schema_version", RECORD_SCHEMA_VERSION)
    _text(issues, record.get("record_id"), "$.record_id")
    obj = _mapping(issues, record.get("object"), "$.object")
    _text(issues, obj.get("identifier"), "$.object.identifier")
    rights = _mapping(issues, record.get("rights"), "$.rights")
    _text(issues, rights.get("category"), "$.rights.category")
    _equal(issues, rights, "decision", "allow", "$.rights.decision")
    _text(issues, rights.get("policy_version"), "$.rights.policy_version")
    if not isinstance(rights.get("statements"), list):
        _issue(issues, "type", "$.rights.statements", "must be a list")
    source = _mapping(issues, record.get("source"), "$.source")
    _text(issues, source.get("manifest_id"), "$.source.manifest_id")
    _url(issues, source.get("manifest_url"), "$.source.manifest_url")
    providers = source.get("providers")
    if not isinstance(providers, list) or not providers:
        _issue(issues, "required", "$.source.providers", "must contain at least one provider")
    media_count = record.get("media_count")
    if not isinstance(media_count, int) or isinstance(media_count, bool) or media_count < 0:
        _issue(issues, "type", "$.media_count", "must be a non-negative integer")
    dates = obj.get("dates", [])
    if not isinstance(dates, list):
        _issue(issues, "type", "$.object.dates", "must be a list")
    else:
        for index, date in enumerate(dates):
            if not isinstance(date, Mapping):
                _issue(issues, "type", f"$.object.dates[{index}]", "must be an object")
                continue
            start, end = date.get("start_year"), date.get("end_year")
            if start is not None and not isinstance(start, int):
                _issue(issues, "type", f"$.object.dates[{index}].start_year", "must be integer or null")
            if end is not None and not isinstance(end, int):
                _issue(issues, "type", f"$.object.dates[{index}].end_year", "must be integer or null")
            if isinstance(start, int) and isinstance(end, int) and start > end:
                _issue(issues, "range", f"$.object.dates[{index}]", "start_year must not exceed end_year")
    return issues


def validate_media(record: Mapping[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    _equal(issues, record, "schema_version", MEDIA_SCHEMA_VERSION)
    _text(issues, record.get("resource_id"), "$.resource_id")
    _text(issues, record.get("record_id"), "$.record_id")
    sequence = record.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        _issue(issues, "type", "$.sequence", "must be a non-negative integer")
    _mapping(issues, record.get("canvas"), "$.canvas")
    image = _mapping(issues, record.get("image"), "$.image")
    services = image.get("service_urls")
    if not isinstance(services, list):
        _issue(issues, "type", "$.image.service_urls", "must be a list")
        services = []
    if not str(image.get("id") or "").strip() and not services:
        _issue(issues, "required", "$.image", "requires an image id or service URL")
    rights = _mapping(issues, record.get("rights"), "$.rights")
    _equal(issues, rights, "decision", "allow", "$.rights.decision")
    _url(issues, record.get("source_manifest_url"), "$.source_manifest_url")
    return issues


def _mapping(issues: list[dict[str, str]], value: Any, path: str) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    _issue(issues, "type", path, "must be an object")
    return {}


def _text(issues: list[dict[str, str]], value: Any, path: str) -> None:
    if not isinstance(value, str) or not value.strip():
        _issue(issues, "required", path, "must be a non-empty string")


def _url(issues: list[dict[str, str]], value: Any, path: str) -> None:
    if not isinstance(value, str) or urlparse(value).scheme not in {"http", "https"} or not urlparse(value).netloc:
        _issue(issues, "format", path, "must be an absolute HTTP(S) URL")


def _equal(issues: list[dict[str, str]], value: Mapping[str, Any], key: str, expected: Any, path: str | None = None) -> None:
    if value.get(key) != expected:
        _issue(issues, "const", path or f"$.{key}", f"must equal {expected!r}")


def _issue(issues: list[dict[str, str]], code: str, path: str, message: str) -> None:
    issues.append({"code": code, "path": path, "message": message})
