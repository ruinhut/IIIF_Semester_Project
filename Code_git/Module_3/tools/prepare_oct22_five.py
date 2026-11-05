"""Register four public libraries and restore KU Leuven through Lovaniensia.

Keep the original Leuven identity and every existing endpoint. Prepare an
isolated, bounded live run; promotion follows independent image verification.
"""
import json
from pathlib import Path
import sys

module = Path(__file__).resolve().parents[1]
code = module.parent
sys.path.insert(0, str(code / "Module_1"))
from iiif_provider_census.pipeline import run_pipeline
from iiif_provider_census.store import read_jsonl, write_csv

root = module / "evaluation/2026-10-22_five_provider_completion"
previous = module / "evaluation/2026-10-21_fourth_five_provider_completion"
root.mkdir(exist_ok=True)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


definitions = [
    ("Badische Landesbibliothek Karlsruhe", "https://www.blb-karlsruhe.de/",
     "https://digital.blb-karlsruhe.de/i3f/v21/collection/178827",
     "https://digital.blb-karlsruhe.de/blbdd/wiki/schnittstellen", "Incunabula"),
    ("Paderborn University Library", "https://www.ub.uni-paderborn.de/",
     "https://digital.ub.uni-paderborn.de/i3f/v21/collection/8437472",
     "https://digital.ub.uni-paderborn.de/", "Zugschwerdt'sche Leihbibliothek"),
    ("Bonn University and State Library", "https://www.ulb.uni-bonn.de/",
     "https://digitale-sammlungen.ulb.uni-bonn.de/i3f/v21/collection/10250864",
     "https://digitale-sammlungen.ulb.uni-bonn.de/ulbbn/wiki/about", "Medieval manuscripts"),
    ("Frankfurt University Library", "https://www.ub.uni-frankfurt.de/",
     "https://sammlungen.ub.uni-frankfurt.de/i3f/v21/collection/all",
     "https://sammlungen.ub.uni-frankfurt.de/", "All-collection first-page sample"),
]
additions = [{"name": name, "institution_url": institution, "discovery_endpoint": endpoint,
              "discovery_type": "Collection", "endpoint_role": "presentation_collection",
              "source_page_url": evidence} for name, institution, endpoint, evidence, subset in definitions]
manual_path = code / "Module_1/config/manual_providers.json"
manual = json.loads(manual_path.read_text(encoding="utf-8"))
existing_urls = {p.get("institution_url") for p in manual["providers"]}
for provider in additions:
    if provider["institution_url"] not in existing_urls:
        manual["providers"].append(provider)
save(root / "additional_provider_source.json", {"providers": additions})
save(root / "module1_registration.json", {"registry_sources": [],
    "manual_sources": [str(root / "additional_provider_source.json")],
    "output_directory": str(root / "registration/module1/output"),
    "log_directory": str(root / "registration/module1/log")})
run_pipeline(root / "module1_registration.json", institution_selection=["all"])
new_records = read_jsonl(root / "registration/module1/output/providers.jsonl")
census_path = code / "Module_1/data/output/providers.jsonl"
backup = root / "before_provider_census.jsonl"
if not backup.exists():
    backup.write_bytes(census_path.read_bytes())
census = [json.loads(s) for s in census_path.read_text(encoding="utf-8").splitlines() if s.strip()]
known = {p["provider_id"] for p in census}
for record in new_records:
    if record.provider_id not in known:
        census.append(record.to_dict())

leuven_id = "provider-ef2f1cc06db37bc3"
leuven = next(p for p in census if p["provider_id"] == leuven_id)
endpoint = {"url": "https://www.lovaniensia.be/items/browse", "endpoint_role": "catalogue_listing",
    "discovery_type": "HTML", "label": "Lovaniensia public catalogue, checked 2026-10-22",
    "verification_status": "unverified", "source": {"source_type": "institution_documentation",
        "source_url": "https://www.lovaniensia.be/", "source_page_url": "https://www.lovaniensia.be/",
        "observed_at": "2026-10-22T13:00:00Z"}}
