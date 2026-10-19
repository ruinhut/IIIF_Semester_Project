"""Reusable discovery skills derived from reviewed institution investigations."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from html.parser import HTMLParser
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit, urlunsplit

from .fetch import FetchError, FetchedDocument, HttpFetcher, is_json_document
from .models import DiscoveryIssue, canonicalize_url


SUPPORTED_SKILL_TYPE = "paginated_json_identifiers_to_manifest_templates"
DIRECT_LINK_SKILL_TYPE = "paginated_json_manifest_links"
HTML_IDENTIFIER_SKILL_TYPE = "paginated_html_identifiers_to_manifest_templates"
OMEKA_S_AUTO_SKILL_ID = "omeka-s-auto-detected-items-to-manifests"


@dataclass(frozen=True)
class ValidatedManifest:
    """One Manifest verified by a reusable discovery skill."""

    manifest_url: str
    source_url: str
    skill_id: str


@dataclass(frozen=True)
class ValidatedEntryPoint:
    """A verified IIIF Collection root, kept distinct from a Manifest."""

    endpoint_url: str
    source_url: str
    skill_id: str


@dataclass
class SkillExecution:
    """Auditable result of applying one learned discovery skill."""

    manifests: list[ValidatedManifest] = field(default_factory=list)
    entry_points: list[ValidatedEntryPoint] = field(default_factory=list)
    issues: list[DiscoveryIssue] = field(default_factory=list)
    audit: dict[str, Any] = field(default_factory=dict)
    truncated: bool = False


def execute_skill(
    skill: Mapping[str, Any],
    fetcher: HttpFetcher,
    *,
    investigation_id: str,
    max_manifests: int,
) -> SkillExecution:
    """Validate and execute one named discovery skill."""

    skill_type = str(skill.get("type", "")).strip()
    skill_id = str(skill.get("skill_id", "")).strip() or "unnamed-skill"
    if skill_type not in {SUPPORTED_SKILL_TYPE, DIRECT_LINK_SKILL_TYPE, HTML_IDENTIFIER_SKILL_TYPE}:
        return SkillExecution(
            issues=[
                DiscoveryIssue(
                    str(skill.get("api_url", "knowledge://unknown")),
                    "unsupported_knowledge_skill",
                    f"Unsupported discovery skill type: {skill_type or 'missing'}",
                )
            ],
            audit={
                "investigation_id": investigation_id,
                "skill_id": skill_id,
                "skill_type": skill_type or None,
                "status": "unsupported",
            },
        )
    try:
        if skill_type == HTML_IDENTIFIER_SKILL_TYPE:
            return _execute_html_identifier_skill(
                skill, fetcher, investigation_id=investigation_id,
                max_manifests=max_manifests,
            )
        if skill_type == DIRECT_LINK_SKILL_TYPE:
            return _execute_paginated_link_skill(
                skill, fetcher, investigation_id=investigation_id,
                max_manifests=max_manifests,
            )
        return _execute_paginated_identifier_skill(
            skill,
            fetcher,
            investigation_id=investigation_id,
            max_manifests=max_manifests,
        )
    except (TypeError, ValueError, KeyError, re.error) as exc:
        api_url = str(skill.get("api_url", "knowledge://invalid"))
        return SkillExecution(
            issues=[
                DiscoveryIssue(api_url, "invalid_knowledge_skill", str(exc))
            ],
            audit={
                "investigation_id": investigation_id,
                "skill_id": skill_id,
                "skill_type": skill_type,
                "status": "invalid_configuration",
            },
        )


def execute_omeka_s_probe(
    seed_urls: Sequence[str],
    fetcher: HttpFetcher,
    *,
    max_manifests: int,
    request_delay_seconds: float = 0.1,
) -> SkillExecution | None:
    """Detect an Omeka S installation and reuse the EPFL discovery method.

    A probe is attempted only when a seed URL or its HTML contains a strong
    Omeka S signal.  Returning ``None`` means that the method was not
    applicable; it is not treated as a provider failure.
    """

    roots: dict[str, set[str]] = {}
    for raw_seed in seed_urls:
        try:
            seed = canonicalize_url(raw_seed)
        except ValueError:
            continue

        path_root = _omeka_root_from_url(seed)
        if path_root:
            roots.setdefault(path_root, set()).add(seed)
            continue

        try:
            document = fetcher.fetch(
                seed,
                accept="text/html, application/xhtml+xml;q=0.9",
            )
            if is_json_document(document):
                continue
            html = document.text()
        except FetchError:
            continue
        for root in _omeka_roots_from_html(document.final_url, html):
            roots.setdefault(root, set()).add(document.final_url)

    if not roots:
        return None

    combined = SkillExecution()
    probed_roots: list[str] = []
    for root in sorted(roots):
        probed_roots.append(root)
        page_size = min(25, max_manifests)
        max_pages = max(1, (max_manifests + page_size - 1) // page_size)
        execution = execute_skill(
            {
                "skill_id": OMEKA_S_AUTO_SKILL_ID,
                "type": SUPPORTED_SKILL_TYPE,
                "api_url": f"{root}/api/items",
                "records_path": "$",
                "identifier_path": "o:id",
                "required_nonempty_paths": ["o:media"],
                "filters": [],
                "pagination": {
                    "page_parameter": "page",
                    "page_size_parameter": "per_page",
                    "page_size": page_size,
                    "start_page": 1,
                    "max_pages": max_pages,
                },
                "max_identifiers": max_manifests,
                "manifest_url_templates": [
                    f"{root}/iiif/3/{{identifier}}/manifest",
                    f"{root}/iiif-presentation/3/item/{{identifier}}/manifest",
                    f"{root}/iiif/{{identifier}}/manifest",
                ],
                "request_delay_seconds": request_delay_seconds,
            },
            fetcher,
            investigation_id="automatic-platform-probe:omeka-s",
            max_manifests=max_manifests,
        )
        execution.audit.update(
            {
                "detected_platform": "Omeka S",
                "platform_root": root,
                "platform_evidence_urls": sorted(roots[root]),
                "probe_mode": "reusable_epfl_method",
            }
        )
        combined.issues.extend(execution.issues)
        combined.truncated = combined.truncated or execution.truncated
        if execution.manifests:
            return execution

    combined.audit = {
        "investigation_id": "automatic-platform-probe:omeka-s",
        "skill_id": OMEKA_S_AUTO_SKILL_ID,
        "skill_type": SUPPORTED_SKILL_TYPE,
        "status": "platform_detected_no_manifests",
        "detected_platform": "Omeka S",
        "probed_roots": probed_roots,
        "probe_mode": "reusable_epfl_method",
        "truncated": combined.truncated,
    }
    return combined


def _execute_paginated_identifier_skill(
    skill: Mapping[str, Any],
    fetcher: HttpFetcher,
    *,
    investigation_id: str,
    max_manifests: int,
) -> SkillExecution:
    skill_id = _required_string(skill, "skill_id")
    api_url = canonicalize_url(_required_string(skill, "api_url"))
    records_path = str(skill.get("records_path", "$"))
    identifier_path = _required_string(skill, "identifier_path")
    templates = _string_list(skill.get("manifest_url_templates"), "manifest_url_templates")
    if any("{identifier}" not in template for template in templates):
        raise ValueError("every manifest URL template must contain {identifier}")

    pagination = _mapping(skill.get("pagination", {}), "pagination")
    page_parameter = str(pagination.get("page_parameter", "page")).strip()
    page_size_parameter = str(
        pagination.get("page_size_parameter", "per_page")
    ).strip()
    page_size = _positive_int(pagination.get("page_size", 20), "page_size")
    start_page = _nonnegative_int(pagination.get("start_page", 1), "start_page")
    page_step = _positive_int(pagination.get("page_step", 1), "page_step")
    max_pages = _positive_int(pagination.get("max_pages", 5), "max_pages")
    max_identifiers = _positive_int(
        skill.get("max_identifiers", max_manifests), "max_identifiers"
    )
    request_delay = float(skill.get("request_delay_seconds", 0.0))
    if request_delay < 0:
        raise ValueError("request_delay_seconds must be non-negative")
    query_parameters = _mapping(
        skill.get("query_parameters", {}), "query_parameters"
    )
    filters = _mapping_list(skill.get("filters", []), "filters")
    required_nonempty_paths = _string_list(
        skill.get("required_nonempty_paths", []),
        "required_nonempty_paths",
        allow_empty=True,
    )

    execution = SkillExecution()
    failure_counts: Counter[str] = Counter()
    identifiers: list[str] = []
    seen_identifiers: set[str] = set()
    identifier_pattern = skill.get("identifier_pattern")
    identifier_regex = re.compile(str(identifier_pattern)) if identifier_pattern else None
    pages_fetched = 0
    records_examined = 0
    manifest_requests = 0
    last_request_made = False
    seen_record_pages = set()
    source_declared_total = None

    def pause_if_needed() -> None:
        nonlocal last_request_made
        if last_request_made and request_delay:
            fetcher.sleeper(request_delay)
        last_request_made = True

    def source_identifiers():
        """Page lazily, so an output limit does not scan the whole catalogue first."""
        nonlocal pages_fetched, records_examined, source_declared_total
        for page_offset in range(max_pages):
            page_number = start_page + page_offset * page_step
            page_url, request_options = catalogue_request(skill, page_number, page_size)
            try:
                pause_if_needed()
                document = fetcher.fetch(
                    page_url,
                    accept="application/ld+json, application/json;q=0.9",
                    **request_options,
                )
                if not is_json_document(document):
                    raise ValueError("API page did not return JSON")
                page_value = document.json()
                records = _path_value(page_value, records_path)
                if not isinstance(records, list):
                    raise ValueError(
                        f"records_path {records_path!r} did not resolve to an array"
                    )
            except FetchError as exc:
                execution.issues.append(
                    DiscoveryIssue(exc.url, exc.error_type, str(exc))
                )
                failure_counts[exc.error_type] += 1
                break
            except ValueError as exc:
                execution.issues.append(
                    DiscoveryIssue(page_url, "knowledge_api_shape", str(exc))
                )
                failure_counts["knowledge_api_shape"] += 1
                break

            pages_fetched += 1
            records_examined += len(records)
            if pagination.get("total_path"):
                declared = _path_value(page_value, str(pagination["total_path"]))
                if isinstance(declared, int) and not isinstance(declared, bool):
                    source_declared_total = declared
            signature = sha256(json.dumps(records, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if records and signature in seen_record_pages:
                execution.truncated = True
                failure_counts["repeated_catalogue_page"] += 1
                execution.issues.append(DiscoveryIssue(page_url, "repeated_catalogue_page", "Pagination returned an already processed record page"))
                break
            seen_record_pages.add(signature)
            for record in records:
                if not isinstance(record, Mapping):
                    continue
                if not _record_matches(record, filters, required_nonempty_paths):
                    continue
                for identifier in _path_values(record, identifier_path):
                    if identifier is None or isinstance(identifier, (list, Mapping)):
                        continue
                    text = str(identifier).strip()
                    if identifier_regex:
                        match = identifier_regex.search(text)
                        if not match:
                            continue
                        text = match.groupdict().get("identifier") or match.group(1)
                    if text and text not in seen_identifiers:
                        identifiers.append(text)
                        seen_identifiers.add(text)
                        yield text
                    if len(identifiers) >= max_identifiers:
                        break
                if len(identifiers) >= max_identifiers:
                    execution.truncated = True
                    break
            if len(identifiers) >= max_identifiers:
                break
            end_path = pagination.get("has_next_path")
            if end_path and not _path_value(page_value, str(end_path)):
                break
            if not end_path and len(records) < page_size:
                if source_declared_total is not None and records_examined < source_declared_total:
                    execution.truncated = True
                    failure_counts["premature_short_catalogue_page"] += 1
                    execution.issues.append(DiscoveryIssue(
                        page_url, "premature_short_catalogue_page",
                        "Short page before the API declared total; check server page-size clamping or pagination."))
                break
        else:
            execution.truncated = True


    template_success_counts: Counter[str] = Counter()
    followup_requests = 0
    followup = skill.get("identifier_followup")

    def candidate_identifiers():
        """Lazily expand parent records through a documented detail API."""
        nonlocal followup_requests
        if not followup:
            yield from source_identifiers()
            return
        detail = _mapping(followup, "identifier_followup")
        detail_template = _required_string(detail, "url_template")
        detail_path = _required_string(detail, "identifier_path")
        detail_pattern = detail.get("identifier_pattern")
        detail_regex = re.compile(str(detail_pattern)) if detail_pattern else None
        if "{identifier}" not in detail_template:
            raise ValueError("identifier_followup URL must contain {identifier}")
        seen_children = set()
        for parent in source_identifiers():
            detail_url = canonicalize_url(detail_template.replace("{identifier}", quote(parent, safe="")))
            followup_requests += 1
            try:
                pause_if_needed()
                document = fetcher.fetch(detail_url, accept="application/json")
                children = _path_value(document.json(), str(detail.get("records_path", "$")))
                # Detail APIs commonly return one record object, unlike search lists.
                if isinstance(children, Mapping):
                    children = [children]
                if not isinstance(children, list):
                    raise ValueError("identifier_followup records_path must resolve to an object or array")
                for child in children:
                    for value in _path_values(child, detail_path):
                        if not isinstance(value, (str, int)) or isinstance(value, bool):
                            continue
                        child_id = str(value).strip()
                        if detail_regex:
                            match = detail_regex.search(child_id)
                            if not match:
                                continue
                            child_id = match.groupdict().get("identifier") or match.group(1)
                        if child_id and child_id not in seen_children:
                            seen_children.add(child_id)
                            yield child_id
            except (FetchError, ValueError) as exc:
                error_type = getattr(exc, "error_type", "knowledge_followup_shape")
                failure_counts[error_type] += 1
                execution.issues.append(DiscoveryIssue(detail_url, error_type, str(exc)))

    seen_manifest_urls = set()
    for identifier in candidate_identifiers():
        if len(execution.manifests) + len(execution.entry_points) >= max_manifests:
            execution.truncated = True
            break
        encoded_identifier = quote(identifier, safe="")
        for template in templates:
            candidate_url = canonicalize_url(
                template.replace("{identifier}", encoded_identifier)
            )
            manifest_requests += 1
            try:
                pause_if_needed()
                document = fetcher.fetch(
                    candidate_url,
                    accept="application/ld+json, application/json;q=0.9",
                )
                if not is_json_document(document):
                    failure_counts["not_json"] += 1
                    continue
                value = document.json()
                if not _is_iiif_manifest(value, allow_legacy_shared_canvas=skill.get("allow_legacy_shared_canvas") is True):
                    if skill.get("allow_collections") and _is_iiif_collection(value):
                        final_url = canonicalize_url(document.final_url)
                        if final_url not in seen_manifest_urls:
                            seen_manifest_urls.add(final_url)
                            execution.entry_points.append(ValidatedEntryPoint(final_url, api_url, skill_id))
                            template_success_counts[template] += 1
                        break
                    failure_counts["not_iiif_manifest"] += 1
                    continue
                final_url = canonicalize_url(document.final_url)
                if final_url in seen_manifest_urls:
                    break
                seen_manifest_urls.add(final_url)
                execution.manifests.append(
                    ValidatedManifest(final_url, api_url, skill_id)
                )
                template_success_counts[template] += 1
                break
            except FetchError as exc:
                failure_counts[exc.error_type] += 1

        if len(execution.manifests) + len(execution.entry_points) >= max_manifests:
            execution.truncated = True
            break

    status = "manifests_found" if execution.manifests else ("collections_found" if execution.entry_points else "no_manifests")
    if not identifiers and not execution.issues:
        execution.issues.append(
            DiscoveryIssue(
                api_url,
                "knowledge_skill_no_identifiers",
                "The API pages yielded no identifiers after filters",
            )
        )
    elif identifiers and not execution.manifests and not execution.entry_points:
        execution.issues.append(
            DiscoveryIssue(
                api_url,
                "knowledge_skill_no_manifests",
                "Identifiers were found, but no URL template returned a valid IIIF Manifest",
            )
        )
    execution.audit = {
        "investigation_id": investigation_id,
        "skill_id": skill_id,
        "skill_type": SUPPORTED_SKILL_TYPE,
        "status": status,
        "api_url": api_url,
        "catalogue_method": str(skill.get("request", {}).get("method", "GET")).upper(),
        "pagination_location": str(pagination.get("location", "query")),
        "pages_fetched": pages_fetched,
        "records_examined": records_examined,
        "source_declared_total": source_declared_total,
        "identifiers_selected": len(identifiers),
        "manifest_requests": manifest_requests,
        "followup_requests": followup_requests,
        "manifests_validated": len(execution.manifests),
        "collection_roots_validated": len(execution.entry_points),
        "template_success_counts": dict(sorted(template_success_counts.items())),
        "failure_counts": dict(sorted(failure_counts.items())),
        "truncated": execution.truncated,
    }
    return execution


def catalogue_request(skill: Mapping[str, Any], page_number: int, page_size: int):
    """Construct a catalogue query without sending it.

    POST must be explicitly marked as a read-only search in the reviewed
    recipe. Only catalogue requests receive its body/headers; candidate
    Manifest retrieval remains a plain GET. Query and JSON-body pagination
    are distinct, and every page starts from an independent body copy.
    """
    api_url = canonicalize_url(_required_string(skill, "api_url"))
    pagination = _mapping(skill.get("pagination", {}), "pagination")
    query = _mapping(skill.get("query_parameters", {}), "query_parameters")
    request = _mapping(skill.get("request", {}), "request")
    method = str(request.get("method", "GET")).upper()
    if method not in {"GET", "POST"}:
        raise ValueError("Catalogue method must be GET or POST")
    if method == "POST" and request.get("read_only") is not True:
        raise ValueError("POST catalogue recipes require read_only=true")
    location = str(pagination.get("location", "query"))
    if location not in {"query", "json_body"}:
        raise ValueError("pagination.location must be query or json_body")
    if location == "json_body" and method != "POST":
        raise ValueError("JSON-body pagination requires a POST catalogue query")
    body = deepcopy(dict(_mapping(request.get("json_body", {}), "request.json_body")))
    page_parameter = str(pagination.get("page_parameter", "page"))
    size_parameter = str(pagination.get("page_size_parameter", "per_page"))
    if location == "json_body":
        if page_parameter:
            body[page_parameter] = page_number
        if size_parameter:
            body[size_parameter] = page_size
        page_parameter = size_parameter = ""
    url = _page_url(api_url, query, page_parameter=page_parameter,
                    page_size_parameter=size_parameter, page_number=page_number, page_size=page_size)
    options = {}
    if method == "POST":
        options.update(method=method, json_body=body)
    headers = _mapping(request.get("headers", {}), "request.headers")
    if headers:
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in headers.items()):
            raise ValueError("request.headers must contain text names and values")
        options["headers"] = dict(headers)
    return url, options


def _execute_paginated_link_skill(
    skill: Mapping[str, Any], fetcher: HttpFetcher, *,
    investigation_id: str, max_manifests: int,
) -> SkillExecution:
    """Read explicit Manifest URLs nested in paginated catalogue records.

    Dot paths permit a `*` segment for arrays, for example
    `items.*.locations.*.url`. Provider links are fetched and IIIF-checked;
    ordinary website, PDF, and Image API links cannot become Manifests.
    """
    skill_id = _required_string(skill, "skill_id")
    api_url = canonicalize_url(_required_string(skill, "api_url"))
    link_path = _required_string(skill, "manifest_url_path")
    link_pattern = skill.get("manifest_url_pattern")
    link_regex = re.compile(str(link_pattern)) if link_pattern else None
    records_path = str(skill.get("records_path", "$"))
    pagination = _mapping(skill.get("pagination", {}), "pagination")
    page_size = _positive_int(pagination.get("page_size", 20), "page_size")
    max_pages = _positive_int(pagination.get("max_pages", 5), "max_pages")
    start_page = _nonnegative_int(pagination.get("start_page", 1), "start_page")
    page_step = _positive_int(pagination.get("page_step", 1), "page_step")
    query = _mapping(skill.get("query_parameters", {}), "query_parameters")
    delay = float(skill.get("request_delay_seconds", 0.25))
    if delay < 0:
        raise ValueError("request_delay_seconds must be non-negative")
    execution = SkillExecution()
    failures: Counter[str] = Counter()
    seen: set[str] = set()
    pages_fetched = records_examined = manifest_requests = 0
    for offset in range(max_pages):
        page_url, request_options = catalogue_request(skill, start_page + offset * page_step, page_size)
        try:
            fetcher.sleeper(delay)
            document = fetcher.fetch(page_url, accept="application/json, application/ld+json", **request_options)
            value = document.json()
            records = _path_value(value, records_path)
            if not isinstance(records, list):
                raise ValueError(f"records_path {records_path!r} must resolve to an array")
        except (FetchError, ValueError) as exc:
            execution.issues.append(DiscoveryIssue(
                page_url, getattr(exc, "error_type", "knowledge_api_shape"), str(exc)
            ))
            failures[getattr(exc, "error_type", "knowledge_api_shape")] += 1
            break
        pages_fetched += 1
        records_examined += len(records)
        for record in records:
            for candidate in _path_values(record, link_path):
                if not isinstance(candidate, str):
                    continue
                # A catalogue may mix Manifest, PDF, viewer and thumbnail URLs.
                if link_regex and not link_regex.search(candidate):
                    continue
                try:
                    url = canonicalize_url(candidate)
                except ValueError:
                    continue
                if url in seen:
                    continue
                seen.add(url)
                manifest_requests += 1
                try:
                    fetcher.sleeper(delay)
                    manifest = _fetch_declared_manifest(fetcher, url, skill)
                    if not _is_iiif_manifest(manifest.json(), allow_legacy_shared_canvas=skill.get("allow_legacy_shared_canvas") is True):
                        failures["not_iiif_manifest"] += 1
                        continue
                    execution.manifests.append(ValidatedManifest(
                        canonicalize_url(manifest.final_url), page_url, skill_id
                    ))
                except FetchError as exc:
                    failures[exc.error_type] += 1
                if len(execution.manifests) >= max_manifests:
                    execution.truncated = True
                    break
            if execution.truncated:
                break
        if execution.truncated or len(records) < page_size:
            break
    else:
        execution.truncated = True
    execution.audit = {
        "investigation_id": investigation_id, "skill_id": skill_id,
        "skill_type": DIRECT_LINK_SKILL_TYPE,
        "status": "manifests_found" if execution.manifests else "no_manifests",
        "api_url": api_url, "pages_fetched": pages_fetched,
        "records_examined": records_examined, "manifest_requests": manifest_requests,
        "manifests_validated": len(execution.manifests),
        "failure_counts": dict(failures), "truncated": execution.truncated,
    }
    return execution


def _fetch_declared_manifest(fetcher: HttpFetcher, url: str, skill: Mapping[str, Any]) -> FetchedDocument:
    """Follow an opted-in HTML refresh migration, never arbitrary page links.

    HTTP redirects remain handled by the fetcher. Some legacy delivery servers
    instead return a successful HTML response with an explicit refresh target.
    Each additional target must match reviewed configuration and cycles stop.
    """
    migration = _mapping(skill.get("html_migration", {}), "html_migration")
    hops = _nonnegative_int(migration.get("max_hops", 0), "html_migration.max_hops")
    pattern = migration.get("url_pattern")
    allowed = re.compile(str(pattern)) if pattern else None
    if hops and not allowed:
        raise ValueError("html_migration requires an explicit allowed url_pattern")
    seen = set()
    for hop in range(hops + 1):
        document = fetcher.fetch(url)
        if is_json_document(document) or hop == hops:
            return document

        class Refresh(HTMLParser):
            target = None

            def handle_starttag(self, tag, attrs):
                values = {k.lower(): v for k, v in attrs}
                if tag == "meta" and str(values.get("http-equiv", "")).lower() == "refresh":
                    match = re.search(r"(?:^|;)\s*url\s*=\s*(.+)$", values.get("content", ""), re.I)
                    if match:
                        self.target = match.group(1).strip().strip("\"'")

        parser = Refresh()
        parser.feed(document.text())
        if not parser.target:
            return document
        target = canonicalize_url(urljoin(document.final_url, parser.target))
        seen.update((url, document.final_url))
        if target in seen or not allowed.search(target):
            return document
        url = target
    return document


def _path_values(value: Any, path: str) -> list[Any]:
    """Resolve an explicit dot path, expanding only declared `*` arrays."""
    values = [value]
    if path in {"", "$"}:
        return values
    for segment in path.removeprefix("$.").split("."):
        next_values = []
        for current in values:
            if segment == "*" and isinstance(current, list):
                next_values.extend(current)
            elif isinstance(current, Mapping) and segment in current:
                next_values.append(current[segment])
            elif isinstance(current, list) and segment.isdigit() and int(segment) < len(current):
                next_values.append(current[int(segment)])
        values = next_values
    return values


def _execute_html_identifier_skill(
    skill: Mapping[str, Any], fetcher: HttpFetcher, *,
    investigation_id: str, max_manifests: int,
) -> SkillExecution:
    """Enumerate catalogue record links using a reviewed identifier pattern.

    This is a targeted catalogue parser, with bounded pages and identifiers,
    rather than an unconstrained same-site crawler. Manifest retrieval and
    validation reuse the existing API identifier skill.
    """
    listing_url = canonicalize_url(_required_string(skill, "api_url"))
    pattern = re.compile(_required_string(skill, "record_url_pattern"))
    identifier_template = str(skill.get("identifier_template", "{identifier}"))
    required_container = skill.get("required_ancestor_class")
    listing_route = urlsplit(listing_url)

    class RecordLinks(HTMLParser):
        def __init__(self, base):
            super().__init__()
            self.base = base
            self.records = {}
            self.frames = []
            self.links = []

        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            allowed = (not required_container or any(required_container in classes for _, classes in self.frames)
                       or required_container in values.get("class", "").split())
            if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
                self.frames.append((tag, values.get("class", "").split()))
            if tag != "a":
                return
            href = values.get("href")
            if not href:
                return
            source = urljoin(self.base, href)
            self.links.append(source)
            match = pattern.search(source)
            if match and allowed:
                identifier = identifier_template.format(**match.groupdict())
                self.records.setdefault(identifier, {"identifier": identifier,
                                                      "record_url": source})

        def handle_endtag(self, tag):
            for index in range(len(self.frames) - 1, -1, -1):
                if self.frames[index][0] == tag:
                    del self.frames[index:]
                    break

    class ListingFetcher:
        sleeper = staticmethod(fetcher.sleeper)
        pages = []

        def fetch(self, url, *, accept="application/json"):
            parts = urlsplit(url)
            if (parts.netloc, parts.path) != (listing_route.netloc, listing_route.path):
                return fetcher.fetch(url, accept=accept)
            document = fetcher.fetch(url, accept="text/html, application/xhtml+xml")
            parser = RecordLinks(document.final_url)
            parser.feed(document.text())
            pagination = _mapping(skill.get("pagination", {}), "pagination")
            parameter = str(pagination.get("page_parameter", "page"))
            current = int(dict(parse_qsl(parts.query)).get(parameter, pagination.get("start_page", 1)))
            has_next = False
            for link in parser.links:
                if urlsplit(link).netloc != urlsplit(document.final_url).netloc:
                    continue
                values = dict(parse_qsl(urlsplit(link).query))
                page_value = values.get(parameter)
                if page_value and page_value.isdigit() and int(page_value) > current:
                    has_next = True
            self.pages.append({"url": document.final_url, "record_count": len(parser.records), "has_next": has_next})
            payload = {"records": list(parser.records.values()), "has_next": has_next}
            return FetchedDocument(document.requested_url, document.final_url,
                                   document.status_code, "application/json",
                                   json.dumps(payload).encode())

    adapted = dict(skill)
    adapted.update(type=SUPPORTED_SKILL_TYPE, records_path="records", identifier_path="identifier")
    if skill.get("pagination", {}).get("detect_next_page"):
        adapted["pagination"] = {**skill["pagination"], "has_next_path": "has_next"}
    listing_fetcher = ListingFetcher()
    result = _execute_paginated_identifier_skill(
        adapted, listing_fetcher, investigation_id=investigation_id,
        max_manifests=max_manifests,
    )
    result.audit["skill_type"] = HTML_IDENTIFIER_SKILL_TYPE
    result.audit["record_url_pattern"] = str(skill["record_url_pattern"])
    result.audit["enumeration_pages"] = listing_fetcher.pages
    return result


def _omeka_root_from_url(url: str) -> str | None:
    """Return the installation root when a URL contains an Omeka S route."""

    parts = urlsplit(url)
    lowered = parts.path.casefold()
    markers = ("/s/", "/application/", "/modules/", "/themes/")
    positions = [lowered.find(marker) for marker in markers if marker in lowered]
    if not positions:
        return None
    prefix = parts.path[: min(positions)].rstrip("/")
    return canonicalize_url(
        urlunsplit((parts.scheme, parts.netloc, prefix or "/", "", ""))
    ).rstrip("/")


def _omeka_roots_from_html(page_url: str, html: str) -> tuple[str, ...]:
    """Infer possible installation roots only from strong Omeka S signals."""

    lowered = html.casefold()
    signals = (
        "omeka.jstranslate",
        "omeka-s",
        "omeka s",
        "omeka.js",
        "omeka.org/s/",
    )
    has_signal = any(signal in lowered for signal in signals)
    if not has_signal and not (
        "/application/asset/" in lowered and "/s/" in urlsplit(page_url).path.casefold()
    ):
        return ()

    candidates: set[str] = set()
    page_root = _omeka_root_from_url(page_url)
    if page_root:
        candidates.add(page_root)
    else:
        parts = urlsplit(page_url)
        candidates.add(
            canonicalize_url(
                urlunsplit((parts.scheme, parts.netloc, "/", "", ""))
            ).rstrip("/")
        )

    for match in re.finditer(
        r"(?:src|href)\s*=\s*['\"]([^'\"]+)['\"]",
        html,
        flags=re.IGNORECASE,
    ):
        absolute = urljoin(page_url, match.group(1))
        root = _omeka_root_from_url(absolute)
        if root:
            candidates.add(root)
    return tuple(sorted(candidates))


def _page_url(
    api_url: str,
    query_parameters: Mapping[str, Any],
    *,
    page_parameter: str,
    page_size_parameter: str,
    page_number: int,
    page_size: int,
) -> str:
    parts = urlsplit(api_url)
    values = {str(key): value for key, value in query_parameters.items()}
    if page_parameter:
        values[page_parameter] = page_number
    if page_size_parameter:
        values[page_size_parameter] = page_size
    replaced_keys = set(values)
    pairs = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in replaced_keys
    ]
    pairs.extend((key, str(value).lower() if isinstance(value, bool) else str(value)) for key, value in values.items())
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(pairs), "")
    )


def _path_value(value: Any, path: str) -> Any:
    if path in {"", "$"}:
        return value
    current = value
    for segment in path.removeprefix("$.").split("."):
        if isinstance(current, Mapping) and segment in current:
            current = current[segment]
        else:
            return None
    return current


def _record_matches(
    record: Mapping[str, Any],
    filters: Sequence[Mapping[str, Any]],
    required_nonempty_paths: Sequence[str],
) -> bool:
    for path in required_nonempty_paths:
        value = _path_value(record, path)
        if value in (None, "", [], {}):
            return False
    for condition in filters:
        path = str(condition.get("path", "")).strip()
        if not path or "equals" not in condition:
            raise ValueError("each filter requires path and equals")
        if _path_value(record, path) != condition["equals"]:
            return False
    return True


def _is_iiif_manifest(value: Any, *, allow_legacy_shared_canvas: bool = False) -> bool:
    if not isinstance(value, Mapping):
        return False
    declared = value.get("type", value.get("@type"))
    types = declared if isinstance(declared, list) else [declared]
    has_manifest_type = any(
        isinstance(item, str)
        and item.rsplit("/", 1)[-1].rsplit("#", 1)[-1].split(":")[-1]
        == "Manifest"
        for item in types
    )
    if not has_manifest_type:
        return False
    contexts = value.get("@context")
    context_values = contexts if isinstance(contexts, list) else [contexts]
    if any(
        isinstance(item, str) and "iiif.io/api/presentation/" in item.casefold()
        for item in context_values
    ):
        return True
    # Explicit compatibility only: do not accept an arbitrary JSON context.
    legacy = {"http://www.shared-canvas.org/ns/context.json", "https://www.shared-canvas.org/ns/context.json"}
    return allow_legacy_shared_canvas and isinstance(value.get("sequences"), list) and any(
        isinstance(item, str) and item in legacy for item in context_values
    )


def _is_iiif_collection(value: Any) -> bool:
    """Require both a Collection declaration and a Presentation context."""
    if not isinstance(value, Mapping):
        return False
    declared = value.get("type", value.get("@type"))
    types = declared if isinstance(declared, list) else [declared]
    if not any(isinstance(t, str) and t.rsplit("/", 1)[-1].split(":")[-1] == "Collection" for t in types):
        return False
    contexts = value.get("@context")
    contexts = contexts if isinstance(contexts, list) else [contexts]
    return any(isinstance(t, str) and "iiif.io/api/presentation/" in t for t in contexts)


def _required_string(value: Mapping[str, Any], name: str) -> str:
    text = str(value.get(name, "")).strip()
    if not text:
        raise ValueError(f"{name} must be a non-empty string")
    return text


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _mapping_list(value: Any, name: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list) or any(not isinstance(item, Mapping) for item in value):
        raise ValueError(f"{name} must be an array of objects")
    return tuple(dict(item) for item in value)


def _string_list(value: Any, name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    output = tuple(str(item).strip() for item in value if str(item).strip())
    if not output and not allow_empty:
        raise ValueError(f"{name} must contain at least one string")
    return output


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a positive integer")
    result = int(value)
    if result < 1:
        raise ValueError(f"{name} must be a positive integer")
    return result


def _nonnegative_int(value: Any, name: str) -> int:
    """Allow zero-based offset pagination without changing page-based defaults."""
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a non-negative integer")
    result = int(value)
    if result < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return result
