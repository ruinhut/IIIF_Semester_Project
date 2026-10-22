"""Exercise catalogue families, access labels, and Collection handoffs."""

import json
from urllib.parse import parse_qs, urlsplit

from helpers import provider_value
from iiif_resource_discovery.discovery import ResourceDiscoverer
from iiif_resource_discovery.fetch import FetchError, FetchedDocument
from iiif_resource_discovery.models import ProviderInputRecord
from iiif_resource_discovery.skills import execute_skill


BASE = "https://example.org"
CONTEXT = "http://iiif.io/api/presentation/2/context.json"


def manifest(number):
    return {"@context": CONTEXT, "@type": "sc:Manifest", "@id": f"{BASE}/m/{number}"}


class Fetcher:
    """A fixture site with explicit failed detail routes and HTML catalogues."""

    sleeper = staticmethod(lambda seconds: None)

    def __init__(self, documents):
        self.documents = documents
        self.calls = []

    def fetch(self, url, **kwargs):
        self.calls.append(url)
        parts = urlsplit(url)
        key = parts.path
        if parts.path == "/api" or parts.path == "/listing":
            key += "?page=" + parse_qs(parts.query).get("page", ["1"])[0]
        value = self.documents.get(key)
        if value is None:
            raise FetchError(url, "http_500", "Unavailable fixture", 500)
        body = value.encode() if isinstance(value, str) else json.dumps(value).encode()
        content_type = "text/html" if isinstance(value, str) else "application/json"
        return FetchedDocument(url, url, 200, content_type, body)


def identifier_skill():
    return {"skill_id": "generic-identifiers", "type": "paginated_json_identifiers_to_manifest_templates",
            "api_url": BASE + "/api", "records_path": "records", "identifier_path": "id",
            "manifest_url_templates": [BASE + "/m/{identifier}"],
            "pagination": {"page_size": 10, "max_pages": 2}, "max_identifiers": 20}


def test_detail_api_failure_does_not_lose_other_parent_records():
    skill = identifier_skill()
    skill["identifier_followup"] = {"url_template": BASE + "/details/{identifier}",
                                    "records_path": "$", "identifier_path": "href"}
    fetcher = Fetcher({"/api?page=1": {"records": [{"id": "bad"}, {"id": "a"}, {"id": "b"}]},
                       "/details/a": [{"href": "1"}, {"href": "1"}],
                       "/details/b": [{"href": "1"}, {"href": "2"}],
                       "/m/1": manifest(1), "/m/2": manifest(2)})
    result = execute_skill(skill, fetcher, investigation_id="detail-test", max_manifests=10)
    assert [m.manifest_url for m in result.manifests] == [BASE + "/m/1", BASE + "/m/2"]
    assert result.audit["followup_requests"] == 3
    assert result.audit["failure_counts"]["http_500"] == 1
    assert fetcher.calls.count(BASE + "/m/1") == 1


def test_catalogue_url_array_becomes_a_collection_root_then_real_manifests():
    skill = identifier_skill()
    skill.update(identifier_path="links.*", identifier_pattern=r"/viewer/(?P<identifier>\d+)", allow_collections=True)
    fetcher = Fetcher({
        "/api?page=1": {"records": [{"links": [BASE + "/about", BASE + "/viewer/1"]}]},
        "/m/1": {"@context": CONTEXT, "@type": "sc:Collection", "@id": BASE + "/m/1",
                 "manifests": [{"@id": BASE + "/m/2", "@type": "sc:Manifest"}]},
        "/m/2": manifest(2),
    })
    execution = execute_skill(skill, fetcher, investigation_id="collection-test", max_manifests=10)
    assert not execution.manifests
    assert len(execution.entry_points) == 1
    assert execution.audit["collection_roots_validated"] == 1
    provider = ProviderInputRecord.from_mapping(provider_value(BASE + "/missing", json_type="Collection"))
    result = ResourceDiscoverer(fetcher, html_enabled=False, omeka_s_probe_enabled=False).discover(
        provider, knowledge_skills=[skill], investigation_id="collection-test")
    assert {m.manifest_url for m in result.manifests} == {BASE + "/m/2"}
    assert result.collections_visited == 1


def test_detail_object_extracts_identifier_from_a_declared_manifest_url():
    skill = identifier_skill()
    skill["identifier_followup"] = {
        "url_template": BASE + "/details/{identifier}",
        "records_path": "response.document", "identifier_path": "manifest",
        "identifier_pattern": r"/published/(?P<identifier>[^/]+)/manifest$",
    }
    fetcher = Fetcher({
        "/api?page=1": {"records": [{"id": "a"}, {"id": "b"}]},
        "/details/a": {"response": {"document": {"manifest": BASE + "/published/one/manifest"}}},
        "/details/b": {"response": {"document": {"manifest": BASE + "/not-a-manifest"}}},
        "/m/one": manifest("one"),
    })
    result = execute_skill(skill, fetcher, investigation_id="object-detail", max_manifests=10)
    assert [m.manifest_url for m in result.manifests] == [BASE + "/m/one"]
    assert result.audit["followup_requests"] == 2
    assert not any("not-a-manifest" in url for url in fetcher.calls)


