"""Prepare isolated, reproducible discovery for BSB, Rumsey and Vatican."""

import argparse
import json
from pathlib import Path
import re


def save(path, value):
    """Write readable UTF-8 configuration or evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    """Append verified catalogue routes without changing previous recipes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-limit", type=int, default=20)
    args = parser.parse_args()
    module = Path(__file__).resolve().parents[1]
    root = module / "evaluation/2026-10-15_three_provider_completion"
    baseline = json.loads((module / "evaluation/2026-10-15_provider_investigation/baseline_unresolved.json").read_text(encoding="utf-8-sig"))
    names = ["Digital Collections iiif of the Bavarian State Library", "David Rumsey Map Collection", "Vatican Library"]
    providers = [next(p for p in baseline if p["name"] == name) for name in names]
    save(root / "providers.json", providers)
    checks = [json.loads(line) for line in (root / "live/checks.jsonl").read_text(encoding="utf-8").splitlines()]
    catalogue = next(p for p in checks if p["url"] == "https://digi.vatlib.it/mss/" and p.get("status") == 200)
    html = Path(catalogue["response_file"]).read_text(encoding="utf-8")
    categories = list(dict.fromkeys(re.findall(r'data-item-url="(/mss/ajax/category/[^"<>]+)"', html)))
    if "/mss/ajax/category/Capp.Giulia" not in categories:
        raise RuntimeError("Previously checked collection missing from current catalogue evidence")
    # Start with the live-verified collection; retain all other declared collections.
    categories.sort(key=lambda value: value != "/mss/ajax/category/Capp.Giulia")
    save(root / "vatican_declared_categories.json", {"source_url": catalogue["url"], "categories": categories})
    recipes = {
        names[1]: [{
            "skill_id": "luna-paginated-explicit-manifest-links",
            "type": "paginated_json_manifest_links",
            "api_url": "https://www.davidrumsey.com/luna/servlet/as/search",
            "query_parameters": {"q": ""}, "records_path": "results", "manifest_url_path": "iiifManifest",
            "pagination": {"page_parameter": "os", "page_size_parameter": "bs", "page_size": 10,
                           "start_page": 0, "page_step": 10, "max_pages": 100000},
            "request_delay_seconds": 0.2,
            "coverage_note": "Live anonymous LUNA search; query total is catalogue records, not a verified count of downloadable images.",
        }],
        names[2]: [{
            "skill_id": "amlad-manuscript-category-" + category.rsplit("/", 1)[-1],
            "type": "paginated_json_identifiers_to_manifest_templates",
            "api_url": "https://digi.vatlib.it" + category,
            "records_path": "fond", "identifier_path": "shelfmark",
            "manifest_url_templates": ["https://digi.vatlib.it/iiif/MSS_{identifier}/manifest.json"],
            "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 50000, "max_pages": 1},
            "max_identifiers": 50000, "request_delay_seconds": 0.2,
            "coverage_note": "One server-declared manuscript category; all category routes retained. Other material classes are not yet inventoried.",
        } for category in categories],
    }
    knowledge_path = module / "config/discovery_knowledge.json"
    knowledge = json.loads(knowledge_path.read_text(encoding="utf-8"))
    for provider in providers[1:]:
        entry = {"provider_id": provider["provider_id"], "provider_name": provider["name"],
                 "investigation_id": "2026-10-15-three-provider-completion",
                 "investigation_document": "knowledge/institutions/2026-10-15_three_provider_completion.md",
                 "skills": recipes[provider["name"]]}
        knowledge["providers"] = [p for p in knowledge["providers"] if p["provider_id"] != provider["provider_id"]]
        knowledge["providers"].append(entry)
    save(knowledge_path, knowledge)
    endpoints_path = module / "config/provider_endpoints.json"
    endpoints = json.loads(endpoints_path.read_text(encoding="utf-8"))
    bsb = providers[0]
    entry = {"provider_id": bsb["provider_id"], "provider_name": bsb["name"],
             "entry_points": ["https://api.digitale-sammlungen.de/iiif/presentation/v2/collection/top"],
             "html_seeds": [], "investigation_id": "2026-10-15-three-provider-completion",
             "evidence_directory": "evaluation/2026-10-15_three_provider_completion",
             "guide_url": "https://iiif.io/guides/guides/digitale-sammlungen.de/"}
    endpoints["providers"] = [p for p in endpoints["providers"] if p["provider_id"] != bsb["provider_id"]]
    endpoints["providers"].append(entry)
    save(endpoints_path, endpoints)
    save(root / "recipes.json", recipes)
    ids = {p["provider_id"] for p in providers}
    checked = [json.loads(line) for line in (module.parent / "Module_2/data/output/checked_entry_points.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    (root / "checked_selected.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in checked if p["provider_id"] in ids), encoding="utf-8")
    network = {"timeout_seconds": 40, "retries": 1, "max_response_bytes": 64 * 1024 * 1024}
    config = {"input_jsonl": str(root / "checked_selected.jsonl"), "curated_endpoints": str(endpoints_path),
              "knowledge_base": str(knowledge_path), "output_directory": str(root / "validation/module3/output"),
              "log_directory": str(root / "validation/module3/log"), "network": network,
              "limits": {"max_stream_pages_per_provider": 2, "max_collections_per_provider": 100,
                         "max_html_pages_per_provider": 1, "max_html_depth": 1, "max_machine_candidates_per_provider": 10,
                         "max_manifests_per_provider": args.sample_limit},
              "html_discovery": {"enabled": False}, "platform_discovery": {"omeka_s_probe_enabled": False}}
    save(root / "module3_validation.json", config)
    save(root / "module4_validation.json", {
        "input_jsonl": str(root / "validation/module3/output/manifest_urls.jsonl"),
        "raw_manifest_directory": str(root / "validation/module4/raw_manifests"),
        "output_directory": str(root / "validation/module4/output"), "log_directory": str(root / "validation/module4/log"),
        "network": network, "run": {"force_refresh": True, "delay_between_requests_seconds": 0.2}})
    print(f"Prepared three providers; sample limit {args.sample_limit}; retained {len(categories)} Vatican category routes.")


if __name__ == "__main__":
    main()