if not any(e["url"] == endpoint["url"] for e in leuven["endpoints"]):
    leuven["endpoints"].append(endpoint)
    leuven["endpoint_count"] = len(leuven["endpoints"])
if not any(p.get("provider_id") == leuven_id for p in manual["providers"]):
    manual["providers"].append({"provider_id": leuven_id, "name": leuven["name"],
        "institution_url": leuven["institution_url"], "source_page_url": "https://www.lovaniensia.be/",
        "endpoints": [endpoint]})
save(manual_path, manual)
census_path.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in census), encoding="utf-8")
write_csv(census_path.with_suffix(".csv"), read_jsonl(census_path))
providers = [leuven] + [p.to_dict() for p in new_records]
save(root / "providers.json", providers)
(root / "selected_providers.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in providers), encoding="utf-8")

leuven_recipe = {
    "skill_id": "ku-leuven-lovaniensia-public-catalogue-detail-manifests",
    "type": "paginated_html_identifiers_to_manifest_templates",
    "api_url": "https://www.lovaniensia.be/items/browse",
    "record_url_pattern": r"^https://www\.lovaniensia\.be/items/show/(?P<identifier>\d+)$",
    "identifier_followup": {"url_template": "https://www.lovaniensia.be/items/show/{identifier}",
        "format": "html", "identifier_pattern": r"^https://data\.lovaniensia\.be/(?P<identifier>IE\d+)/manifest$"},
    "manifest_url_templates": ["https://data.lovaniensia.be/{identifier}/manifest"],
    "pagination": {"page_parameter": "page", "page_size_parameter": "", "page_size": 20,
                   "start_page": 1, "max_pages": 100, "detect_next_page": True},
    "max_identifiers": 2000,
    "coverage_note": "Public Lovaniensia catalogue subset. Follow declared item links, then the explicit Manifest anchor; do not guess IE numbers. The first sample records' Location metadata identifies KU Leuven Libraries Special Collections. Lovaniensia is a collaborative project, so provenance must be retained rather than assigning every future record to KU. Its /api/items returned 403; this recipe uses the accessible public catalogue and does not bypass that restriction."}
entries = []
for provider in providers:
    if provider["provider_id"] == leuven_id:
        recipe = leuven_recipe
    else:
        name, institution, endpoint_url, evidence, subset = next(d for d in definitions if d[0] == provider["name"])
        recipe = {"skill_id": provider["provider_id"] + "-native-visuallibrary-collection-members",
            "type": "paginated_json_manifest_links", "api_url": endpoint_url,
            "records_path": "members", "manifest_url_path": "@id", "manifest_url_pattern": r"/manifest$",
            "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 100, "max_pages": 1},
            "coverage_note": subset + ". This fallback reads the native Collection's first-page explicit members only. The main generic IIIF Collection walker separately supports declared next links; the bounded run stops at six Manifests, not at catalogue exhaustion. No catalogue-wide count is inferred from the sample."}
    recipe["request_delay_seconds"] = 0.6
    entries.append({"provider_id": provider["provider_id"], "provider_name": provider["name"],
        "investigation_id": "2026-10-22-five-provider-discovery",
        "investigation_document": "knowledge/institutions/2026-10-22_five_provider_completion.md", "skills": [recipe]})
save(root / "new_knowledge_entries.json", entries)
save(root / "new_endpoint_entries.json", [])
save(root / "candidate_discovery_knowledge.json", {"knowledge_base_version": "1.0", "providers": entries})
save(root / "candidate_provider_endpoints.json", {"providers": []})
for filename in ["module2_validation.json", "module3_validation.json", "module4_validation.json"]:
    value = (previous / filename).read_text(encoding="utf-8").replace(str(previous).replace("\\", "\\\\"), str(root).replace("\\", "\\\\"))
    save(root / filename, json.loads(value))
save(root / "sample_selection.json", {})
print("Prepared:", [(p["name"], p["provider_id"]) for p in providers])
