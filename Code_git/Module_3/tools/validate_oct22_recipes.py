"""Check fallback recipes, declared next pages and KU ownership independently.

These additional requests are not added to the end-to-end sample counts.
"""
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import time

module = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(module))
from iiif_resource_discovery.fetch import HttpFetcher
from iiif_resource_discovery.skills import execute_skill

root = module / "evaluation/2026-10-22_five_provider_completion"
evidence = root / "recipe_checks"
evidence.mkdir(exist_ok=True)


class EvidenceFetcher(HttpFetcher):
    """Keep every successful supplementary response without reusing old bodies."""
    def fetch(self, url, **options):
        time.sleep(0.6)
        doc = super().fetch(url, **options)
        path = evidence / (sha256(url.encode()).hexdigest()[:20] + ".body")
        path.write_bytes(doc.body)
        with (evidence / "requests.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"url": url, "final_url": doc.final_url,
                "status_code": doc.status_code, "body_file": str(path), "bytes": len(doc.body)}) + "\n")
        return doc


fetcher = EvidenceFetcher(timeout_seconds=35, retries=1, max_response_bytes=64 * 1024 * 1024)
entries = json.loads((root / "new_knowledge_entries.json").read_text(encoding="utf-8"))
results, pagination = [], []
for entry in entries:
    skill = entry["skills"][0]
    if entry["provider_name"] == "KU Leuven":
        first = fetcher.fetch(skill["api_url"] + "?page=1").text()
        second = fetcher.fetch(skill["api_url"] + "?page=2").text()
        ids = [set(re.findall(r"/items/show/(\d+)", page)) for page in [first, second]]
        assert all(ids) and ids[0] != ids[1]
        pagination.append({"provider": entry["provider_name"], "page_1_records": sorted(ids[0]),
            "page_2_records": sorted(ids[1]), "distinct_pages": True})
        continue
    result = execute_skill(skill, fetcher, investigation_id=entry["investigation_id"], max_manifests=2)
    assert len(result.manifests) == 2, (entry["provider_name"], result.audit, result.issues)
    results.append({"provider_id": entry["provider_id"], "provider_name": entry["provider_name"],
        "validated_manifest_urls": [v.manifest_url for v in result.manifests], "audit": result.audit,
        "added_to_downstream_count": False})
    collection = fetcher.fetch(skill["api_url"]).json()
    next_value = collection.get("next")
    next_url = next_value.get("@id", next_value.get("id")) if isinstance(next_value, dict) else next_value
    assert isinstance(next_url, str) and next_url.startswith("https://")
    next_page = fetcher.fetch(next_url).json()
    first_ids = {m.get("@id") for m in collection["members"]}
    next_ids = {m.get("@id") for m in next_page["members"]}
    assert next_ids and next_ids != first_ids
    pagination.append({"provider": entry["provider_name"], "first_page": skill["api_url"],
        "declared_next": next_url, "first_page_members": len(first_ids),
        "next_page_members": len(next_ids), "distinct_pages": True,
        "note": "Page traversal checked; these links were not all fetched as Manifests."})

ownership = []
for line in (root / "validation/module4/output/validated_manifests.jsonl").read_text(encoding="utf-8").splitlines():
    manifest = json.loads(line)
    if not any(p["provider_id"] == "provider-ef2f1cc06db37bc3" for p in manifest["providers"]):
        continue
    raw = json.loads((root / manifest["raw_manifest"]["raw_manifest_path"]).read_bytes())
    location = [m for m in raw.get("metadata", []) if "location" in str(m.get("label", {})).lower()]
    assert "KU Leuven Libraries" in json.dumps(location)
    ownership.append({"manifest_url": manifest["manifest_url"], "declared_location": location})
assert len(ownership) == 6
for name, value in [("fallback_recipe_validation.json", results), ("pagination_validation.json", pagination),
                    ("ku_leuven_ownership_validation.json", ownership)]:
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"fallback_recipes_passed": len(results), "distinct_pagination_checks": len(pagination),
                  "ku_leuven_owned_sample_records": len(ownership)}))
