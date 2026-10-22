"""Check catalogue-to-detail discovery without executing page scripts."""

from test_five_provider_skills import BASE, Fetcher, identifier_skill, manifest
from iiif_resource_discovery.skills import execute_skill


def recipe():
    value = identifier_skill()
    value["identifier_followup"] = {
        "url_template": BASE + "/detail/{identifier}", "format": "html",
        "identifier_pattern": r"/native/(?P<identifier>\d+)$",
        "include_visible_url_text": True,
    }
    return value


def test_detail_accepts_visible_url_and_anchor_but_ignores_scripts():
    fetcher = Fetcher({
        "/api?page=1": {"records": [{"id": "parent"}]},
        "/detail/parent": '<script>"https://example.test/native/99"</script>'
                          '<style>.x{url:https://example.test/native/98}</style>'
                          '<p>https://example.test/native/1</p>'
                          '<a href="/native/2">IIIF</a><p>https://example.test/native/1</p>',
        "/m/1": manifest(1), "/m/2": manifest(2),
    })
    result = execute_skill(recipe(), fetcher, investigation_id="html-detail", max_manifests=10)
    assert [m.manifest_url for m in result.manifests] == [BASE + "/m/1", BASE + "/m/2"]
    assert result.audit["followup_requests"] == 1
    assert fetcher.calls.count(BASE + "/m/1") == 1
    assert BASE + "/m/99" not in fetcher.calls


def test_detail_url_still_requires_a_valid_manifest_response():
    fetcher = Fetcher({
        "/api?page=1": {"records": [{"id": "parent"}]},
        "/detail/parent": '<p>https://example.test/native/1</p>',
        "/m/1": {"type": "CatalogueRecord", "id": BASE + "/m/1"},
    })
    result = execute_skill(recipe(), fetcher, investigation_id="not-manifest", max_manifests=10)
    assert not result.manifests
    assert result.audit["failure_counts"]["not_iiif_manifest"] == 1
