"""Regression checks for routes learned during the 2026-10-15 audit."""

import json
from urllib.parse import parse_qs, urlsplit

from iiif_resource_discovery.discovery import DiscoveryLimits, ResourceDiscoverer
from iiif_resource_discovery.fetch import FetchedDocument, FetchError
from iiif_resource_discovery.models import ProviderInputRecord
from iiif_resource_discovery.skills import execute_skill, _path_values
from helpers import provider_value


BASE = "https://example.org"
CONTEXT = "http://iiif.io/api/presentation/2/context.json"


class FixtureFetcher:
    def __init__(self, values):
        self.values = values
        self.calls = []
        self.sleeper = lambda seconds: None

    def fetch(self, url, *, accept="application/json"):
        self.calls.append(url)
        parts = urlsplit(url)
        key = parts.path
        if key == "/api":
            key += "?page=" + parse_qs(parts.query)["page"][0]
        if key not in self.values:
            raise FetchError(url, "http_404", "Missing test route", 404)
        return FetchedDocument(url, url, 200, "application/json",
                               json.dumps(self.values[key]).encode())


def manifest(identifier):
    return {"@context": CONTEXT, "@type": "sc:Manifest", "@id": BASE + identifier,
            "label": "Test", "sequences": []}


def test_collection_first_then_next_is_traversed_and_cycles_stop():
    fetcher = FixtureFetcher({
        "/root": {"@context": CONTEXT, "@type": "sc:Collection",
                  "first": {"@id": BASE + "/page1"}},
        "/page1": {"@context": CONTEXT, "@type": "sc:Collection",
                   "manifests": [{"@id": BASE + "/m1", "@type": "sc:Manifest"}],
                   "next": BASE + "/page2", "first": BASE + "/page1"},
        "/page2": {"@context": CONTEXT, "@type": "sc:Collection",
                   "manifests": [{"@id": BASE + "/m2", "@type": "sc:Manifest"}],
                   "next": BASE + "/root"},
    })
    provider = ProviderInputRecord.from_mapping(provider_value(BASE + "/root", json_type="Collection"))
    result = ResourceDiscoverer(
        fetcher, limits=DiscoveryLimits(), html_enabled=False,
        omeka_s_probe_enabled=False,
    ).discover(provider)
    assert {row.manifest_url for row in result.manifests} == {BASE + "/m1", BASE + "/m2"}
    assert len(fetcher.calls) == 3


def link_skill():
    return {
        "skill_id": "nested-catalogue", "type": "paginated_json_manifest_links",
        "api_url": BASE + "/api", "records_path": "results",
        "manifest_url_path": "items.*.locations.*.url",
        "pagination": {"page_size": 1, "max_pages": 3},
        "request_delay_seconds": 0,
    }


def link_fetcher():
    def record(*urls):
        return {"items": [{"locations": [{"url": url} for url in urls]}]}
    return FixtureFetcher({
        "/api?page=1": {"results": [record(BASE + "/m1", BASE + "/m1", BASE + "/image-info")]},
        "/api?page=2": {"results": [record(BASE + "/m2")]},
        "/api?page=3": {"results": []},
        "/m1": manifest("/m1"), "/m2": manifest("/m2"),
        "/image-info": {"@context": "http://iiif.io/api/image/2/context.json", "width": 100},
    })


def test_nested_manifest_links_page_deduplicate_and_reject_image_api():
    result = execute_skill(link_skill(), link_fetcher(), investigation_id="test", max_manifests=10)
    assert [row.manifest_url for row in result.manifests] == [BASE + "/m1", BASE + "/m2"]
    assert result.audit["pages_fetched"] == 3
    assert result.audit["manifest_requests"] == 3
    assert result.audit["failure_counts"] == {"not_iiif_manifest": 1}
    assert result.truncated is False


def test_zero_based_offset_pagination_visits_distinct_batches():
    skill = link_skill()
    skill["pagination"].update(start_page=0, page_step=2, page_size=2)
    fetcher = FixtureFetcher({
        "/api?page=0": {"results": [
            {"items": [{"locations": [{"url": BASE + "/m1"}]}]},
            {"items": [{"locations": [{"url": BASE + "/m1"}]}]},
        ]},
        "/api?page=2": {"results": []},
        "/m1": manifest("/m1"),
    })
    result = execute_skill(skill, fetcher, investigation_id="offset-test", max_manifests=10)
    assert len(result.manifests) == 1
    assert result.audit["pages_fetched"] == 2
    assert any("page=2" in url for url in fetcher.calls)


def test_invalid_learned_html_pattern_is_audited_without_crashing():
    result = execute_skill({
        "skill_id": "bad-pattern", "type": "paginated_html_identifiers_to_manifest_templates",
        "api_url": BASE + "/catalogue", "record_url_pattern": "(",
    }, FixtureFetcher({}), investigation_id="bad-proposal", max_manifests=5)
    assert result.audit["status"] == "invalid_configuration"
    assert not result.manifests


def test_nested_link_skill_honours_manifest_budget():
    result = execute_skill(link_skill(), link_fetcher(), investigation_id="test", max_manifests=1)
    assert len(result.manifests) == 1
    assert result.truncated is True
    assert result.audit["pages_fetched"] == 1


def test_explicit_wildcard_paths_handle_missing_and_non_array_values():
    value = {"items": [{"locations": [{"url": "a"}, {}]}, {"locations": None}]}
    assert _path_values(value, "items.*.locations.*.url") == ["a"]
    assert _path_values(value, "items.0.locations.0.url") == ["a"]
    assert _path_values(value, "missing.*") == []


def test_link_skill_rejects_invalid_catalogue_shape():
    fetcher = FixtureFetcher({"/api?page=1": {"results": {"error": "not an array"}}})
    result = execute_skill(link_skill(), fetcher, investigation_id="test", max_manifests=5)
    assert not result.manifests
    assert result.issues[0].issue_type == "knowledge_api_shape"


def test_html_catalogue_extracts_named_identifiers_and_ignores_unrelated_links():
    class HtmlFetcher(FixtureFetcher):
        def fetch(self, url, *, accept="application/json"):
            if urlsplit(url).path == "/listing":
                self.calls.append(url)
                html = ('<a href="/record/lib/0001">One</a>'
                        '<a href="/record/lib/0001">Duplicate</a>'
                        '<a href="/record/lib/0002">Two</a>'
                        '<a href="/styles.css">Unrelated</a>')
                return FetchedDocument(url, url, 200, "text/html", html.encode())
            return super().fetch(url, accept=accept)
    fetcher = HtmlFetcher({"/lib-0001": manifest("/lib-0001"),
                           "/lib-0002": manifest("/lib-0002")})
    result = execute_skill({
        "skill_id": "html-records", "type": "paginated_html_identifiers_to_manifest_templates",
        "api_url": BASE + "/listing",
        "record_url_pattern": r"/record/(?P<library>[^/]+)/(?P<number>[^/?#]+)$",
        "identifier_template": "{library}-{number}",
        "manifest_url_templates": [BASE + "/{identifier}"],
        "pagination": {"page_size": 20, "max_pages": 1},
        "max_identifiers": 10, "request_delay_seconds": 0,
    }, fetcher, investigation_id="test", max_manifests=10)
    assert [row.manifest_url for row in result.manifests] == [BASE + "/lib-0001", BASE + "/lib-0002"]
    assert result.audit["identifiers_selected"] == 2
    assert result.audit["skill_type"] == "paginated_html_identifiers_to_manifest_templates"
