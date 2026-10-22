"""Prepare isolated, bounded tests for five reviewed public discovery routes."""

import json
from pathlib import Path

module = Path(__file__).resolve().parents[1]
code = module.parent
root = module / "evaluation/2026-10-21_five_provider_completion"
root.mkdir(parents=True, exist_ok=True)


def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


ids = ["provider-e1782e53439deb7b", "provider-d98fe11ebfc34f6d",
       "provider-c4aa50f2571a99e9", "provider-637a751532e5f5a3", "provider-c4bca842117bf9f7"]
census = [json.loads(s) for s in (code / "Module_1/data/output/providers.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
providers = [next(p for p in census if p["provider_id"] == pid) for pid in ids]
save("providers.json", providers)
(root / "selected_providers.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in providers), encoding="utf-8")

entries = []
for provider in providers:
    pid = provider["provider_id"]
    if pid == ids[0]:
        recipe = {
            "skill_id": "vatican-public-gallery-keyed-records",
            "type": "paginated_json_identifiers_to_manifest_templates",
            "api_url": "https://digi.vatlib.it/pickup/digital_gallery",
            "query_parameters": {"format": "ajax"},
            "records_path": "result", "records_format": "mapping_values", "identifier_path": "id",
            "identifier_pattern": r"^(?P<identifier>MSS_[A-Za-z0-9_.-]+)$",
            "manifest_url_templates": ["https://digi.vatlib.it/iiif/{identifier}/manifest.json"],
            "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 100, "max_pages": 1},
            "max_identifiers": 100, "request_delay_seconds": 0.8,
            "coverage_note": "Public selected-manuscripts gallery only (14 records observed), not the complete Vatican catalogue. Gallery API and native Manifest routes were verified separately."}
    elif pid == ids[1]:
        recipe = {
            "skill_id": "getty-sparql-objects-linked-art-manifests",
            "type": "paginated_json_identifiers_to_manifest_templates",
            "api_url": "https://data.getty.edu/museum/collection/sparql",
            "query_parameters": {"format": "json"},
            "query_parameter_templates": {"query": "SELECT ?s WHERE { ?s a <http://www.cidoc-crm.org/cidoc-crm/E22_Human-Made_Object> } ORDER BY ?s LIMIT {page_size} OFFSET {page_number}"},
            "records_path": "results.bindings", "identifier_path": "s.value",
            "identifier_pattern": r"^https://data\.getty\.edu/museum/collection/object/(?P<identifier>[a-f0-9-]+)$",
            "identifier_followup": {"url_template": "https://data.getty.edu/museum/collection/object/{identifier}",
                                    "identifier_path": "subject_of.*.id",
                                    "identifier_pattern": r"^https://media\.getty\.edu/iiif/manifest/3/(?P<identifier>[a-f0-9-]+)$"},
            "manifest_url_templates": ["https://media.getty.edu/iiif/manifest/3/{identifier}"],
            "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 8, "start_page": 0, "page_step": 8, "max_pages": 1000},
            "max_identifiers": 8000, "request_delay_seconds": 0.6,
            "coverage_note": "Getty Museum objects in the public SPARQL/Linked Art dataset with explicitly declared Presentation 3 links; not all Getty Research Institute holdings. Stable ordering is used for OFFSET pagination."}
    elif pid == ids[4]:
        recipe = {
            "skill_id": "nga-library-primo-mms-to-native-manifests",
            "type": "paginated_json_identifiers_to_manifest_templates",
            "api_url": "https://library.nga.gov/primaws/rest/pub/pnxs",
            "query_parameters": {"vid": "01NGA_INST:NGA", "tab": "LibraryCatalog", "scope": "MyInstitution", "lang": "en", "q": "any,contains,grandezze"},
            "records_path": "docs", "identifier_path": "pnx.control.sourcerecordid.0",
            "required_nonempty_paths": ["delivery.link.0.linkURL"],
            "identifier_pattern": r"^(?P<identifier>\d+)$",
            "manifest_url_templates": ["https://libraryimage.nga.gov/manifest/mms/{identifier}.json"],
            "pagination": {"page_parameter": "offset", "page_size_parameter": "limit", "page_size": 6, "start_page": 0, "page_step": 6, "max_pages": 3, "total_path": "info.total"},
            "max_identifiers": 100, "request_delay_seconds": 0.6,
            "coverage_note": "Public Primo catalogue query for grandezze (18 observed records), including physical titles and digital books. Only live native library Manifests are accepted. This validates a keyword subset, not the whole NGA catalogue or the separate NGA museum collection."}
    else:
        source_filters = {
            ids[3]: "ハーバード美術館API",
        }
        query = {"fc-_media": "IIIF"}
        if pid in source_filters:
            query["fc-source"] = source_filters[pid]
        native_patterns = {
            ids[2]: r"^https://(?!api\.cultural\.jp/).+",
            ids[3]: r"^https://iiif\.harvardartmuseums\.org/manifests/object/\d+$",
        }
        recipe = {
            "skill_id": {ids[2]: "cultural-japan-public-native-manifest-index", ids[3]: "cultural-japan-harvard-native-manifests"}[pid],
            "type": "paginated_json_manifest_links", "api_url": "https://api.cultural.jp/search",
            "query_parameters": query, "records_path": "hits.hits", "manifest_url_path": "manifest.*",
            "manifest_url_pattern": native_patterns[pid],
            "pagination": {"page_parameter": "page", "page_size_parameter": "size", "page_size": 6, "start_page": 1, "max_pages": 5},
            "request_delay_seconds": 0.6,
            "coverage_note": "Cultural Japan's indexed IIIF subset; follows explicitly declared native Manifests. The search total is capped at 10000 and is not a validated Manifest count. Some indexed URLs are stale; failures are retained. No API key was supplied or bypassed."}
    entries.append({"provider_id": pid, "provider_name": provider["name"],
                    "investigation_id": "2026-10-21-five-provider-discovery",
                    "investigation_document": "knowledge/institutions/2026-10-21_five_provider_completion.md",
                    "skills": [recipe]})

save("new_knowledge_entries.json", entries)
save("new_endpoint_entries.json", [])
save("candidate_discovery_knowledge.json", {"knowledge_base_version": "1.0", "providers": entries})
save("candidate_provider_endpoints.json", {"providers": []})
network = {"timeout_seconds": 35, "retries": 1, "backoff_seconds": 0.5, "max_response_bytes": 67108864}
save("module2_validation.json", {"input_jsonl": str(root / "selected_providers.jsonl"),
     "output_directory": str(root / "validation/module2/output"), "log_directory": str(root / "validation/module2/log"),
     "network": network, "run": {"delay_between_requests_seconds": 0.3}})
save("module3_validation.json", {"input_jsonl": str(root / "validation/module2/output/checked_entry_points.jsonl"),
     "knowledge_base": str(root / "candidate_discovery_knowledge.json"), "curated_endpoints": str(root / "candidate_provider_endpoints.json"),
     "output_directory": str(root / "validation/module3/output"), "log_directory": str(root / "validation/module3/log"),
     "network": network, "limits": {"max_stream_pages_per_provider": 3, "max_collections_per_provider": 6,
                                  "max_html_pages_per_provider": 1, "max_html_depth": 1,
                                  "max_machine_candidates_per_provider": 6, "max_manifests_per_provider": 6},
     "html_discovery": {"enabled": False}, "platform_discovery": {"omeka_s_probe_enabled": False}})
save("module4_validation.json", {"input_jsonl": str(root / "validation/module3/output/manifest_urls.jsonl"),
     "raw_manifest_directory": str(root / "validation/module4/raw_manifests"),
     "output_directory": str(root / "validation/module4/output"), "log_directory": str(root / "validation/module4/log"),
     "network": network, "run": {"force_refresh": True, "delay_between_requests_seconds": 0.6}})
save("sample_selection.json", {})
print("Prepared five reviewed sources:", root)
