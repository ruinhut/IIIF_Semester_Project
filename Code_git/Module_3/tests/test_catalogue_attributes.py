"""Verify opt-in catalogue attributes and cross-institution JSON followups."""

from test_five_provider_skills import BASE, Fetcher, manifest
from iiif_resource_discovery.skills import execute_skill


def skill():
    return {"skill_id": "declared-attributes", "type": "paginated_html_identifiers_to_manifest_templates",
            "api_url": BASE + "/listing", "record_url_pattern": r"/m/(?P<identifier>\d+)$",
            "manifest_url_templates": [BASE + "/m/{identifier}"],
            "pagination": {"page_size": 1, "max_pages": 3, "detect_next_page": True}}


def test_container_manifest_attributes_enumerate_distinct_paginated_records():
    recipe = skill()
    recipe["record_url_attributes"] = ["href", "data-manifest"]
    fetcher = Fetcher({
        "/listing?page=1": '<div data-manifest="/m/1"><a href="/m/1">same object</a></div><a href="?page=2">Next</a>',
        "/listing?page=2": '<article data-manifest="/m/2"></article><span data-manifest="/m/not-matching"></span>',
        "/m/1": manifest(1), "/m/2": manifest(2),
    })
    result = execute_skill(recipe, fetcher, investigation_id="attribute-transfer", max_manifests=10)
    assert [r.manifest_url for r in result.manifests] == [BASE + "/m/1", BASE + "/m/2"]
    assert result.audit["pages_fetched"] == 2
    assert sum(url.endswith("/m/1") for url in fetcher.calls) == 1
    assert not any("not-matching" in url for url in fetcher.calls)


def test_attributes_are_not_used_without_explicit_recipe_opt_in():
    fetcher = Fetcher({"/listing?page=1": '<div data-manifest="/m/1"></div>'})
    result = execute_skill(skill(), fetcher, investigation_id="default-contract", max_manifests=10)
    assert not result.manifests
    assert not any(url.endswith("/m/1") for url in fetcher.calls)


def test_json_followup_selects_only_reviewed_institution_manifest_namespace():
    recipe = {"skill_id": "linked-art-followup", "type": "paginated_json_identifiers_to_manifest_templates",
              "api_url": BASE + "/api", "records_path": "orderedItems", "identifier_path": "id",
              "identifier_pattern": r"/object/(?P<identifier>[a-z]+)$",
              "identifier_followup": {"url_template": BASE + "/details/{identifier}",
                  "identifier_path": "subject_of.*.digitally_carried_by.*.access_point.*.id",
                  "identifier_pattern": r"/museum-a/(?P<identifier>\d+)$"},
              "manifest_url_templates": [BASE + "/m/{identifier}"],
              "pagination": {"page_size": 3, "max_pages": 1}}
    detail = {"subject_of": [{"digitally_carried_by": [{"access_point": [
        {"id": BASE + "/catalogue/12"}, {"id": BASE + "/museum-b/99"},
        {"id": BASE + "/museum-a/12"}]}]}]}
    fetcher = Fetcher({"/api?page=1": {"orderedItems": [{"id": BASE + "/object/alpha"}]},
                       "/details/alpha": detail, "/m/12": manifest(12)})
    result = execute_skill(recipe, fetcher, investigation_id="institution-namespace", max_manifests=3)
    assert [r.manifest_url for r in result.manifests] == [BASE + "/m/12"]
    assert not any("museum-b" in url or "/catalogue/" in url for url in fetcher.calls)


def test_array_index_filters_and_declared_totals_match_identifier_paths():
    recipe = {"skill_id": "array-metadata", "type": "paginated_json_identifiers_to_manifest_templates",
              "api_url": BASE + "/api", "records_path": "records", "identifier_path": "ids.0",
              "required_nonempty_paths": ["images.0"],
              "filters": [{"path": "published.0", "equals": "Yes"}],
              "manifest_url_templates": [BASE + "/m/{identifier}"],
              "pagination": {"page_size": 10, "max_pages": 1, "total_path": "partOf.0.totalItems"}}
    fetcher = Fetcher({"/api?page=1": {"partOf": [{"totalItems": 3}], "records": [
        {"ids": [1], "images": [], "published": ["Yes"]},
        {"ids": [2], "images": ["page.jpg"], "published": ["Yes"]},
        {"ids": [3], "images": ["hidden.jpg"], "published": ["No"]}]},
        "/m/2": manifest(2)})
    result = execute_skill(recipe, fetcher, investigation_id="indexed-metadata", max_manifests=10)
    assert [r.manifest_url for r in result.manifests] == [BASE + "/m/2"]
    assert result.audit["source_declared_total"] == 3
    assert len(fetcher.calls) == 2
