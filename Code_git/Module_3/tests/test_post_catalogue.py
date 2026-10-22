"""Exercise JSON search pagination over real local HTTP, not live institutions."""

from copy import deepcopy

from http_test_server import LocalHttpServer
from iiif_resource_discovery.fetch import HttpFetcher
from iiif_resource_discovery.skills import catalogue_request, execute_skill
from iiif_resource_discovery.discovery import ResourceDiscoverer
from iiif_resource_discovery.models import ProviderInputRecord
from helpers import provider_value


def recipe(base):
    """Return a reviewed public search contract with header and body scope."""
    return {
        "skill_id": "public-json-search", "type": "paginated_json_identifiers_to_manifest_templates",
        "api_url": base + "/catalogue-search", "records_path": "hits", "identifier_path": "id",
        "request": {"method": "POST", "read_only": True,
                    "headers": {"X-Catalogue-Site": "public"}, "json_body": {"query": "", "filters": []}},
        "pagination": {"location": "json_body", "page_parameter": "offset", "page_size_parameter": "",
                       "page_size": 1, "page_step": 1, "start_page": 0, "max_pages": 5},
        "max_identifiers": 10, "manifest_url_templates": [base + "/templated/{identifier}/manifest"],
    }


def test_post_catalogue_pages_and_plain_get_manifests():
    """Headers/body must reach search only; two offsets and terminal empty page work."""
    with LocalHttpServer() as server:
        skill = recipe(server.base_url)
        original = deepcopy(skill)
        result = execute_skill(skill, HttpFetcher(retries=0, sleeper=lambda _: None),
                               investigation_id="post-test", max_manifests=10)
        counts = dict(server.server.RequestHandlerClass.request_counts)
    assert len(result.manifests) == 2
    assert result.audit["pages_fetched"] == 3
    assert result.audit["catalogue_method"] == "POST"
    assert counts["POST:0"] == counts["POST:1"] == counts["POST:2"] == 1
    assert counts["/templated/11/manifest"] == counts["/templated/13/manifest"] == 1
    assert skill == original


def test_post_recipe_requires_explicit_read_only_intent():
    """Unreviewed POST requests must fail locally before making HTTP requests."""
    skill = recipe("https://example.org")
    del skill["request"]["read_only"]
    result = execute_skill(skill, HttpFetcher(retries=0), investigation_id="invalid", max_manifests=1)
    assert result.issues[0].issue_type == "invalid_knowledge_skill"
    assert "read_only" in result.issues[0].message


def test_body_pagination_preserves_query_and_does_not_mutate_recipe():
    skill = recipe("https://example.org")
    skill["query_parameters"] = {"size": "1"}
    first, one = catalogue_request(skill, 0, 1)
    second, two = catalogue_request(skill, 1, 1)
    assert first == second == "https://example.org/catalogue-search?size=1"
    assert one["json_body"]["offset"] == 0 and two["json_body"]["offset"] == 1
    two["json_body"]["filters"].append("changed")
    assert not one["json_body"]["filters"] and not skill["request"]["json_body"]["filters"]


def test_json_body_pagination_cannot_be_sent_as_get():
    skill = recipe("https://example.org")
    skill["request"]["method"] = "GET"
    result = execute_skill(skill, HttpFetcher(retries=0), investigation_id="invalid", max_manifests=1)
    assert result.issues[0].issue_type == "invalid_knowledge_skill"
    assert "requires a POST" in result.issues[0].message


def test_server_page_size_clamping_is_not_reported_as_complete():
    with LocalHttpServer() as server:
        skill = recipe(server.base_url)
        skill["pagination"].update(page_size=2, page_step=2, total_path="total")
        result = execute_skill(skill, HttpFetcher(retries=0, sleeper=lambda _: None),
                               investigation_id="clamped-size", max_manifests=10)
    assert len(result.manifests) == 1
    assert result.truncated
    assert result.audit["source_declared_total"] == 2
    assert result.audit["failure_counts"]["premature_short_catalogue_page"] == 1


def test_overlapping_recipes_keep_distinct_evidence_without_duplicate_findings():
    with LocalHttpServer() as server:
        provider = ProviderInputRecord.from_mapping(provider_value(
            server.base_url + "/plain", check_result="reachable_non_json", json_type=None))
        first = recipe(server.base_url)
        second = deepcopy(first)
        second["skill_id"] = "alternative-search"
        result = ResourceDiscoverer(HttpFetcher(retries=0), html_enabled=False,
                                   omeka_s_probe_enabled=False).discover(
            provider, knowledge_skills=[first, deepcopy(first), second], investigation_id="overlap-test")
    assert result.to_dict()["resource_discovery"]["manifest_count"] == 2
    assert len(result.manifests) == 4
    assert {finding.evidence.discovery_method for finding in result.manifests} == {
        "knowledge_skill:public-json-search", "knowledge_skill:alternative-search"}
