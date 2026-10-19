"""Configure reproducible catalogue discovery for five investigated providers."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode


def main():
    """Preserve knowledge, append recipes, and isolate live evaluation outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-limit", type=int, default=20)
    parser.add_argument("--batch", default="validation")
    args = parser.parse_args()
    module = Path(__file__).resolve().parents[1]
    root = module / "evaluation/2026-10-15_five_provider_completion"
    providers = json.loads((root / "providers.json").read_text(encoding="utf-8"))
    assert len(providers) == 5
    recipes = {}
    recipes["Göttingen University Collections"] = {
        "skill_id": "gdz-paginated-search-records", "type": "paginated_html_identifiers_to_manifest_templates",
        "api_url": "https://gdz.sub.uni-goettingen.de/suche",
        "record_url_pattern": r"/id/(?P<identifier>[^/?#]+)",
        "manifest_url_templates": ["https://manifests.sub.uni-goettingen.de/iiif/presentation/{identifier}/manifest"],
        "pagination": {"page_parameter": "page", "page_size_parameter": "", "page_size": 15,
                       "start_page": 1, "max_pages": 10000, "detect_next_page": True},
        "max_identifiers": 150000, "request_delay_seconds": 0.15,
    }
    leiden_query = {"type": "dismax", "f[0]": 'RELS_EXT_hasModel_uri_ms:"info\\:fedora\\/islandora\\:bookCModel"'}
    recipes["Leiden University"] = {
        "skill_id": "leiden-islandora-books-to-current-manifests", "type": "paginated_html_identifiers_to_manifest_templates",
        "api_url": "https://digitalcollections.universiteitleiden.nl/islandora/search?" + urlencode(leiden_query),
        "record_url_pattern": r"/view/item/(?P<identifier>\d+)",
        "manifest_url_templates": ["https://digitalcollections.universiteitleiden.nl/iiif_manifest/item:{identifier}/manifest"],
        "pagination": {"page_parameter": "page", "page_size_parameter": "", "page_size": 20,
                       "start_page": 0, "max_pages": 10000, "detect_next_page": True},
        "max_identifiers": 150000, "request_delay_seconds": 0.15,
        "coverage_note": "Book content-model query; individual child records may lack a Manifest. Redirects to migrated Alma Manifests are followed. Not all Leiden content models are inventoried.",
    }
    recipes["Utrecht University Library"] = {
        "skill_id": "utrecht-public-object-list-to-manifests", "type": "paginated_html_identifiers_to_manifest_templates",
        "api_url": "https://objects.library.uu.nl/reader/object-list?lan=en",
        "record_url_pattern": r"/reader/(?P<identifier>20\.500\.14918-\d+)(?:$|[?#])",
        "required_ancestor_class": "object-openaccess",
        "manifest_url_templates": ["https://objects.library.uu.nl/manifest/iiif/v3/{identifier}"],
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 30000,
                       "max_pages": 1},
        "max_identifiers": 30000, "request_delay_seconds": 0.15,
        "coverage_note": "Complete listing response; only entries labelled object-openaccess are selected. A public metadata row does not guarantee downloadable image content.",
    }
    recipes["Universitaet Jena"] = {
        "skill_id": "mycore-objects-to-derivatives-to-manifests", "type": "paginated_json_identifiers_to_manifest_templates",
        "api_url": "https://collections.thulb.uni-jena.de/api/v2/objects",
        "records_path": "$", "identifier_path": "id",
        "identifier_followup": {
            "url_template": "https://collections.thulb.uni-jena.de/api/v2/objects/{identifier}/derivates",
            "records_path": "$", "identifier_path": "href",
        },
        "manifest_url_templates": ["https://collections.thulb.uni-jena.de/api/iiif/presentation/v2/{identifier}/manifest"],
        "pagination": {"page_parameter": "offset", "page_size_parameter": "limit", "page_size": 20,
                       "page_step": 20, "start_page": 0, "max_pages": 10000},
        "max_identifiers": 200000, "request_delay_seconds": 0.15,
    }
    recipes["National Library of Wales"] = {
        "skill_id": "primo-viewer-identifiers-to-iiif-resources", "type": "paginated_json_identifiers_to_manifest_templates",
        "api_url": "https://discover.library.wales/primaws/rest/pub/pnxs",
        "records_path": "docs", "identifier_path": "delivery.availabilityLinksUrl.*",
        "identifier_pattern": r"https?://viewer\.library\.wales/(?P<identifier>\d+)",
        "query_parameters": {"vid": "44WHELF_NLW:44WHELF_NLW_NUI", "scope": "MyInstitution", "tab": "tab1",
                             "q": "any,contains,viewer.library.wales", "lang": "en"},
        "manifest_url_templates": ["https://iiif.llyfrgell.cymru/manifests/2.0/{identifier}/manifest.json"],
        "allow_collections": True,
        "pagination": {"page_parameter": "offset", "page_size_parameter": "limit", "page_size": 20,
                       "page_step": 20, "start_page": 0, "max_pages": 25},
        "max_identifiers": 500, "request_delay_seconds": 0.15,
        "coverage_note": "Primo query returns catalogue records matching viewer.library.wales; this query is not proof of all NLW digitized holdings. Collection responses are traversed by the native IIIF engine.",
    }
    knowledge_path = module / "config/discovery_knowledge.json"
    knowledge = json.loads(knowledge_path.read_text(encoding="utf-8"))
    for provider in providers:
        entry = {"provider_id": provider["provider_id"], "provider_name": provider["name"],
                 "investigation_id": "2026-10-15-five-provider-completion",
                 "investigation_document": "knowledge/institutions/2026-10-15_five_provider_completion.md",
                 "skills": [recipes[provider["name"]]]}
        knowledge["providers"] = [p for p in knowledge["providers"] if p["provider_id"] != provider["provider_id"]]
        knowledge["providers"].append(entry)
    knowledge_path.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "recipes.json").write_text(json.dumps(recipes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ids = {p["provider_id"] for p in providers}
    checked = [json.loads(line) for line in (module.parent / "Module_2/data/output/checked_entry_points.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    (root / "checked_selected.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in checked if p["provider_id"] in ids), encoding="utf-8")
    config = {"input_jsonl": str(root / "checked_selected.jsonl"), "curated_endpoints": str(module / "config/provider_endpoints.json"),
              "knowledge_base": str(knowledge_path), "output_directory": str(root / args.batch / "module3/output"),
              "log_directory": str(root / args.batch / "module3/log"),
              "network": {"timeout_seconds": 35, "retries": 1, "max_response_bytes": 64 * 1024 * 1024},
              "limits": {"max_stream_pages_per_provider": 2, "max_collections_per_provider": 100,
                         "max_html_pages_per_provider": 1, "max_html_depth": 1, "max_machine_candidates_per_provider": 10,
                         "max_manifests_per_provider": args.sample_limit},
              "html_discovery": {"enabled": False}, "platform_discovery": {"omeka_s_probe_enabled": False}}
    (root / f"module3_{args.batch}.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    module4 = {"input_jsonl": str(root / "combined/module3/output/manifest_urls.jsonl"),
               "raw_manifest_directory": str(root / args.batch / "module4/raw_manifests"),
               "output_directory": str(root / args.batch / "module4/output"), "log_directory": str(root / args.batch / "module4/log"),
               "network": {"timeout_seconds": 35, "retries": 1, "max_response_bytes": 64 * 1024 * 1024},
               "run": {"force_refresh": True, "delay_between_requests_seconds": 0.15}}
    (root / f"module4_{args.batch}.json").write_text(json.dumps(module4, indent=2), encoding="utf-8")
    print(f"Prepared five-provider {args.batch} run; limit {args.sample_limit} each.")


if __name__ == "__main__":
    main()
