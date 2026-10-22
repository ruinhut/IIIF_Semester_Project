"""Verify namespace-aware catalogue parsing and safe OAI continuation."""
import json
from urllib.parse import parse_qs, urlsplit

from iiif_resource_discovery.fetch import FetchedDocument
from iiif_resource_discovery.skills import execute_skill

BASE = "https://example.org"


class Fetcher:
    sleeper = staticmethod(lambda _: None)

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def fetch(self, url, **kwargs):
        self.calls.append(url)
        parts = urlsplit(url)
        if parts.path == "/oai":
            q = parse_qs(parts.query)
            assert "__xml_page" not in q
            if "resumptionToken" in q:
                assert set(q) == {"verb", "resumptionToken"}
            value = self.pages[1 if "resumptionToken" in q else 0]
            return FetchedDocument(url, url, 200, "application/xml", value.encode())
        value = {"@context": "http://iiif.io/api/presentation/2/context.json",
                 "@id": url, "@type": "sc:Manifest"}
        return FetchedDocument(url, url, 200, "application/json", json.dumps(value).encode())


def recipe():
    return {"skill_id": "xml-test", "type": "paginated_xml_identifiers_to_manifest_templates",
            "api_url": BASE + "/oai", "query_parameters": {"verb": "ListRecords", "metadataPrefix": "oai_dc"},
            "xml_namespaces": {"o": "http://www.openarchives.org/OAI/2.0/", "d": "urn:dc"},
            "xml_record_path": ".//o:record", "xml_identifier_path": ".//d:link",
            "identifier_pattern": r"/m/(?P<identifier>\d+)$",
            "manifest_url_templates": [BASE + "/m/{identifier}"],
            "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 50,
                           "max_pages": 5, "next_token_path": ".//o:resumptionToken"}}


def page(body, token=""):
    return '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:d="urn:dc"><ListRecords>' + body + '<resumptionToken>' + token + '</resumptionToken></ListRecords></OAI-PMH>'


def test_oai_token_preserved_and_duplicate_or_deleted_links_skipped():
    first = '<record><header/><metadata><d:link>https://example.org/m/1</d:link><d:link>https://example.org/m/1</d:link></metadata></record><record><header status="deleted"/><metadata><d:link>https://example.org/m/99</d:link></metadata></record>'
    second = '<record><header/><metadata><d:link>https://example.org/m/2</d:link></metadata></record>'
    fetcher = Fetcher([page(first, "opaque:50!next"), page(second)])
    result = execute_skill(recipe(), fetcher, investigation_id="test", max_manifests=10)
    assert [m.manifest_url for m in result.manifests] == [BASE + "/m/1", BASE + "/m/2"]
    assert len(result.audit["enumeration_pages"]) == 2
    assert not result.issues
    assert fetcher.calls.count(BASE + "/m/1") == 1


def test_oai_error_or_html_is_not_an_empty_success():
    for value in ['<html><body>Access restricted</body></html>', '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><error code="badArgument"/></OAI-PMH>']:
        result = execute_skill(recipe(), Fetcher([value]), investigation_id="test", max_manifests=10)
        assert not result.manifests
        assert result.truncated
        assert result.audit["failure_counts"]["knowledge_api_shape"] == 1


def test_attribute_urls_are_extracted_and_invalid_manifest_is_rejected():
    skill = recipe()
    skill.update(xml_record_path=".//item", xml_identifier_path="link", xml_identifier_attribute="href")
    skill["pagination"].pop("next_token_path")
    fetcher = Fetcher(['<rss><item><link href="https://example.org/m/3"/></item></rss>'])
    original = fetcher.fetch

    def fetch(url, **kwargs):
        if urlsplit(url).path.startswith("/m/"):
            return FetchedDocument(url, url, 200, "application/json", b'{"type":"CatalogueRecord"}')
        return original(url, **kwargs)

    fetcher.fetch = fetch
    result = execute_skill(skill, fetcher, investigation_id="test", max_manifests=10)
    assert not result.manifests
    assert result.audit["failure_counts"]["not_iiif_manifest"] == 1
