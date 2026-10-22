"""Register five new institutions and prepare isolated, reproducible validation."""
import json
from pathlib import Path
import sys
from urllib.parse import urlencode

module = Path(__file__).resolve().parents[1]
code = module.parent
sys.path.insert(0, str(code / "Module_1"))
from iiif_provider_census.pipeline import run_pipeline
from iiif_provider_census.store import read_jsonl, write_csv

root = module / "evaluation/2026-10-21_fourth_five_provider_completion"
previous = module / "evaluation/2026-10-21_third_five_provider_completion"
root.mkdir(exist_ok=True)


def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


norway_query = {"q": "mediatype:bøker AND digital:Ja", "filter": "date:[15000101 TO 19001231]", "digitalAccessibleOnly": "true"}
definitions = [
    ("University of Manchester Library", "https://www.library.manchester.ac.uk/",
     "https://www.digitalcollections.manchester.ac.uk/search/JSONAdvanced?keyword=manuscript&start=0&end=20",
     "JSON API", "https://www.digitalcollections.manchester.ac.uk/help/"),
    ("Pennsylvania State University Libraries", "https://libraries.psu.edu/",
     "https://digital.libraries.psu.edu/iiif/2/ejb/manifest.json", "Collection",
     "https://digital.libraries.psu.edu/digital/collection/ejb"),
    ("National Library of Norway", "https://www.nb.no/",
     "https://api.nb.no/catalog/v1/items?" + urlencode({**norway_query, "size": 6}),
     "JSON API", "https://api.nb.no/catalog/v1/items/api-docs"),
    ("Berlin State Library", "https://staatsbibliothek-berlin.de/",
     "https://oai.sbb.berlin/?verb=ListRecords&metadataPrefix=oai_dc", "OAI-PMH",
     "https://lab.sbb.berlin/dc/?lang=en"),
    ("University Library of Bern", "https://www.ub.unibe.ch/",
     "https://iiif.ub.unibe.ch/presentation/v2.1/collection/691e6e0c-afc2-4f17-aee5-d9f88be15865/",
     "Collection", "https://ub-unibe-ch.github.io/IIIF_Server/presentation_api/"),
]
additions = [{"name": name, "institution_url": institution, "discovery_endpoint": endpoint,
              "discovery_type": kind, "endpoint_role": "presentation_collection" if kind == "Collection" else "catalogue_api",
              "source_page_url": evidence} for name, institution, endpoint, kind, evidence in definitions]
manual_path = code / "Module_1/config/manual_providers.json"
manual = json.loads(manual_path.read_text(encoding="utf-8"))
existing_urls = {p.get("institution_url") for p in manual["providers"]}
for provider in additions:
    if provider["institution_url"] not in existing_urls:
        manual["providers"].append(provider)
manual_path.write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
save("additional_provider_source.json", {"providers": additions})
save("module1_registration.json", {"registry_sources": [],
    "manual_sources": [str(root / "additional_provider_source.json")],
    "output_directory": str(root / "registration/module1/output"),
    "log_directory": str(root / "registration/module1/log")})
run_pipeline(root / "module1_registration.json", institution_selection=["all"])
records = read_jsonl(root / "registration/module1/output/providers.jsonl")
census_path = code / "Module_1/data/output/providers.jsonl"
if not (root / "before_provider_census.jsonl").exists():
    (root / "before_provider_census.jsonl").write_bytes(census_path.read_bytes())
known = {p.provider_id for p in read_jsonl(census_path)}
with census_path.open("a", encoding="utf-8", newline="\n") as handle:
    for record in records:
        if record.provider_id not in known:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