def test_declared_link_pattern_skips_pdf_and_viewer_without_requesting_them():
    skill = {"skill_id": "filtered-links", "type": "paginated_json_manifest_links",
             "api_url": BASE + "/api", "records_path": "records", "manifest_url_path": "links.*",
             "manifest_url_pattern": r"/m/[^/]+$", "pagination": {"page_size": 10, "max_pages": 1}}
    fetcher = Fetcher({"/api?page=1": {"records": [{"links": [BASE + "/file.pdf", BASE + "/viewer/1", BASE + "/m/1"]}]},
                       "/m/1": manifest(1)})
    result = execute_skill(skill, fetcher, investigation_id="filtered-links", max_manifests=5)
    assert len(result.manifests) == 1
    assert result.audit["manifest_requests"] == 1
    assert not any("file.pdf" in url or "/viewer/" in url for url in fetcher.calls)


def test_explicit_html_refresh_is_followed_only_for_reviewed_targets():
    skill = {"skill_id": "moved-links", "type": "paginated_json_manifest_links",
             "api_url": BASE + "/api", "records_path": "records", "manifest_url_path": "url",
             "pagination": {"page_size": 10, "max_pages": 1},
             "html_migration": {"max_hops": 2, "url_pattern": r"^https://example\.org/current/"}}
    fetcher = Fetcher({
        "/api?page=1": {"records": [{"url": BASE + "/old/1"}, {"url": BASE + "/old/2"}]},
        "/old/1": '<meta http-equiv="refresh" content="15; url=/current/1">',
        "/old/2": '<meta http-equiv="refresh" content="0; url=https://unreviewed.test/m">',
        "/current/1": manifest(1),
    })
    result = execute_skill(skill, fetcher, investigation_id="migration", max_manifests=5)
    assert [m.manifest_url for m in result.manifests] == [BASE + "/current/1"]
    assert not any("unreviewed.test" in url for url in fetcher.calls)


def test_legacy_shared_canvas_requires_opt_in_and_the_exact_known_context():
    skill = identifier_skill()
    legacy = {**manifest(1), "@context": "http://www.shared-canvas.org/ns/context.json", "sequences": []}
    documents = {"/api?page=1": {"records": [{"id": "1"}]}, "/m/1": legacy}
    assert not execute_skill(skill, Fetcher(documents), investigation_id="legacy", max_manifests=5).manifests
    skill['allow_legacy_shared_canvas'] = True
    assert len(execute_skill(skill, Fetcher(documents), investigation_id="legacy", max_manifests=5).manifests) == 1
    legacy['@context'] = 'https://unknown.example/context.json'
    assert not execute_skill(skill, Fetcher(documents), investigation_id="legacy", max_manifests=5).manifests


def test_html_access_labels_and_next_page_override_short_page_heuristic():
    skill = {"skill_id": "targeted-html", "type": "paginated_html_identifiers_to_manifest_templates",
             "api_url": BASE + "/listing", "record_url_pattern": r"/record/(?P<identifier>\d+)",
             "required_ancestor_class": "public", "manifest_url_templates": [BASE + "/m/{identifier}"],
             "pagination": {"page_size": 100, "max_pages": 10, "detect_next_page": True}}
    fetcher = Fetcher({
        "/listing?page=1": '<li class="public"><a href="/record/1">one</a></li><li class="campus"><a href="/record/2">private</a></li><a href="/listing?page=2">next</a>',
        "/listing?page=2": '<li class="public"><a href="/record/3">three</a></li><a href="/listing?page=1">previous</a>',
        "/m/1": manifest(1), "/m/3": manifest(3),
    })
    result = execute_skill(skill, fetcher, investigation_id="html-test", max_manifests=10)
    assert {m.manifest_url for m in result.manifests} == {BASE + "/m/1", BASE + "/m/3"}
    assert result.audit["pages_fetched"] == 2
    assert not result.truncated
    assert not any("/m/2" in url for url in fetcher.calls)


def test_single_listing_does_not_add_fake_pagination_parameters():
    skill = {"skill_id": "single-list", "type": "paginated_html_identifiers_to_manifest_templates",
             "api_url": BASE + "/all", "record_url_pattern": r"/record/(?P<identifier>\d+)",
             "manifest_url_templates": [BASE + "/m/{identifier}"],
             "pagination": {"page_parameter": "", "page_size_parameter": "", "max_pages": 1}}
    fetcher = Fetcher({"/all": '<a href="/record/1">one</a>', "/m/1": manifest(1)})
    result = execute_skill(skill, fetcher, investigation_id="single-test", max_manifests=10)
    assert len(result.manifests) == 1
    assert fetcher.calls[0] == BASE + "/all"


def test_manifest_budget_stops_before_fetching_the_next_catalogue_page():
    skill = identifier_skill()
    skill["pagination"].update(page_size=1, max_pages=10000)
    fetcher = Fetcher({"/api?page=1": {"records": [{"id": "1"}]}, "/m/1": manifest(1)})
    result = execute_skill(skill, fetcher, investigation_id="stream-test", max_manifests=1)
    assert len(result.manifests) == 1
    assert result.audit["pages_fetched"] == 1
    assert result.truncated
    assert not any("page=2" in url for url in fetcher.calls)


def test_ignored_pagination_is_reported_instead_of_looping_to_the_page_cap():
    skill = identifier_skill()
    skill["pagination"].update(page_size=1, max_pages=10000)
    duplicate = {"records": [{"id": "1"}]}
    fetcher = Fetcher({"/api?page=1": duplicate, "/api?page=2": duplicate, "/m/1": manifest(1)})
    result = execute_skill(skill, fetcher, investigation_id="repeat-test", max_manifests=10)
    assert len(result.manifests) == 1
    assert result.audit["failure_counts"]["repeated_catalogue_page"] == 1
    assert result.truncated
    assert not any("page=3" in url for url in fetcher.calls)
