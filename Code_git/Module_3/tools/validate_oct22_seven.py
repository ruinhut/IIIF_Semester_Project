"""Independently verify branch ownership, pagination and seven fallback recipes."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

module = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(module))
from iiif_resource_discovery.discovery import DiscoveryLimits, ResourceDiscoverer
from iiif_resource_discovery.fetch import HttpFetcher
from iiif_resource_discovery.models import ProviderInputRecord
from iiif_resource_discovery.skills import execute_skill

root = module / "evaluation/2026-10-22_seven_provider_completion"
evidence = root / "recipe_checks"
evidence.mkdir(exist_ok=True)


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class EvidenceFetcher(HttpFetcher):
    """Save each extra response and retain the exact requested route."""
    def __init__(self):
        super().__init__(timeout_seconds=35, retries=1, max_response_bytes=64 * 1024 * 1024)
        self.requests = []

    def fetch(self, url, **options):
        time.sleep(0.6)
        self.requests.append(url)
        document = super().fetch(url, **options)
        path = evidence / (sha256(url.encode()).hexdigest()[:20] + ".body")
        path.write_bytes(document.body)
        with (evidence / "requests.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"url": url, "final_url": document.final_url,
                "status_code": document.status_code, "body_file": str(path), "bytes": len(document.body)}) + "\n")
        return document


entries = json.loads((root / "new_knowledge_entries.json").read_text(encoding="utf-8"))
fetcher = EvidenceFetcher()
fallbacks, pagination, scoped_runs = [], [], []
checked = rows(root / "validation/module2/output/checked_entry_points.jsonl")
for entry in entries:
    skill = entry["skills"][0]
    result = execute_skill(skill, fetcher, investigation_id=entry["investigation_id"], max_manifests=2)
    assert len(result.manifests) == 2, (entry["provider_name"], result.audit, result.issues)
    fallbacks.append({"provider_name": entry["provider_name"], "validated_manifest_urls": [m.manifest_url for m in result.manifests],
        "audit": result.audit, "added_to_downstream_count": False})
    page = fetcher.fetch(skill["api_url"]).json()
    declared_next = page.get("next")
    if not declared_next:
        pagination.append({"provider_name": entry["provider_name"], "declared_next": None})
        continue
    if isinstance(declared_next, dict):
        declared_next = declared_next.get("@id", declared_next.get("id"))
    requested_next = declared_next
    for rule in skill.get("collection_url_rewrites", []):
        if requested_next.startswith(rule["from_prefix"]):
            requested_next = rule["to_prefix"] + requested_next[len(rule["from_prefix"]):]
    next_page = fetcher.fetch(requested_next).json()
    first_ids = {m.get("@id") for m in page["members"]}
    next_ids = {m.get("@id") for m in next_page["members"]}
    assert next_ids and first_ids != next_ids
    pagination.append({"provider_name": entry["provider_name"], "first_page": skill["api_url"],
        "declared_next": declared_next, "requested_next": requested_next,
        "first_page_members": len(first_ids), "next_page_members": len(next_ids), "distinct_pages": True,
        "scope_rewrite_applied": declared_next != requested_next})
    if skill.get("collection_url_rewrites"):
        scoped_fetcher = EvidenceFetcher()
        provider = ProviderInputRecord.from_mapping(next(v for v in checked if v["provider_id"] == entry["provider_id"]))
        discovered = ResourceDiscoverer(scoped_fetcher,
            limits=DiscoveryLimits(max_collections_per_provider=6, max_manifests_per_provider=24),
            html_enabled=False, omeka_s_probe_enabled=False).discover(provider, knowledge_skills=[skill])
        collection_requests = [url for url in scoped_fetcher.requests if "/collection/" in url]
        expected_prefix = skill["collection_url_rewrites"][0]["to_prefix"]
        unique_manifests = {m.manifest_url for m in discovered.manifests}
        assert len(unique_manifests) == 24
        assert len(collection_requests) >= 2
        assert all(url.startswith(expected_prefix) for url in collection_requests)
        scoped_runs.append({"provider_name": entry["provider_name"], "discovered_urls": len(unique_manifests),
            "collection_requests": collection_requests, "all_requests_keep_institution_scope": True,
            "root_next_reached_before_manifest_cap": requested_next in collection_requests,
            "scope_audit": [a for a in discovered.knowledge_application if a.get("status") == "collection_scope_preserved"],
            "added_to_downstream_count": False})

owners = {"Rheinland-Pfalz State Library Centre": ["Landesbibliothekszentrum"],
    "Trier University Library": ["Trier", "Universit"], "Trier City Library": ["Trier", "Stadtbibliothek"],
    "Mainz City Library": ["Mainz", "Stadtbibliothek"]}
ownership = []
by_provider = {}
for manifest in rows(root / "validation/module4/output/validated_manifests.jsonl"):
    name = manifest["providers"][0]["provider_name"]
    if name not in owners:
        continue
    raw = json.loads((root / manifest["raw_manifest"]["raw_manifest_path"]).read_bytes())
    edition = [m for m in raw.get("metadata", []) if m.get("label") == "Online-Ausgabe"]
    declared = json.dumps(edition, ensure_ascii=False)
    assert all(token in declared for token in owners[name]), (name, manifest["manifest_url"], edition)
    by_provider.setdefault(name, set()).add(manifest["manifest_url"])
    ownership.append({"provider_name": name, "manifest_url": manifest["manifest_url"],
        "declared_attribution": raw.get("attribution"), "online_edition_metadata": edition})
assert len(by_provider) == 4
assert len(set.union(*by_provider.values())) == sum(len(v) for v in by_provider.values())
save("fallback_recipe_validation.json", fallbacks)
save("pagination_validation.json", pagination)
save("collection_scope_verification.json", scoped_runs)
save("institution_ownership_verification.json", {"sample_manifest_ownership_checks": ownership,
    "independent_holders": 4, "manifest_urls_overlap_between_holders": False})
print(json.dumps({"fallbacks_passed": len(fallbacks), "pagination_checks": len(pagination),
    "scoped_24_url_runs": len(scoped_runs), "verified_holder_metadata_records": len(ownership)}))
