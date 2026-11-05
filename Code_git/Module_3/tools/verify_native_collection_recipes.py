"""Audit native Collection recipes independently of an end-to-end sample.

Use --evaluation-root and an optional JSON ownership profile. Additional URLs
found here are evidence of traversal, not additional M4-validated objects.
"""
import argparse
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
from iiif_resource_discovery.skills import execute_skill, _path_value


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--ownership-profile", type=Path)
    parser.add_argument("--scope-budget", type=int, default=24)
    args = parser.parse_args()
    root = args.evaluation_root.resolve()
    evidence = root / "recipe_checks"
    evidence.mkdir(exist_ok=True)

    def save(name, value):
        (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    class EvidenceFetcher(HttpFetcher):
        def __init__(self):
            super().__init__(timeout_seconds=35, retries=1, max_response_bytes=64 * 1024 * 1024)
            self.requests = []

        def fetch(self, url, **options):
            time.sleep(0.6)
            self.requests.append(url)
            document = super().fetch(url, **options)
            path = evidence / (sha256(url.encode()).hexdigest()[:20] + ".body")
            path.write_bytes(document.body)
            with (evidence / "requests.jsonl").open("a", encoding="utf-8") as output:
                output.write(json.dumps({"url": url, "final_url": document.final_url,
                    "status_code": document.status_code, "body_file": str(path), "bytes": len(document.body)}) + "\n")
            return document

    entries = json.loads((root / "new_knowledge_entries.json").read_text(encoding="utf-8"))
    checked = rows(root / "validation/module2/output/checked_entry_points.jsonl")
    fetcher = EvidenceFetcher()
    fallbacks, pagination, scoped = [], [], []
    for entry in entries:
        skill = entry["skills"][0]
        result = execute_skill(skill, fetcher, investigation_id=entry["investigation_id"], max_manifests=2)
        assert len(result.manifests) == 2, (entry["provider_name"], result.audit, result.issues)
        fallbacks.append({"provider_name": entry["provider_name"], "audit": result.audit,
            "validated_manifest_urls": [m.manifest_url for m in result.manifests], "added_to_downstream_count": False})
        page = fetcher.fetch(skill["api_url"]).json()
        first = _path_value(page, skill["records_path"])
        assert isinstance(first, list)
        declared = page.get("next")
        if isinstance(declared, dict):
            declared = declared.get("@id", declared.get("id"))
        page_check = {"provider_name": entry["provider_name"], "first_page": skill["api_url"],
            "first_page_members": len(first), "declared_next": declared}
        if declared:
            requested = declared
            for rule in skill.get("collection_url_rewrites", []):
                if requested.startswith(rule["from_prefix"]):
                    requested = rule["to_prefix"] + requested[len(rule["from_prefix"]):]
            second = _path_value(fetcher.fetch(requested).json(), skill["records_path"])
            assert isinstance(second, list) and second
            first_ids = {m.get("@id", m.get("id")) for m in first}
            second_ids = {m.get("@id", m.get("id")) for m in second}
            assert first_ids != second_ids
            page_check.update(requested_next=requested, next_page_members=len(second), distinct_pages=True)
        else:
            page_check["note"] = "No next link declared; member count is not a count of downloaded objects."
        pagination.append(page_check)
        if skill.get("collection_url_rewrites"):
            scoped_fetcher = EvidenceFetcher()
            provider = ProviderInputRecord.from_mapping(next(v for v in checked if v["provider_id"] == entry["provider_id"]))
            discovery = ResourceDiscoverer(scoped_fetcher,
                limits=DiscoveryLimits(max_collections_per_provider=15, max_manifests_per_provider=args.scope_budget),
                html_enabled=False, omeka_s_probe_enabled=False).discover(provider, knowledge_skills=[skill])
            collection_requests = [u for u in scoped_fetcher.requests if "/collection/" in u]
            prefix = skill["collection_url_rewrites"][0]["to_prefix"]
            unique = {m.manifest_url for m in discovery.manifests}
            assert unique and all(url.startswith(prefix) for url in collection_requests)
            scoped.append({"provider_name": entry["provider_name"], "manifest_budget": args.scope_budget,
                "unique_discovered_urls": len(unique), "collection_requests": collection_requests,
                "all_requests_keep_institution_scope": True, "added_to_downstream_count": False,
                "audit": [a for a in discovery.knowledge_application if a.get("status") == "collection_scope_preserved"]})
    save("fallback_recipe_validation.json", fallbacks)
    save("pagination_validation.json", pagination)
    save("collection_scope_verification.json", scoped)
    ownership = []
    if args.ownership_profile:
        profile = json.loads(args.ownership_profile.read_text(encoding="utf-8"))
        urls = set()
        for manifest in rows(root / "validation/module4/output/validated_manifests.jsonl"):
            name = manifest["providers"][0]["provider_name"]
            rule = profile[name]
            raw = json.loads((root / manifest["raw_manifest"]["raw_manifest_path"]).read_bytes())
            values = ([m for m in raw.get("metadata", []) if m.get("label") == "Online-Ausgabe"]
                      if rule["field"] == "online_edition" else raw.get(rule["field"]))
            declared = json.dumps(values, ensure_ascii=False)
            assert all(token in declared for token in rule["required_tokens"]), (name, manifest["manifest_url"], values)
            assert manifest["manifest_url"] not in urls
            urls.add(manifest["manifest_url"])
            ownership.append({"provider_name": name, "manifest_url": manifest["manifest_url"],
                "checked_field": rule["field"], "declared_values": values,
                "institution_relation": rule.get("institution_relation", "source_declared_institution")})
        save("institution_ownership_verification.json", {"records_checked": len(ownership),
            "manifest_urls_overlap_between_sources": False, "records": ownership})
    print(json.dumps({"fallbacks_passed": len(fallbacks), "next_page_pairs": sum(bool(p["declared_next"]) for p in pagination),
        "scoped_provider_runs": len(scoped), "provenance_records_checked": len(ownership)}))


if __name__ == "__main__":
    main()
