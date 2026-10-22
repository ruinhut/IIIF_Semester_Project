"""Check keyed catalogues, literal query templates and incomplete traversal."""

from urllib.parse import parse_qs, urlsplit

from test_five_provider_skills import BASE, Fetcher, identifier_skill, manifest
from iiif_resource_discovery.skills import catalogue_request, execute_skill
from helpers import provider_value
from iiif_resource_discovery.discovery import ResourceDiscoverer
from iiif_resource_discovery.models import ProviderInputRecord


def test_keyed_catalogue_opt_in_preserves_record_ids_and_deduplication():
    recipe = identifier_skill()
    recipe.update(records_path="result", records_format="mapping_values")
    fetcher = Fetcher({"/api?page=1": {"result": {
        "shelfmark-a": {"id": "1"}, "alias-a": {"id": "1"},
        "shelfmark-b": {"id": "2"}}}, "/m/1": manifest(1), "/m/2": manifest(2)})
    result = execute_skill(recipe, fetcher, investigation_id="keyed-records", max_manifests=10)
    assert [m.manifest_url for m in result.manifests] == [BASE + "/m/1", BASE + "/m/2"]
    assert result.audit["records_examined"] == 3
    assert fetcher.calls.count(BASE + "/m/1") == 1


def test_mapping_is_not_silently_accepted_without_opt_in():
    recipe = identifier_skill()
    fetcher = Fetcher({"/api?page=1": {"records": {"a": {"id": "1"}}}})
    result = execute_skill(recipe, fetcher, investigation_id="shape-contract", max_manifests=10)
    assert not result.manifests
    assert result.truncated
    assert result.audit["failure_counts"]["knowledge_api_shape"] == 1


def test_sparql_pagination_template_changes_offset_without_formatting_braces():
    recipe = identifier_skill()
    query = "SELECT ?s WHERE { ?s a <https://example.org/Object> } ORDER BY ?s LIMIT {page_size} OFFSET {page_number}"
    recipe.update(query_parameters={"format": "json"}, query_parameter_templates={"query": query},
                  pagination={"page_parameter": "", "page_size_parameter": ""})
    first, _ = catalogue_request(recipe, 0, 3)
    second, _ = catalogue_request(recipe, 3, 3)
    assert parse_qs(urlsplit(first).query)["query"] == [query.replace("{page_size}", "3").replace("{page_number}", "0")]
    assert parse_qs(urlsplit(second).query)["query"][0].endswith("LIMIT 3 OFFSET 3")
    assert "{page_number}" in recipe["query_parameter_templates"]["query"]


def test_catalogue_failure_marks_partial_output_incomplete():
    recipe = identifier_skill()
    recipe["pagination"] = {"page_size": 1, "max_pages": 3}
    fetcher = Fetcher({"/api?page=1": {"records": [{"id": "1"}]}, "/m/1": manifest(1)})
    result = execute_skill(recipe, fetcher, investigation_id="failed-next-page", max_manifests=10)
    assert len(result.manifests) == 1
    assert result.truncated
    assert result.audit["failure_counts"]["http_500"] == 1


def test_range_pagination_computes_exclusive_end_without_evaluating_code():
    recipe = identifier_skill()
    recipe.update(query_parameter_templates={"start": "{page_number}", "end": "{page_end}"},
                  pagination={"page_parameter": "", "page_size_parameter": ""})
    first, _ = catalogue_request(recipe, 0, 20)
    second, _ = catalogue_request(recipe, 20, 20)
    assert parse_qs(urlsplit(first).query) == {"start": ["0"], "end": ["20"]}
    assert parse_qs(urlsplit(second).query) == {"start": ["20"], "end": ["40"]}


def test_disabled_html_is_not_reported_as_network_unreachable():
    provider = ProviderInputRecord.from_mapping(provider_value(BASE + "/home", check_result="reachable_non_json"))
    result = ResourceDiscoverer(Fetcher({}), html_enabled=False, omeka_s_probe_enabled=False).discover(provider)
    issue = next(i for i in result.issues if i.issue_type == "module_2_reachable_non_json")
    assert "is reachable" in issue.message and "disabled" in issue.message
    assert "was not reachable" not in issue.message
