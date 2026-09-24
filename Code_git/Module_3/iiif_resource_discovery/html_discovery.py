"""Bounded HTML inspection for declared or embedded IIIF resource links."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
import re
import time
from typing import Any, Callable, Iterable, Mapping, Optional
from urllib.parse import urljoin, urlsplit

from .fetch import FetchError, HttpFetcher, is_json_document, normalized_media_type
from .models import DiscoveryIssue, canonicalize_url


URL_PATTERN = re.compile(r"https?://[^\s\"'<>\\]+", re.IGNORECASE)
DISCOVERY_TERMS = (
    "manifest",
    "iiif",
    "collection",
    "activity",
    "presentation",
)
CRAWL_TERMS = DISCOVERY_TERMS + (
    "digital",
    "object",
    "item",
    "record",
    "viewer",
    "manuscript",
    "archive",
)
SKIPPED_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".css",
    ".js",
    ".woff",
    ".woff2",
    ".ttf",
    ".pdf",
    ".zip",
)


@dataclass(frozen=True)
class HtmlCandidate:
    """A likely machine-readable URL and the HTML page that exposed it."""

    url: str
    source_page: str
    method: str = "html_declared_link"


@dataclass
class HtmlDiscoveryResult:
    """Candidates and audit information from one bounded HTML crawl."""

    candidates: list[HtmlCandidate] = field(default_factory=list)
    pages_visited: int = 0
    issues: list[DiscoveryIssue] = field(default_factory=list)
    truncated: bool = False


class _LinkParser(HTMLParser):
    """Collect candidate machine links, crawl links, and JSON-LD blocks."""

    def __init__(self, page_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.machine_candidates: list[str] = []
        self.crawl_links: list[tuple[str, str]] = []
        self._json_ld_depth = 0
        self._json_ld_parts: list[str] = []
        self.json_ld_blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        values = {name.casefold(): value or "" for name, value in attrs}
        tag = tag.casefold()
        if tag == "script" and "ld+json" in values.get("type", "").casefold():
            self._json_ld_depth += 1
            self._json_ld_parts = []

        for name, raw_value in values.items():
            if not raw_value:
                continue
            if name in {"href", "src", "data-manifest", "data-iiif-manifest", "data-manifest-uri"}:
                absolute = _absolute_http_url(self.page_url, raw_value)
                if not absolute:
                    continue
                if tag == "a" and name == "href":
                    self.crawl_links.append((absolute, values.get("title", "")))
                if _strong_machine_candidate(tag, name, absolute, values):
                    self.machine_candidates.append(absolute)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "script" and self._json_ld_depth:
            self._json_ld_depth -= 1
            self.json_ld_blocks.append("".join(self._json_ld_parts))
            self._json_ld_parts = []

    def handle_data(self, data: str) -> None:
        if self._json_ld_depth:
            self._json_ld_parts.append(data)
        for match in URL_PATTERN.findall(data):
            if _url_contains_discovery_term(match):
                self.machine_candidates.append(match.rstrip(".,);]"))


def discover_html_candidates(
    start_url: str,
    fetcher: HttpFetcher,
    *,
    max_pages: int,
    max_depth: int,
    max_candidates_per_page: int,
    same_host_only: bool,
    delay_seconds: float = 0.1,
    sleeper: Callable[[float], None] = time.sleep,
) -> HtmlDiscoveryResult:
    """Inspect a small, deterministic subset of pages for IIIF links."""

    if max_pages < 1 or max_depth < 0 or max_candidates_per_page < 1:
        raise ValueError("HTML discovery limits are invalid")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must be non-negative")

    start = canonicalize_url(start_url)
    queue: list[tuple[str, int]] = [(start, 0)]
    queued = {start}
    visited: set[str] = set()
    candidate_keys: set[str] = set()
    result = HtmlDiscoveryResult()

    while queue and result.pages_visited < max_pages:
        page_url, depth = queue.pop(0)
        if page_url in visited:
            continue
        if result.pages_visited and delay_seconds:
            sleeper(delay_seconds)
        visited.add(page_url)
        try:
            document = fetcher.fetch(
                page_url,
                accept="text/html, application/xhtml+xml, application/ld+json;q=0.8, application/json;q=0.8",
            )
        except FetchError as exc:
            result.issues.append(DiscoveryIssue(exc.url, exc.error_type, str(exc)))
            continue
        result.pages_visited += 1

        if is_json_document(document):
            _add_candidate(
                result,
                candidate_keys,
                HtmlCandidate(document.final_url, page_url, "html_link_resolved_to_json"),
            )
            continue
        media_type = normalized_media_type(document.content_type)
        if media_type and media_type not in {"text/html", "application/xhtml+xml"}:
            continue
        try:
            text = document.text()
        except FetchError as exc:
            result.issues.append(DiscoveryIssue(exc.url, exc.error_type, str(exc)))
            continue

        parser = _LinkParser(document.final_url)
        try:
            parser.feed(text)
            parser.close()
        except Exception as exc:  # HTMLParser can encounter malformed publisher markup.
            result.issues.append(
                DiscoveryIssue(document.final_url, "html_parse_error", str(exc)[:500])
            )

        page_candidates = list(parser.machine_candidates)
        for block in parser.json_ld_blocks:
            page_candidates.extend(_urls_from_json_ld(block, document.final_url))
        for candidate_url in _unique_urls(page_candidates)[:max_candidates_per_page]:
            _add_candidate(
                result,
                candidate_keys,
                HtmlCandidate(candidate_url, document.final_url),
            )

        if depth >= max_depth:
            continue
        crawl_links = sorted(
            _unique_crawl_links(parser.crawl_links),
            key=lambda item: (-_crawl_score(item[0], item[1]), item[0]),
        )
        for crawl_url, _label in crawl_links:
            if same_host_only and not _same_site(start, crawl_url):
                continue
            if not _eligible_crawl_url(crawl_url, _label):
                continue
            canonical = canonicalize_url(crawl_url)
            if canonical not in queued and canonical not in visited:
                if len(queued) >= max_pages:
                    result.truncated = True
                    break
                queue.append((canonical, depth + 1))
                queued.add(canonical)

    if queue:
        result.truncated = True
    return result


def _strong_machine_candidate(
    tag: str,
    attribute_name: str,
    url: str,
    attributes: Mapping[str, str],
) -> bool:
    if "manifest" in attribute_name or "iiif" in attribute_name:
        return True
    declared_type = attributes.get("type", "").casefold()
    rel = attributes.get("rel", "").casefold()
    if tag == "link" and (
        "json" in declared_type or "alternate" in rel or "manifest" in rel
    ):
        return True
    return _url_contains_discovery_term(url)


def _urls_from_json_ld(value: str, base_url: str) -> list[str]:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return []
    results: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            resource_type = _normalized_type(item.get("type", item.get("@type")))
            resource_id = item.get("id", item.get("@id"))
            if resource_type in {"Manifest", "Collection", "OrderedCollection", "OrderedCollectionPage"}:
                if isinstance(resource_id, str):
                    absolute = _absolute_http_url(base_url, resource_id)
                    if absolute:
                        results.append(absolute)
            for key, child in item.items():
                if key.casefold() in {"manifest", "manifesturl", "iiifmanifest", "iiif_manifest"}:
                    if isinstance(child, str):
                        absolute = _absolute_http_url(base_url, child)
                        if absolute:
                            results.append(absolute)
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(decoded)
    return results


def _normalized_type(value: Any) -> Optional[str]:
    if isinstance(value, list):
        for item in value:
            result = _normalized_type(item)
            if result:
                return result
        return None
    if not isinstance(value, str):
        return None
    return re.split(r"[/#:]", value)[-1]


def _absolute_http_url(base_url: str, value: str) -> Optional[str]:
    try:
        absolute = urljoin(base_url, value.strip())
        return canonicalize_url(absolute)
    except (ValueError, TypeError):
        return None


def _url_contains_discovery_term(url: str) -> bool:
    lowered = url.casefold()
    return any(term in lowered for term in DISCOVERY_TERMS)


def _eligible_crawl_url(url: str, label: str) -> bool:
    path = urlsplit(url).path.casefold()
    if path.endswith(SKIPPED_EXTENSIONS):
        return False
    text = f"{url} {label}".casefold()
    return any(term in text for term in CRAWL_TERMS)


def _crawl_score(url: str, label: str) -> int:
    text = f"{url} {label}".casefold()
    return sum(3 if term in DISCOVERY_TERMS else 1 for term in CRAWL_TERMS if term in text)


def _same_site(first_url: str, second_url: str) -> bool:
    first = (urlsplit(first_url).hostname or "").casefold().removeprefix("www.")
    second = (urlsplit(second_url).hostname or "").casefold().removeprefix("www.")
    return bool(first and first == second)


def _unique_urls(values: Iterable[str]) -> list[str]:
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


def _unique_crawl_links(values: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    seen: set[str] = set()
    for url, label in values:
        try:
            canonical = canonicalize_url(url)
        except ValueError:
            continue
        if canonical not in seen:
            output.append((canonical, label))
            seen.add(canonical)
    return output


def _add_candidate(
    result: HtmlDiscoveryResult,
    keys: set[str],
    candidate: HtmlCandidate,
) -> None:
    try:
        canonical = canonicalize_url(candidate.url)
    except ValueError:
        return
    if canonical in keys:
        return
    result.candidates.append(HtmlCandidate(canonical, candidate.source_page, candidate.method))
    keys.add(canonical)
