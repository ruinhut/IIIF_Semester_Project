"""Protect institution boundaries when reviewed Collection links lose scope."""
import json
import unittest

from iiif_resource_discovery.discovery import ResourceDiscoverer
from iiif_resource_discovery.fetch import FetchedDocument
from iiif_resource_discovery.models import ProviderInputRecord
from helpers import provider_value


class MemoryFetcher:
    sleeper = staticmethod(lambda _: None)

    def __init__(self):
        self.requests = []

    def fetch(self, url, **options):
        self.requests.append(url)
        name = "foreign" if url == "https://catalog.example/i3f/v21/collection/all_o20" else "local"
        first = url.endswith("/all")
        body = {"@context": "http://iiif.io/api/presentation/2/context.json",
            "@type": "sc:Collection", "@id": url,
            "members": [{"@type": "sc:Manifest", "@id": f"https://catalog.example/manifest/{'one' if first else name}"}]}
        if first:
            body["next"] = "https://catalog.example/i3f/v21/collection/all_o20"
        return FetchedDocument(url, url, 200, "application/json", json.dumps(body).encode())


class CollectionScopeTests(unittest.TestCase):
    def run_case(self, target=None, rules=None):
        fetcher = MemoryFetcher()
        provider = ProviderInputRecord.from_mapping(provider_value(
            "https://catalog.example/branch/i3f/v21/collection/all", json_type="Collection"))
        skills = [] if target is None and rules is None else [{"skill_id": "reviewed-branch",
            "collection_url_rewrites": rules if rules is not None else [{
                "from_prefix": "https://catalog.example/i3f/v21/collection/", "to_prefix": target}]}]
        result = ResourceDiscoverer(fetcher, html_enabled=False, omeka_s_probe_enabled=False).discover(
            provider, knowledge_skills=skills)
        return result, fetcher

    def test_scoped_next_retains_institution_and_manifest_urls(self):
        result, fetcher = self.run_case("https://catalog.example/branch/i3f/v21/collection/")
        self.assertIn("https://catalog.example/branch/i3f/v21/collection/all_o20", fetcher.requests)
        self.assertNotIn("https://catalog.example/i3f/v21/collection/all_o20", fetcher.requests)
        self.assertEqual({m.manifest_url for m in result.manifests}, {
            "https://catalog.example/manifest/one", "https://catalog.example/manifest/local"})
        audit = next(a for a in result.knowledge_application if a.get("status") == "collection_scope_preserved")
        self.assertEqual(audit["declared_url"], "https://catalog.example/i3f/v21/collection/all_o20")

    def test_without_reviewed_rule_follows_declared_url(self):
        result, fetcher = self.run_case()
        self.assertIn("https://catalog.example/i3f/v21/collection/all_o20", fetcher.requests)
        self.assertIn("https://catalog.example/manifest/foreign", {m.manifest_url for m in result.manifests})

    def test_cross_origin_scope_rule_is_rejected(self):
        result, fetcher = self.run_case("https://other.example/branch/i3f/v21/collection/")
        self.assertTrue(any(i.issue_type == "invalid_collection_scope_rule" for i in result.issues))
        self.assertFalse(any("other.example" in url for url in fetcher.requests))

    def test_overbroad_non_collection_prefix_is_rejected(self):
        result, _ = self.run_case(rules=[{"from_prefix": "https://catalog.example/", "to_prefix": "https://catalog.example/branch/"}])
        self.assertTrue(any(i.issue_type == "invalid_collection_scope_rule" for i in result.issues))

    def test_malformed_rule_does_not_abort_provider(self):
        result, _ = self.run_case(rules=[{"from_prefix": None, "to_prefix": 42}])
        self.assertTrue(any(i.issue_type == "invalid_collection_scope_rule" for i in result.issues))
        self.assertEqual(len(result.manifests), 2)

    def test_invalid_rule_container_does_not_abort_provider(self):
        result, _ = self.run_case(rules="not-an-array")
        self.assertTrue(any(i.issue_type == "invalid_collection_scope_rule" for i in result.issues))
        self.assertEqual(len(result.manifests), 2)


if __name__ == "__main__":
    unittest.main()