write_csv(census_path.with_suffix(".csv"), read_jsonl(census_path))
providers = [p.to_dict() for p in records]
save("providers.json", providers)
(root / "selected_providers.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in providers), encoding="utf-8")

recipes = {
    "University of Manchester Library": {
        "skill_id": "manchester-xtf-json-range-search-to-manifests",
        "type": "paginated_json_identifiers_to_manifest_templates",
        "api_url": "https://www.digitalcollections.manchester.ac.uk/search/JSONAdvanced",
        "query_parameters": {"keyword": "manuscript"},
        "query_parameter_templates": {"start": "{page_number}", "end": "{page_end}"},
        "records_path": "items", "identifier_path": "item.id.0",
        "identifier_pattern": r"^(?P<identifier>[A-Za-z0-9_-]+)$",
        "manifest_url_templates": ["https://www.digitalcollections.manchester.ac.uk/iiif/{identifier}"],
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 20,
                       "start_page": 0, "page_step": 20, "max_pages": 100, "total_path": "info.hits"},
        "max_identifiers": 2000,
        "coverage_note": "Manuscript keyword subset. The site's own search JavaScript calls JSONAdvanced with start/end ranges, in 20-result pages. Object IDs are item.id[0]. Some image bodies are Image service roots; existing M8 service fallback supplies actual JPEG requests."},
    "Pennsylvania State University Libraries": {
        "skill_id": "penn-state-contentdm-public-diary-collection",
        "type": "paginated_json_manifest_links",
        "api_url": definitions[1][2], "records_path": "manifests", "manifest_url_path": "@id",
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 1000, "max_pages": 1},
        "coverage_note": "One public Elisha J. Bracken Civil War Diary compound object, discovered through CONTENTdm's declared collection Manifest. This is not the whole university catalogue. The public collection-list API supplies other collection aliases for later expansion."},
    "National Library of Norway": {
        "skill_id": "norway-public-digital-books-hal-presentation-links",
        "type": "paginated_json_manifest_links",
        "api_url": "https://api.nb.no/catalog/v1/items", "query_parameters": norway_query,
        "records_path": "_embedded.items", "manifest_url_path": "_links.presentation.href",
        "manifest_url_pattern": r"^https://api\.nb\.no(?::443)?/catalog/v1/iiif/[^/]+/manifest$",
        "pagination": {"page_parameter": "page", "page_size_parameter": "size", "page_size": 6, "start_page": 0, "max_pages": 100},
        "coverage_note": "Digitally available books, publication date 1500–1900, digitalAccessibleOnly=true. Follow explicit HAL presentation links; public metadata alone does not prove an image is accessible. No login, geography or rights restriction is bypassed."},
    "Berlin State Library": {
        "skill_id": "berlin-oai-ppn-identifiers-to-native-manifests",
        "type": "paginated_xml_identifiers_to_manifest_templates",
        "api_url": "https://oai.sbb.berlin/", "query_parameters": {"verb": "ListRecords", "metadataPrefix": "oai_dc"},
        "xml_namespaces": {"oai": "http://www.openarchives.org/OAI/2.0/"},
        "xml_record_path": ".//oai:record", "xml_identifier_path": "oai:header/oai:identifier",
        "identifier_pattern": r"^oai:digital\.staatsbibliothek-berlin\.de:(?P<identifier>PPN[0-9X]+)$",
        "manifest_url_templates": ["https://content.staatsbibliothek-berlin.de/dc/{identifier}/manifest"],
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 50, "max_pages": 100,
                       "next_token_path": ".//oai:resumptionToken", "token_keep_parameters": ["verb"]},
        "max_identifiers": 5000,
        "coverage_note": "Public digitised-collections OAI identifier stream. OAI PPN strings can end in X; do not force numeric IDs. Resumption tokens are opaque even if their text already contains percent escapes."},
    "University Library of Bern": {
        "skill_id": "bern-public-haller-gga-iiif-collection",
        "type": "paginated_json_manifest_links",
        "api_url": definitions[4][2], "records_path": "manifests", "manifest_url_path": "@id",
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 1000, "max_pages": 1},
        "coverage_note": "Haller GGA Collection explicitly linked from the institution's IIIF server manual. The run samples six volumes; it does not enumerate all Bern projects."},
}
entries = []
for provider in providers:
    recipe = recipes[provider["name"]]
    recipe["request_delay_seconds"] = 0.6
    entries.append({"provider_id": provider["provider_id"], "provider_name": provider["name"],
        "investigation_id": "2026-10-21-fourth-five-provider-discovery",
        "investigation_document": "knowledge/institutions/2026-10-21_fourth_five_provider_completion.md",
        "skills": [recipe]})
save("new_knowledge_entries.json", entries)
save("new_endpoint_entries.json", [])
save("candidate_discovery_knowledge.json", {"knowledge_base_version": "1.0", "providers": entries})
save("candidate_provider_endpoints.json", {"providers": []})
for filename in ["module2_validation.json", "module3_validation.json", "module4_validation.json"]:
    value = (previous / filename).read_text(encoding="utf-8").replace(str(previous).replace("\\", "\\\\"), str(root).replace("\\", "\\\\"))
    save(filename, json.loads(value))
save("sample_selection.json", {})
print("Prepared:", [(p["name"], p["provider_id"]) for p in providers])
