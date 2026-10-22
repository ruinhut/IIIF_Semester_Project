"""Preserve the baseline and configure bounded live validation of reviewed routes."""

from pathlib import Path
import json


def main():
    module = Path(__file__).resolve().parents[1]
    root = module / "evaluation/2026-10-15_provider_investigation"
    providers = json.loads((root / "baseline_unresolved.json").read_text(encoding="utf-8"))
    by_name = {row["name"]: row for row in providers}
    curated_path = module / "config/provider_endpoints.json"
    knowledge_path = module / "config/discovery_knowledge.json"
    for path in (curated_path, knowledge_path):
        backup = root / ("baseline_" + path.name)
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
    curated = json.loads(curated_path.read_text(encoding="utf-8"))
    routes = {
        "University of Cambridge": "https://cudl.lib.cam.ac.uk/iiif/collection/all",
        "Lancaster University Library": "https://digitalcollections.lancaster.ac.uk/iiif/collection/all",
        "Huntington Digital Library": "https://hdl.huntington.org/iiif/2/manifest.json",
        "University of Leicester Library": "https://specialcollections.le.ac.uk/iiif/2/manifest.json",
        "Radboud University Library": "https://bijzonderecollecties.ubn.ru.nl/iiif/2/manifest.json",
        "University of Washington Libraries": "https://cdm16786.contentdm.oclc.org/iiif/2/manifest.json",
        "Durham University": "https://iiif.durham.ac.uk/manifests/trifle/collection/index",
        "Northwestern University": "https://api.dc.library.northwestern.edu/api/v2/collections?as=iiif",
        "National Library of Scotland": "https://view.nls.uk/collections/top.json",
        "University of Toronto": "https://iiif.library.utoronto.ca/presentation/collections",
    }
    for name, url in routes.items():
        provider = by_name[name]
        row = next((r for r in curated["providers"] if r.get("provider_id") == provider["provider_id"]), None)
        if row is None:
            row = {"provider_id": provider["provider_id"], "provider_name": name,
                   "entry_points": [], "html_seeds": []}
            curated["providers"].append(row)
        if url not in row["entry_points"]:
            row["entry_points"].append(url)
        row["investigation_id"] = "2026-10-15-provider-route-audit"
        row["evidence_directory"] = "evaluation/2026-10-15_provider_investigation"
        if name == "University of Washington Libraries":
            fallback = "https://cdm16786.contentdm.oclc.org/iiif/2/alaskawcanada/manifest.json"
            if fallback not in row["entry_points"]:
                row["entry_points"].append(fallback)
            row["coverage_note"] = "Top index may time out; fallback covers one collection only."
    curated_path.write_text(json.dumps(curated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    knowledge = json.loads(knowledge_path.read_text(encoding="utf-8"))
    name = "Wellcome Collection"
    provider = by_name[name]
    recipe = {
        "provider_id": provider["provider_id"], "provider_name": name,
        "investigation_id": "2026-10-15-wellcome-catalogue-links",
        "investigation_document": "knowledge/institutions/2026-10-15_provider_routes.md",
        "skills": [{
            "skill_id": "wellcome-paginated-declared-manifests",
            "type": "paginated_json_manifest_links",
            "api_url": "https://api.wellcomecollection.org/catalogue/v2/works",
            "records_path": "results", "manifest_url_path": "items.*.locations.*.url",
            "query_parameters": {"items.locations.locationType": "iiif-presentation", "include": "items"},
            "pagination": {"page_parameter": "page", "page_size_parameter": "pageSize",
                           "page_size": 5, "max_pages": 3},
            "request_delay_seconds": 0.25,
        }],
    }
    knowledge["providers"] = [r for r in knowledge["providers"] if r.get("provider_id") != provider["provider_id"]]
    knowledge["providers"].append(recipe)
    name = "e-codices - Virtual Manuscript Library of Switzerland"
    ecodices_names = {name, "e-codices"}
    for ecodices_name in ecodices_names:
        provider = by_name[ecodices_name]
        html_recipe = {
            "provider_id": provider["provider_id"], "provider_name": ecodices_name,
            "investigation_id": "2026-10-15-ecodices-targeted-catalogue",
            "investigation_document": "knowledge/institutions/2026-10-15_provider_routes.md",
            "skills": [{
                "skill_id": "ecodices-catalogue-record-identifiers",
                "type": "paginated_html_identifiers_to_manifest_templates",
                "api_url": "https://www.e-codices.ch/en/list/all",
                "record_url_pattern": r"/en/list/one/(?P<library>[^/]+)/(?P<shelfmark>[^/?#]+)",
                "identifier_template": "{library}-{shelfmark}",
                "manifest_url_templates": ["https://www.e-codices.ch/metadata/iiif/{identifier}/manifest.json"],
                "pagination": {"page_size": 100, "max_pages": 1},
                "max_identifiers": 5, "request_delay_seconds": 0.3,
                "coverage_note": "One listing response only; catalogue pagination is not yet established.",
            }],
        }
        knowledge["providers"] = [r for r in knowledge["providers"] if r.get("provider_id") != provider["provider_id"]]
        knowledge["providers"].append(html_recipe)
    provider = by_name["Northwestern University"]
    nw_recipe = {
        "provider_id": provider["provider_id"], "provider_name": "Northwestern University",
        "investigation_id": "2026-10-15-northwestern-api-transfer",
        "investigation_document": "knowledge/institutions/2026-10-15_provider_routes.md",
        "skills": [{
            "skill_id": "northwestern-paginated-declared-manifests",
            "type": "paginated_json_manifest_links",
            "api_url": "https://api.dc.library.northwestern.edu/api/v2/search",
            "records_path": "data", "manifest_url_path": "iiif_manifest",
            "query_parameters": {"query": "*"},
            "pagination": {"page_parameter": "page", "page_size_parameter": "size",
                           "page_size": 5, "max_pages": 3},
            "request_delay_seconds": 0.25,
        }],
    }
    knowledge["providers"] = [r for r in knowledge["providers"] if r.get("provider_id") != provider["provider_id"]]
    knowledge["providers"].append(nw_recipe)
    knowledge_path.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    names = set(routes) | {"Wellcome Collection"} | ecodices_names
    ids = {by_name[n]["provider_id"] for n in names}
    checked = module.parent / "Module_2/data/output/checked_entry_points.jsonl"
    selected = [json.loads(line) for line in checked.read_text(encoding="utf-8").splitlines()
                if line.strip() and json.loads(line).get("provider_id") in ids]
    (root / "checked_selected.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in selected), encoding="utf-8")
    config = {
        "input_jsonl": str(root / "checked_selected.jsonl"),
        "curated_endpoints": str(curated_path), "knowledge_base": str(knowledge_path),
        "output_directory": str(root / "module3/output"), "log_directory": str(root / "module3/log"),
        "network": {"timeout_seconds": 15, "retries": 0, "max_response_bytes": 16 * 1024 * 1024},
        "limits": {"max_stream_pages_per_provider": 2, "max_collections_per_provider": 30,
                   "max_html_pages_per_provider": 1, "max_html_depth": 1,
                   "max_machine_candidates_per_provider": 10, "max_manifests_per_provider": 5},
        "html_discovery": {"enabled": False}, "platform_discovery": {"omeka_s_probe_enabled": False},
    }
    (root / "module3_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print("Prepared", len(ids), "previously unresolved providers; original outputs retained.")


if __name__ == "__main__":
    main()
