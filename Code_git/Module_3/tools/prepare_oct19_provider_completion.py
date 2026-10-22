"""Prepare five reviewed routes in an isolated evaluation before promotion."""

import argparse
from copy import deepcopy
import json
from pathlib import Path


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-limit", type=int, default=20)
    args = parser.parse_args()
    module = Path(__file__).resolve().parents[1]
    code = module.parent
    root = module / "evaluation/2026-10-19_five_provider_completion"
    census = [json.loads(line) for line in (code / "Module_1/data/output/providers.jsonl").open(encoding="utf-8")]
    ids = ["provider-3e6e726f68de3eaa", "provider-7caa47e568a1951d", "provider-f1308a5306328276",
           "provider-028fd9292205c39c", "provider-6fb76c5e6a229a82"]
    providers = [next(p for p in census if p["provider_id"] == identifier) for identifier in ids]
    save(root / "providers.json", providers)
    knowledge = json.loads((module / "config/discovery_knowledge.json").read_text(encoding="utf-8"))
    endpoints = json.loads((module / "config/provider_endpoints.json").read_text(encoding="utf-8"))
    # Replays use this evaluation's frozen baseline after successful promotion.
    if (root / "before_discovery_knowledge.json").exists():
        knowledge = json.loads((root / "before_discovery_knowledge.json").read_text(encoding="utf-8"))
    if (root / "before_provider_endpoints.json").exists():
        endpoints = json.loads((root / "before_provider_endpoints.json").read_text(encoding="utf-8"))
    for filename, value in [("before_discovery_knowledge.json", knowledge), ("before_provider_endpoints.json", endpoints)]:
        if not (root / filename).exists():
            save(root / filename, value)
    roots = {
        ids[0]: ["https://www.e-rara.ch/i3f/v21/collection/all", "https://www.e-rara.ch/i3f/v21/collection/top"],
        ids[1]: ["https://www.e-manuscripta.ch/i3f/v21/collection/all", "https://www.e-manuscripta.ch/i3f/v21/collection/top"],
        ids[2]: ["https://fromthepage.com/iiif/collection/jeremiah-white-graves-diaries"],
        ids[4]: ["https://iiif.onb.ac.at/presentation/collection/wrz_1703",
                 "https://iiif.onb.ac.at/presentation/collection/wrz_1704",
                 "https://iiif.onb.ac.at/presentation/collection/jerusalem"],
    }
    candidates = []
    for provider in providers:
        identifier = provider["provider_id"]
        if identifier not in roots:
            continue
        entry = {"provider_id": identifier, "provider_name": provider["name"], "entry_points": roots[identifier],
                 "html_seeds": [], "investigation_id": "2026-10-19-five-provider-completion",
                 "evidence_directory": "evaluation/2026-10-19_five_provider_completion"}
        if any(p["provider_id"] == identifier for p in endpoints["providers"]):
            raise RuntimeError("An existing provider entry must not be overwritten")
        endpoints["providers"].append(entry)
        candidates.append(entry)
    recipe = {
        "provider_id": ids[3], "provider_name": providers[3]["name"],
        "investigation_id": "2026-10-19-five-provider-completion",
        "investigation_document": "knowledge/institutions/2026-10-19_five_provider_completion.md",
        "skills": [{
            "skill_id": "constellation-catalogue-to-declared-manifest-route",
            "type": "paginated_html_identifiers_to_manifest_templates",
            "api_url": "https://bodmerlab.unige.ch/fr/search",
            "query_parameters": {"keywords": ""},
            "record_url_pattern": r"/constellations/autographes/barcode/(?P<identifier>\d+)(?:$|[?#])",
            "manifest_url_templates": ["https://bodmerlab.unige.ch/fr/constellations/autographes/manifest/{identifier}"],
            "pagination": {"page_parameter": "Page", "page_size_parameter": "", "page_size": 21,
                           "start_page": 1, "max_pages": 1000, "detect_next_page": True},
            "max_identifiers": 50000, "request_delay_seconds": 0.35,
            "coverage_note": "Current executable scope is the autographes constellation. Other constellations are retained as investigation candidates, not asserted resolved."
        }]
    }
    if any(p["provider_id"] == ids[3] for p in knowledge["providers"]):
        raise RuntimeError("An existing provider recipe must not be overwritten")
    knowledge["providers"].append(recipe)
    save(root / "candidate_discovery_knowledge.json", knowledge)
    save(root / "candidate_provider_endpoints.json", endpoints)
    save(root / "new_endpoint_entries.json", candidates)
    save(root / "new_knowledge_entries.json", [recipe])
    # The already recorded Module 2 results are reused as input evidence only.
    checked = [json.loads(line) for line in (code / "Module_2/data/output/checked_entry_points.jsonl").open(encoding="utf-8")]
    chosen = [p for p in checked if p["provider_id"] in ids]
    if len(chosen) != 5:
        raise RuntimeError("Expected all five providers in the frozen Module 2 input")
    (root / "checked_selected.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in chosen), encoding="utf-8")
    network = {"timeout_seconds": 35, "retries": 1, "max_response_bytes": 64 * 1024 * 1024}
    config = {
        "input_jsonl": str(root / "checked_selected.jsonl"), "curated_endpoints": str(root / "candidate_provider_endpoints.json"),
        "knowledge_base": str(root / "candidate_discovery_knowledge.json"),
        "output_directory": str(root / "validation/module3/output"), "log_directory": str(root / "validation/module3/log"),
        "network": network, "limits": {"max_stream_pages_per_provider": 10, "max_collections_per_provider": 10,
            "max_html_pages_per_provider": 1, "max_html_depth": 1, "max_machine_candidates_per_provider": 10,
            "max_manifests_per_provider": args.sample_limit}, "html_discovery": {"enabled": False},
        "platform_discovery": {"omeka_s_probe_enabled": False}}
    save(root / "module3_validation.json", config)
    # A second isolated Bodmer run starts on page 2 and tests learned pagination.
    transfer = deepcopy(knowledge)
    transfer["providers"][-1]["skills"][0]["pagination"]["start_page"] = 2
    save(root / "bodmer_page2_knowledge.json", transfer)
    config2 = deepcopy(config)
    config2.update(knowledge_base=str(root / "bodmer_page2_knowledge.json"),
                   output_directory=str(root / "page2_check/module3/output"), log_directory=str(root / "page2_check/module3/log"))
    config2["limits"]["max_manifests_per_provider"] = 2
    (root / "checked_bodmer.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in chosen if p["provider_id"] == ids[3]), encoding="utf-8")
    config2["input_jsonl"] = str(root / "checked_bodmer.jsonl")
    save(root / "module3_page2_check.json", config2)
    save(root / "module4_validation.json", {
        "input_jsonl": str(root / "validation/module3/output/manifest_urls.jsonl"),
        "raw_manifest_directory": str(root / "validation/module4/raw_manifests"),
        "output_directory": str(root / "validation/module4/output"), "log_directory": str(root / "validation/module4/log"),
        "network": network, "run": {"force_refresh": True, "delay_between_requests_seconds": 0.65}})
    print(json.dumps({"providers": [p["name"] for p in providers], "sample_limit": args.sample_limit,
                      "global_configs_modified": False}, ensure_ascii=True))


if __name__ == "__main__":
    main()
