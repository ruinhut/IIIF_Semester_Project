"""Install reviewed public search recipes and prepare isolated Blavatnik runs."""

import argparse
import json
from pathlib import Path


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--batch", default="validation")
    args = parser.parse_args()
    module = Path(__file__).resolve().parents[1]
    root = module / "evaluation/2026-10-16_blavatnik_investigation"
    provider = json.loads((root / "provider.json").read_text(encoding="utf-8"))
    alternatives = json.loads((root / "catalogue_recipes.json").read_text(encoding="utf-8"))
    # Start with a collection where original-language transcription was observed.
    alternatives.sort(key=lambda r: r["skill_id"] != "public-post-search-collection-48")
    for recipe in alternatives:
        recipe["api_url"] = "https://www.blavatnikarchive.org/api/data/es/search?size=25"
        recipe["pagination"].update(page_size=25, page_step=25, max_pages=400)
    save(root / "catalogue_recipes.json", alternatives)
    complete = root / "entire_catalogue_snapshot_v2/summary.json"
    if complete.exists() and json.loads(complete.read_text())["finished_collections"] == 1:
        recipes = json.loads((root / "entire_catalogue_recipe.json").read_text(encoding="utf-8"))
    else:
        recipes = alternatives
    knowledge_path = module / "config/discovery_knowledge.json"
    knowledge = json.loads(knowledge_path.read_text(encoding="utf-8"))
    knowledge["providers"] = [p for p in knowledge["providers"] if p["provider_id"] != provider["provider_id"]]
    knowledge["providers"].append({"provider_id": provider["provider_id"], "provider_name": provider["name"],
        "investigation_id": "2026-10-16-blavatnik", "investigation_document": "knowledge/institutions/2026-10-16_blavatnik.md",
        "skills": recipes, "alternative_skills": alternatives,
        "alternative_skills_note": "Collection-specific queries retained for targeted runs; the verified whole-catalogue query avoids facet omissions."})
    save(knowledge_path, knowledge)
    checked_path = module.parent / "Module_2/data/output/checked_entry_points.jsonl"
    if not checked_path.exists():
        # Replay the preserved Module 2 input, never invent a fresh check result.
        checked_path = root / "checked_selected.jsonl"
    checked = [json.loads(line) for line in checked_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    selected = [p for p in checked if p["provider_id"] == provider["provider_id"]]
    assert selected
    (root / "checked_selected.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in selected), encoding="utf-8")
    network = {"timeout_seconds": 25, "retries": 1, "max_response_bytes": 32 * 1024 * 1024}
    batch = root / args.batch
    save(root / f"module3_{args.batch}.json", {
        "input_jsonl": str(root / "checked_selected.jsonl"), "curated_endpoints": str(module / "config/provider_endpoints.json"),
        "knowledge_base": str(knowledge_path), "output_directory": str(batch / "module3/output"),
        "log_directory": str(batch / "module3/log"), "network": network,
        "limits": {"max_manifests_per_provider": args.limit, "max_collections_per_provider": 50,
                   "max_html_pages_per_provider": 1, "max_html_depth": 1, "max_machine_candidates_per_provider": 10},
        "html_discovery": {"enabled": False}, "platform_discovery": {"omeka_s_probe_enabled": False}})
    save(root / f"module4_{args.batch}.json", {
        "input_jsonl": str(batch / "module3/output/manifest_urls.jsonl"),
        "raw_manifest_directory": str(batch / "module4/raw_manifests"),
        "output_directory": str(batch / "module4/output"), "log_directory": str(batch / "module4/log"),
        "normalization": {"infer_missing_manifest_id": True}, "network": network,
        "run": {"force_refresh": False, "delay_between_requests_seconds": 0.2}})
    print(f"Prepared {len(recipes)} primary queries and retained {len(alternatives)} collection alternatives; {args.limit} Manifest budget in {args.batch}.")


if __name__ == "__main__":
    main()
