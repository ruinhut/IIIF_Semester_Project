"""Resolve machine-readable IIIF endpoints and discover Manifest URLs."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Optional, Sequence

from .fetch import FetchError, HttpFetcher, is_json_document
from .html_discovery import discover_html_candidates
from .models import (
    DiscoveryEvidence,
    DiscoveryIssue,
    ManifestFinding,
    ProviderDiscoveryResult,
    ProviderInputRecord,
    ResolvedEndpoint,
    canonicalize_url,
)
from .skills import execute_omeka_s_probe, execute_skill


ACTIVE_ACTIVITY_TYPES = {"Create", "Update", "Add", "Move"}
REMOVAL_ACTIVITY_TYPES = {"Delete", "Remove"}
IIIF_RESOURCE_TYPES = {"Manifest", "Collection", "OrderedCollection", "OrderedCollectionPage"}


@dataclass(frozen=True)
class DiscoveryLimits:
    """Hard bounds that keep remote traversal finite and reproducible."""

    max_stream_pages_per_provider: int = 5
    max_collections_per_provider: int = 20
    max_html_pages_per_provider: int = 3
    max_html_depth: int = 1
    max_candidates_per_html_page: int = 50
    max_machine_candidates_per_provider: int = 20
    max_manifests_per_provider: int = 100

    def __post_init__(self) -> None:
        positive = (
            self.max_stream_pages_per_provider,
            self.max_collections_per_provider,
            self.max_html_pages_per_provider,
            self.max_candidates_per_html_page,
            self.max_machine_candidates_per_provider,
            self.max_manifests_per_provider,
        )
        if any(value < 1 for value in positive) or self.max_html_depth < 0:
            raise ValueError("Discovery limits must be positive; max_html_depth may be zero")


@dataclass
class _DiscoveryState:
    manifest_urls: set[str] = field(default_factory=set)
    manifest_finding_keys: set[tuple[Any, ...]] = field(default_factory=set)
    resolved_endpoint_keys: set[tuple[str, str]] = field(default_factory=set)
    processed_machine_urls: set[str] = field(default_factory=set)
    processed_collection_urls: set[str] = field(default_factory=set)
    processed_stream_pages: set[str] = field(default_factory=set)


class ResourceDiscoverer:
    """Implement Module 3A endpoint resolution and Module 3B resource discovery."""

    def __init__(
        self,
        fetcher: HttpFetcher,
        *,
        limits: DiscoveryLimits | None = None,
        html_enabled: bool = True,
        same_host_only: bool = True,
        html_delay_seconds: float = 0.1,
        omeka_s_probe_enabled: bool = True,
    ) -> None:
        if html_delay_seconds < 0:
            raise ValueError("html_delay_seconds must be non-negative")
        self.fetcher = fetcher
        self.limits = limits or DiscoveryLimits()
        self.html_enabled = html_enabled
        self.same_host_only = same_host_only
        self.html_delay_seconds = html_delay_seconds
        self.omeka_s_probe_enabled = omeka_s_probe_enabled

    def discover(
        self,
        provider: ProviderInputRecord,
        *,
        curated_entry_points: Sequence[str] = (),
        curated_html_seeds: Sequence[str] = (),
        knowledge_skills: Sequence[Mapping[str, Any]] = (),
        investigation_id: str | None = None,
    ) -> ProviderDiscoveryResult:
        """Discover a bounded, deduplicated set of Manifests for one provider."""

        result = ProviderDiscoveryResult(provider=provider)
        state = _DiscoveryState()
        candidates: dict[str, tuple[str, str]] = {}
        html_seeds: list[str] = []

        for url in curated_entry_points:
            self._queue_candidate(candidates, url, "curated_entry", url, result)
        for url in curated_html_seeds:
            try:
                html_seeds.append(canonicalize_url(url))
            except ValueError as exc:
                result.issues.append(DiscoveryIssue(str(url), "invalid_curated_url", str(exc)))

        processable_route_found = False
        for route in provider.endpoint_routes:
            candidate = route["endpoint_candidate"]
            check = route["endpoint_check"]
            candidate_url = str(
                candidate.get("url", check.get("requested_url", ""))
            )
            final_url = str(check.get("final_url") or candidate_url)
            check_result = str(check.get("check_result", ""))
            endpoint_role = str(
                candidate.get("endpoint_role", "unclassified")
            )
            if check_result == "reachable_json":
                self._queue_candidate(
                    candidates,
                    final_url,
                    f"module_2_json:{endpoint_role}",
                    candidate_url,
                    result,
                )
                processable_route_found = True
            elif check_result == "reachable_non_json" and self.html_enabled:
                html_seeds.append(final_url)
                processable_route_found = True
            elif check_result in {"invalid_json", "response_too_large", "restricted"}:
                result.issues.append(
                    DiscoveryIssue(
                        final_url,
                        f"module_2_{check_result}",
                        f"Endpoint role {endpoint_role!r} requires review or an adapter",
                    )
                )
            elif check_result:
                result.issues.append(
                    DiscoveryIssue(
                        final_url,
                        f"module_2_{check_result}",
                        f"Endpoint role {endpoint_role!r} was not reachable",
                    )
                )

        if (
            not processable_route_found
            and not curated_entry_points
            and not curated_html_seeds
        ):
            result.issues.append(
                DiscoveryIssue(
                    provider.discovery_endpoint,
                    "no_processable_entry",
                    "No checked endpoint is currently processable",
                )
            )

        for url, (method, source_url) in list(candidates.items()):
            if self._manifest_limit_reached(result, state):
                result.truncated = True
                break
            self._process_machine_candidate(url, method, source_url, result, state)

        knowledge_succeeded = False
        if knowledge_skills and not state.manifest_urls:
            for skill in knowledge_skills:
                remaining = (
                    self.limits.max_manifests_per_provider
                    - len(state.manifest_urls)
                )
                if remaining <= 0:
                    result.truncated = True
                    break
                execution = execute_skill(
                    skill,
                    self.fetcher,
                    investigation_id=investigation_id or "unrecorded-investigation",
                    max_manifests=remaining,
                )
                result.knowledge_application.append(execution.audit)
                result.issues.extend(execution.issues)
                result.truncated = result.truncated or execution.truncated
                for manifest in execution.manifests:
                    method = f"knowledge_skill:{manifest.skill_id}"
                    self._add_resolved(
                        result,
                        state,
                        manifest.manifest_url,
                        "Manifest",
                        method,
                        manifest.source_url,
                    )
                    self._add_manifest(
                        result,
                        state,
                        manifest.manifest_url,
                        discovery_method=method,
                        source_url=manifest.source_url,
                    )
                for entry in execution.entry_points:
                    if self._manifest_limit_reached(result, state):
                        result.truncated = True
                        break
                    self._process_machine_candidate(
                        entry.endpoint_url, f"knowledge_skill:{entry.skill_id}",
                        entry.source_url, result, state,
                    )
            knowledge_succeeded = bool(state.manifest_urls)
        elif knowledge_skills:
            result.knowledge_application.extend(
                {
                    "investigation_id": investigation_id,
                    "skill_id": str(skill.get("skill_id", "unnamed-skill")),
                    "skill_type": str(skill.get("type", "")) or None,
                    "status": "skipped_existing_manifests",
                }
                for skill in knowledge_skills
            )

        if (
            self.omeka_s_probe_enabled
            and not state.manifest_urls
            and html_seeds
        ):
            execution = execute_omeka_s_probe(
                _deduplicated_urls(html_seeds),
                self.fetcher,
                max_manifests=self.limits.max_manifests_per_provider,
                request_delay_seconds=self.html_delay_seconds,
            )
            if execution is not None:
                result.knowledge_application.append(execution.audit)
                result.issues.extend(execution.issues)
                result.truncated = result.truncated or execution.truncated
                for manifest in execution.manifests:
                    method = f"platform_skill:{manifest.skill_id}"
                    self._add_resolved(
                        result,
                        state,
                        manifest.manifest_url,
                        "Manifest",
                        method,
                        manifest.source_url,
                    )
                    self._add_manifest(
                        result,
                        state,
                        manifest.manifest_url,
                        discovery_method=method,
                        source_url=manifest.source_url,
                    )
                knowledge_succeeded = knowledge_succeeded or bool(
                    execution.manifests
                )

        if self.html_enabled and not knowledge_succeeded:
            for seed in _deduplicated_urls(html_seeds):
                html_result = discover_html_candidates(
                    seed,
                    self.fetcher,
                    max_pages=self.limits.max_html_pages_per_provider,
                    max_depth=self.limits.max_html_depth,
                    max_candidates_per_page=self.limits.max_candidates_per_html_page,
                    same_host_only=self.same_host_only,
                    delay_seconds=self.html_delay_seconds,
                )
                result.html_pages_visited += html_result.pages_visited
                result.issues.extend(html_result.issues)
                result.truncated = result.truncated or html_result.truncated
                for candidate in html_result.candidates:
                    self._queue_candidate(
                        candidates,
                        candidate.url,
                        candidate.method,
                        candidate.source_page,
                        result,
                    )

            for url, (method, source_url) in list(candidates.items()):
                if self._manifest_limit_reached(result, state):
                    result.truncated = True
                    break
                self._process_machine_candidate(
                    url, method, source_url, result, state
                )

        if state.manifest_urls:
            result.status = "manifests_found"
        elif result.resolved_endpoints:
            result.status = "resolved_no_manifests"
        else:
            result.status = "unresolved"
        return result

    def _process_machine_candidate(
        self,
        url: str,
        method: str,
        source_url: str,
        result: ProviderDiscoveryResult,
        state: _DiscoveryState,
    ) -> None:
        canonical = canonicalize_url(url)
        if canonical in state.processed_machine_urls:
            return
        state.processed_machine_urls.add(canonical)
        document_and_json = self._fetch_json(canonical, result)
        if document_and_json is None:
            return
        final_url, value = document_and_json
        resource_type = _resource_type(value)
        if resource_type not in IIIF_RESOURCE_TYPES:
            linked_candidates = _json_iiif_candidates(value)
            if linked_candidates:
                for linked_url in linked_candidates:
                    if (
                        len(state.processed_machine_urls)
                        >= self.limits.max_machine_candidates_per_provider
                    ):
                        result.truncated = True
                        break
                    self._process_machine_candidate(
                        linked_url,
                        "provider_api_link",
                        final_url,
                        result,
                        state,
                    )
            else:
                result.issues.append(
                    DiscoveryIssue(
                        final_url,
                        "unsupported_json_type",
                        f"JSON type is {resource_type or 'unknown'} and no IIIF links were found",
                    )
                )
            return
        if not _has_iiif_declared_type(value, resource_type):
            result.issues.append(
                DiscoveryIssue(
                    final_url,
                    "non_iiif_json_resource",
                    f"JSON type {resource_type!r} is not declared in an IIIF or ActivityStreams vocabulary",
                )
            )
            return
        self._add_resolved(result, state, final_url, resource_type, method, source_url)

        if resource_type == "Manifest":
            self._add_manifest(
                result,
                state,
                final_url,
                discovery_method=method,
                source_url=source_url,
            )
        elif resource_type in {"OrderedCollection", "OrderedCollectionPage"}:
            self._walk_activity_stream(final_url, value, resource_type, result, state)
        elif resource_type == "Collection":
            self._walk_collections(
                [(final_url, value, method, source_url, None, None)], result, state
            )

    def _walk_activity_stream(
        self,
        initial_url: str,
        initial_value: Any,
        initial_type: str,
        result: ProviderDiscoveryResult,
        state: _DiscoveryState,
    ) -> None:
        if not isinstance(initial_value, Mapping):
            result.issues.append(DiscoveryIssue(initial_url, "invalid_stream", "Stream JSON must be an object"))
            return

        page_queue: list[tuple[str, Optional[Mapping[str, Any]], str]] = []
        if initial_type == "OrderedCollectionPage":
            direction = "prev" if _link_url(initial_value.get("prev")) else "next"
            page_queue.append((initial_url, initial_value, direction))
        else:
            self._process_activities(initial_value, initial_url, result, state)
            last_url = _link_url(initial_value.get("last"))
            first_url = _link_url(initial_value.get("first"))
            if last_url:
                page_queue.append((last_url, None, "prev"))
            elif first_url:
                page_queue.append((first_url, None, "next"))
            else:
                result.issues.append(
                    DiscoveryIssue(initial_url, "stream_has_no_pages", "OrderedCollection has neither last nor first")
                )

        while page_queue and result.stream_pages_visited < self.limits.max_stream_pages_per_provider:
            page_url, embedded, direction = page_queue.pop(0)
            page_url = canonicalize_url(page_url)
            if page_url in state.processed_stream_pages:
                continue
            state.processed_stream_pages.add(page_url)
            if embedded is None:
                fetched = self._fetch_json(page_url, result)
                if fetched is None:
                    continue
                final_url, page_value = fetched
                if not isinstance(page_value, Mapping):
                    result.issues.append(DiscoveryIssue(final_url, "invalid_stream_page", "Page must be a JSON object"))
                    continue
                page_url = final_url
            else:
                page_value = embedded
            result.stream_pages_visited += 1
            self._add_resolved(
                result,
                state,
                page_url,
                _resource_type(page_value) or "OrderedCollectionPage",
                "change_discovery_page",
                initial_url,
            )
            self._process_activities(page_value, page_url, result, state)
            if self._manifest_limit_reached(result, state):
                result.truncated = True
                break
            next_page = _link_url(page_value.get(direction))
            if next_page:
                page_queue.append((next_page, None, direction))

        if page_queue:
            result.truncated = True

    def _process_activities(
        self,
        page_value: Mapping[str, Any],
        page_url: str,
        result: ProviderDiscoveryResult,
        state: _DiscoveryState,
    ) -> None:
        activities = page_value.get("orderedItems", [])
        if activities is None:
            activities = []
        if not isinstance(activities, list):
            result.issues.append(
                DiscoveryIssue(page_url, "invalid_ordered_items", "orderedItems must be an array")
            )
            return
        for activity in activities:
            if not isinstance(activity, Mapping):
                continue
            activity_type = _resource_type(activity)
            if activity_type in REMOVAL_ACTIVITY_TYPES:
                continue
            if activity_type and activity_type not in ACTIVE_ACTIVITY_TYPES:
                continue
            object_value = activity.get("object")
            object_url = _link_url(object_value)
            object_type = _resource_type(object_value)
            activity_time = _optional_string(
                activity.get("endTime", activity.get("startTime"))
            )
            if not object_url:
                continue
            if object_type == "Manifest":
                self._add_manifest(
                    result,
                    state,
                    object_url,
                    discovery_method="change_discovery",
                    source_url=page_url,
                    activity_type=activity_type,
                    activity_time=activity_time,
                )
            elif object_type == "Collection":
                self._walk_collections(
                    [(object_url, None, "change_discovery_collection", page_url, activity_type, activity_time)],
                    result,
                    state,
                )
            if self._manifest_limit_reached(result, state):
                return

    def _walk_collections(
        self,
        queue: list[tuple[str, Optional[Mapping[str, Any]], str, str, Optional[str], Optional[str]]],
        result: ProviderDiscoveryResult,
        state: _DiscoveryState,
    ) -> None:
        while queue and result.collections_visited < self.limits.max_collections_per_provider:
            collection_url, embedded, method, source_url, activity_type, activity_time = queue.pop(0)
            collection_url = canonicalize_url(collection_url)
            if collection_url in state.processed_collection_urls:
                continue
            state.processed_collection_urls.add(collection_url)
            if embedded is None:
                fetched = self._fetch_json(collection_url, result)
                if fetched is None:
                    continue
                final_url, value = fetched
            else:
                final_url, value = collection_url, embedded
            resource_type = _resource_type(value)
            if resource_type == "Manifest":
                self._add_manifest(
                    result,
                    state,
                    final_url,
                    discovery_method=method,
                    source_url=source_url,
                    activity_type=activity_type,
                    activity_time=activity_time,
                )
                continue
            if resource_type != "Collection" or not isinstance(value, Mapping):
                result.issues.append(
                    DiscoveryIssue(final_url, "not_a_collection", f"Expected Collection, got {resource_type or 'unknown'}")
                )
                continue

            result.collections_visited += 1
            self._add_resolved(result, state, final_url, "Collection", method, source_url)
            children = _collection_children(value)
            for child_url, child_type, child_value in children:
                if child_type == "Manifest":
                    self._add_manifest(
                        result,
                        state,
                        child_url,
                        discovery_method="presentation_collection",
                        source_url=final_url,
                        activity_type=activity_type,
                        activity_time=activity_time,
                    )
                elif child_type == "Collection":
                    embedded_child = child_value if _has_collection_children(child_value) else None
                    queue.append(
                        (
                            child_url,
                            embedded_child,
                            "presentation_collection",
                            final_url,
                            activity_type,
                            activity_time,
                        )
                    )
                if self._manifest_limit_reached(result, state):
                    result.truncated = True
                    return

            # CONTENTdm and other Presentation 2 providers expose an empty
            # Collection wrapper whose actual members begin at `first`.
            # Follow both relations within the same visited set and budget.
            for relation in ("first", "next"):
                page_url = _link_url(value.get(relation))
                if page_url and page_url not in state.processed_collection_urls:
                    queue.append(
                        (
                            page_url,
                            None,
                            f"presentation_collection_{relation}",
                            final_url,
                            activity_type,
                            activity_time,
                        )
                    )
        if queue:
            result.truncated = True

    def _fetch_json(
        self, url: str, result: ProviderDiscoveryResult
    ) -> Optional[tuple[str, Any]]:
        try:
            document = self.fetcher.fetch(
                url,
                accept="application/activity+json, application/ld+json, application/json;q=0.9",
            )
            if not is_json_document(document):
                result.issues.append(
                    DiscoveryIssue(document.final_url, "not_json", "Candidate did not return JSON")
                )
                return None
            return canonicalize_url(document.final_url), document.json()
        except FetchError as exc:
            result.issues.append(DiscoveryIssue(exc.url, exc.error_type, str(exc)))
            return None

    def _add_manifest(
        self,
        result: ProviderDiscoveryResult,
        state: _DiscoveryState,
        manifest_url: str,
        *,
        discovery_method: str,
        source_url: str,
        activity_type: Optional[str] = None,
        activity_time: Optional[str] = None,
    ) -> None:
        try:
            canonical = canonicalize_url(manifest_url)
        except ValueError as exc:
            result.issues.append(DiscoveryIssue(str(manifest_url), "invalid_manifest_url", str(exc)))
            return
        if canonical not in state.manifest_urls and len(state.manifest_urls) >= self.limits.max_manifests_per_provider:
            result.truncated = True
            return
        evidence = DiscoveryEvidence(
            provider_id=result.provider.provider_id,
            provider_name=result.provider.name,
            discovery_method=discovery_method,
            source_url=canonicalize_url(source_url),
            activity_type=activity_type,
            activity_time=activity_time,
        )
        finding_key = (
            canonical,
            evidence.discovery_method,
            evidence.source_url,
            evidence.activity_type,
            evidence.activity_time,
        )
        # Preserve distinct evidence without rescanning every previous finding.
        # Rebuilding that set for each item made a large catalogue quadratic.
        if finding_key not in state.manifest_finding_keys:
            result.manifests.append(ManifestFinding(canonical, evidence))
            state.manifest_finding_keys.add(finding_key)
        state.manifest_urls.add(canonical)

    def _add_resolved(
        self,
        result: ProviderDiscoveryResult,
        state: _DiscoveryState,
        url: str,
        resource_type: str,
        method: str,
        source_url: str,
    ) -> None:
        endpoint = ResolvedEndpoint(url, resource_type, method, canonicalize_url(source_url))
        key = (endpoint.endpoint_url, endpoint.resource_type)
        if key not in state.resolved_endpoint_keys:
            result.resolved_endpoints.append(endpoint)
            state.resolved_endpoint_keys.add(key)

    def _queue_candidate(
        self,
        candidates: dict[str, tuple[str, str]],
        url: str,
        method: str,
        source_url: str,
        result: ProviderDiscoveryResult,
    ) -> None:
        try:
            canonical = canonicalize_url(url)
            source = canonicalize_url(source_url)
        except ValueError as exc:
            result.issues.append(DiscoveryIssue(str(url), "invalid_candidate_url", str(exc)))
            return
        if (
            canonical not in candidates
            and len(candidates) >= self.limits.max_machine_candidates_per_provider
        ):
            result.truncated = True
            return
        candidates.setdefault(canonical, (method, source))

    def _manifest_limit_reached(
        self, result: ProviderDiscoveryResult, state: _DiscoveryState
    ) -> bool:
        reached = len(state.manifest_urls) >= self.limits.max_manifests_per_provider
        if reached:
            result.truncated = True
        return reached


ProviderDiscovery = ProviderDiscoveryResult


def _resource_type(value: Any) -> Optional[str]:
    if isinstance(value, Mapping):
        value = value.get("type", value.get("@type"))
    if isinstance(value, list):
        for item in value:
            result = _resource_type(item)
            if result:
                return result
        return None
    if not isinstance(value, str):
        return None
    return re.split(r"[/#:]", value)[-1]


def _has_iiif_declared_type(value: Any, resource_type: str) -> bool:
    """Reject unrelated JSON-LD types whose local name resembles an IIIF type.

    For example, Digital Bodleian also publishes ``db:Collection`` JSON-LD.
    Its local name is ``Collection``, but it is not an IIIF Presentation
    Collection and must not be counted as a resolved IIIF endpoint.
    """

    if not isinstance(value, Mapping):
        return False
    declared = value.get("type", value.get("@type"))
    declared_values = declared if isinstance(declared, list) else [declared]
    accepted_compact = {resource_type, f"sc:{resource_type}", f"as:{resource_type}"}
    for item in declared_values:
        if not isinstance(item, str):
            continue
        if item in accepted_compact:
            return True
        lowered = item.casefold()
        if (
            _resource_type(item) == resource_type
            and ("iiif.io/" in lowered or "w3.org/ns/activitystreams" in lowered)
        ):
            return True

    contexts = value.get("@context")
    context_values = contexts if isinstance(contexts, list) else [contexts]
    return any(
        isinstance(item, str)
        and ("iiif.io/" in item.casefold() or "w3.org/ns/activitystreams" in item.casefold())
        for item in context_values
    )


def _link_url(value: Any) -> Optional[str]:
    if isinstance(value, str):
        try:
            return canonicalize_url(value)
        except ValueError:
            return None
    if isinstance(value, Mapping):
        identifier = value.get("id", value.get("@id"))
        if isinstance(identifier, str):
            try:
                return canonicalize_url(identifier)
            except ValueError:
                return None
    return None


def _collection_children(
    value: Mapping[str, Any],
) -> list[tuple[str, Optional[str], Optional[Mapping[str, Any]]]]:
    output: list[tuple[str, Optional[str], Optional[Mapping[str, Any]]]] = []
    for field_name, implied_type in (
        ("items", None),
        ("members", None),
        ("manifests", "Manifest"),
        ("collections", "Collection"),
    ):
        children = value.get(field_name, [])
        if not isinstance(children, list):
            continue
        for child in children:
            child_url = _link_url(child)
            if not child_url:
                continue
            child_type = _resource_type(child) or implied_type
            child_mapping = child if isinstance(child, Mapping) else None
            output.append((child_url, child_type, child_mapping))
    return output


def _has_collection_children(value: Optional[Mapping[str, Any]]) -> bool:
    if not value:
        return False
    return any(isinstance(value.get(name), list) for name in ("items", "members", "manifests", "collections"))




def _json_iiif_candidates(value: Any) -> list[str]:
    """Extract explicit IIIF-looking URLs from a provider-specific JSON API.

    This is a conservative generic adapter: a URL is considered only when its
    field name or value explicitly mentions IIIF, Manifest, or Collection.
    """

    output: list[str] = []
    seen: set[str] = set()

    def visit(item: Any, key_hint: str = "") -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                visit(child, str(key))
            return
        if isinstance(item, list):
            for child in item:
                visit(child, key_hint)
            return
        if not isinstance(item, str):
            return
        evidence = f"{key_hint} {item}".casefold()
        if not any(token in evidence for token in ("iiif", "manifest", "collection")):
            return
        try:
            canonical = canonicalize_url(item)
        except ValueError:
            return
        if canonical not in seen:
            output.append(canonical)
            seen.add(canonical)

    visit(value)
    return output

def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _deduplicated_urls(values: Sequence[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        try:
            canonical = canonicalize_url(value)
        except ValueError:
            continue
        if canonical not in seen:
            output.append(canonical)
            seen.add(canonical)
    return output
