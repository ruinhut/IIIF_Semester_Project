"""Prepare an isolated second five-source investigation, preserving old recipes."""

import json
from pathlib import Path

module = Path(__file__).resolve().parents[1]
code = module.parent
root = module / "evaluation/2026-10-21_second_five_provider_completion"
root.mkdir(parents=True, exist_ok=True)


def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


ids = ["provider-fe4c0f49dea727df", "provider-9c24703f7d539465",
       "provider-e8f0640dd782bf74", "provider-f2fa8935cf790b44", "provider-feedf2702c521119"]
census = [json.loads(s) for s in (code / "Module_1/data/output/providers.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
providers = [next(p for p in census if p["provider_id"] == pid) for pid in ids]
save("providers.json", providers)
(root / "selected_providers.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in providers), encoding="utf-8")

recipes = {
    ids[0]: {
        "skill_id": "bsb-east-asia-result-data-manifests",
        "type": "paginated_html_identifiers_to_manifest_templates",
        "api_url": "https://ostasien.digitale-sammlungen.de/search",
        "query_parameters": {"q": "China", "searchType": "free"},
        "record_url_attributes": ["data-manifest"],
        "record_url_pattern": r"^https://api\.digitale-sammlungen\.de/iiif/presentation/v2/(?P<identifier>bsb\d+)/manifest$",
        "manifest_url_templates": ["https://api.digitale-sammlungen.de/iiif/presentation/v2/{identifier}/manifest"],
        "pagination": {"page_parameter": "start", "page_size_parameter": "rows", "page_size": 10,
                       "start_page": 0, "max_pages": 100, "detect_next_page": True},
        "max_identifiers": 1000, "request_delay_seconds": 0.5,
        "coverage_note": "Keyword China in the BSB East Asian catalogue (108 search hits observed). start is a zero-based page number, not a row offset. This is a collection subset of BSB, not a new independent institution or a full-catalogue total."},
    ids[1]: {
        "skill_id": "cardiff-public-primo-mms-to-alma-manifests",
        "type": "paginated_json_identifiers_to_manifest_templates",
        "api_url": "https://librarysearch.cardiff.ac.uk/primaws/rest/pub/pnxs",
        "query_parameters": {"vid": "44WHELF_CAR:44WHELF_CAR_VU1", "tab": "LibraryCatalog",
                             "scope": "MyInstitution", "q": "any,contains,Ellor", "lang": "en"},
        "records_path": "docs", "identifier_path": "pnx.control.sourcerecordid.0",
        "filters": [{"path": "delivery.hasD", "equals": True}],
        "identifier_pattern": r"^(?P<identifier>\d+)$",
        "manifest_url_templates": ["https://librarysearch.cardiff.ac.uk/view/iiif/presentation/44WHELF_CAR/{identifier}/manifest"],
        "pagination": {"page_parameter": "offset", "page_size_parameter": "limit", "page_size": 6,
                       "start_page": 0, "page_step": 6, "max_pages": 10, "total_path": "info.total"},
        "max_identifiers": 60, "request_delay_seconds": 0.5,
        "coverage_note": "Ellor keyword subset: 9 catalogue hits, only records explicitly declaring digital delivery are selected. Ex Libris documents MMS-to-representation redirects, so guessing representation IDs is unnecessary."},
    ids[3]: {
        "skill_id": "hmml-dreamsea-public-catalogue-detail-manifests",
        "type": "paginated_html_identifiers_to_manifest_templates",
        "api_url": "https://hmmlcloud.org/dreamsea/manuscripts.php",
        "query_parameters": {"country": "Laos", "searchType": "1"},
        "record_url_pattern": r"^https://hmmlcloud\.org/dreamsea/detail\.php\?msid=(?P<identifier>\d+)$",
        "identifier_followup": {"url_template": "https://hmmlcloud.org/dreamsea/detail.php?msid={identifier}",
                                "format": "html", "include_visible_url_text": True,
                                "identifier_pattern": r"^https://www\.vhmml\.org/image/manifest/(?P<identifier>\d+)$"},
        "manifest_url_templates": ["https://www.vhmml.org/image/manifest/{identifier}"],
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 5000, "max_pages": 1},
        "max_identifiers": 50, "request_delay_seconds": 0.6,
        "coverage_note": "DREAMSEA public Laos subset; native vHMML Manifest numbers are read from visible detail-page URL text, not inferred from DREAMSEA IDs. Restricted Reading Room search is not bypassed; public partner catalogue and images are used."},
    ids[4]: {
        "skill_id": "yale-lux-linked-art-library-manifests",
        "type": "paginated_json_identifiers_to_manifest_templates",
        "api_url": "https://lux.collections.yale.edu/api/search/item",
        "query_parameters": {"q": json.dumps({"AND": [{"hasDigitalImage": 1}, {"text": "manuscript"}]}, separators=(",", ":"))},
        "records_path": "orderedItems", "identifier_path": "id",
        "identifier_pattern": r"^https://lux\.collections\.yale\.edu/data/object/(?P<identifier>[a-f0-9-]+)$",
        "identifier_followup": {"url_template": "https://lux.collections.yale.edu/data/object/{identifier}",
                                "identifier_path": "subject_of.*.digitally_carried_by.*.access_point.*.id",
                                "identifier_pattern": r"^https://collections\.library\.yale\.edu/manifests/(?P<identifier>\d+)$"},
        "manifest_url_templates": ["https://collections.library.yale.edu/manifests/{identifier}"],
        "pagination": {"page_parameter": "page", "page_size_parameter": "pageLength", "page_size": 6,
                       "start_page": 1, "max_pages": 100, "has_next_path": "next.id"},
        "max_identifiers": 600, "request_delay_seconds": 0.6,
        "coverage_note": "Public Yale LUX manuscript-with-digital-image search; only explicitly declared Yale Library Manifest URLs are accepted. LUX estimate 5234 is a search estimate, not a validated Manifest total; one LUX object can declare several volume Manifests."},
}
entries = [{"provider_id": p["provider_id"], "provider_name": p["name"],
            "investigation_id": "2026-10-21-second-five-provider-discovery",
            "investigation_document": "knowledge/institutions/2026-10-21_second_five_provider_completion.md",
            "skills": [recipes[p["provider_id"]]]} for p in providers if p["provider_id"] in recipes]
endpoints = [{"provider_id": ids[2], "provider_name": providers[2]["name"],
              "entry_points": ["https://presentation-api.dlcs-trial.digirati.io/176/leeds-imc/university-of-leeds-medieval-manuscripts"],
              "html_seeds": [], "investigation_id": "2026-10-21-second-five-provider-discovery",
              "evidence_directory": "evaluation/2026-10-21_second_five_provider_completion",
              "coverage_note": "Public IMC workshop Collection declares native Leeds Manifests; this is a selected medieval-manuscripts set, not the entire Leeds catalogue. The main catalogue search returned HTTP 403."}]
save("new_knowledge_entries.json", entries)
save("new_endpoint_entries.json", endpoints)
save("candidate_discovery_knowledge.json", {"knowledge_base_version": "1.0", "providers": entries})
save("candidate_provider_endpoints.json", {"providers": endpoints})

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
save("sample_selection.json", {
    ids[0]: {"manifest_url_pattern": r"/bsb11178213/manifest$", "canvas_sequence": 9},
    ids[3]: {"canvas_sequence": 3},
})
print("Prepared:", root)
