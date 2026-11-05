"""Register seven distinct holders and prepare bounded, reproducible live checks.

RSS recipes cover the public feed subset, not an entire institution. Shared
Schriftgut.SH feeds are filtered by the owner declared in the source catalogue.
"""
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlencode

module = Path(__file__).resolve().parents[1]
code = module.parent
sys.path.insert(0, str(code / "Module_1"))
from iiif_provider_census.pipeline import run_pipeline
from iiif_provider_census.store import read_jsonl, write_csv

root = module / "evaluation/2026-10-22_third_seven_provider_completion"
previous = module / "evaluation/2026-10-22_second_seven_provider_completion"


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rss(name, institution, base, evidence, *, owner=None, descending=True):
    parameters = {"query": f'MD_DV_OWNER:"{owner}"' if owner else "",
                  "sortField": "DATECREATED", "sortDescending": str(descending).lower()}
    api = base + "/api/v1/records/rss"
    # The feed is declared by the site's HTML. Do not invent numeric pagination:
    # these installations return a capped public feed with no declared next URL.
    skill = {"type": "paginated_xml_identifiers_to_manifest_templates", "api_url": api,
        "query_parameters": parameters, "xml_namespaces": {},
        "xml_record_path": ".//item", "xml_identifier_path": "link",
        "identifier_pattern": r"^" + re.escape(base) + r"/(?:image|metadata|toc)/(?P<identifier>[^/?#]+)(?:/.*)?$",
        "manifest_url_templates": [base + "/api/v1/records/{identifier}/manifest/"],
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 50, "max_pages": 1},
        "max_identifiers": 50, "request_delay_seconds": 0.6,
        "coverage_note": "Public RSS feed subset (at most 50 feed records); no complete-catalogue or numeric-pagination claim. Each generated native Manifest must be validated."}
    if owner:
        skill["coverage_note"] += " Shared portal filtered by MD_DV_OWNER=" + owner + "; check holder metadata independently."
    return {"name": name, "institution_url": institution, "source_page_url": evidence,
            "discovery_endpoint": api + "?" + urlencode(parameters),
            "discovery_type": "OpenSearch RSS", "endpoint_role": "catalogue_api"}, skill


definitions = [rss("University of Kassel Library", "https://www.uni-kassel.de/ub/",
    "https://orka.bibliothek.uni-kassel.de/viewer", "https://orka.bibliothek.uni-kassel.de/viewer/"),
    rss("Kiel University Library", "https://www.ub.uni-kiel.de/", "https://schriftgut.sh/viewer",
        "https://schriftgut.sh/viewer/partner/ub-kiel/", owner="Universitätsbibliothek Kiel"),
    rss("Kiel City Archives", "https://www.kiel.de/de/bildung_wissenschaft/stadtarchiv/", "https://schriftgut.sh/viewer",
        "https://schriftgut.sh/viewer/partner/stadtarchiv-kiel/", owner="Stadtarchiv Kiel"),
    rss("Humboldt University of Berlin Library", "https://www.ub.hu-berlin.de/", "https://www.digi-hub.de/viewer",
        "https://www.digi-hub.de/viewer/", descending=False),
    rss("Berlin Central and Regional Library", "https://www.zlb.de/", "https://digital.zlb.de/viewer",
        "https://digital.zlb.de/viewer/", descending=False)]

dresden_api = "https://digital.slub-dresden.de/oai/"
definitions.append(({"name": "SLUB Dresden", "institution_url": "https://www.slub-dresden.de/",
    "source_page_url": "https://digital.slub-dresden.de/",
    "discovery_endpoint": dresden_api + "?verb=ListRecords&metadataPrefix=oai_dc",
    "discovery_type": "OAI-PMH", "endpoint_role": "catalogue_api"},
    {"type": "paginated_xml_identifiers_to_manifest_templates", "api_url": dresden_api,
     "query_parameters": {"verb": "ListRecords", "metadataPrefix": "oai_dc"},
     "xml_namespaces": {"oai": "http://www.openarchives.org/OAI/2.0/"},
     "xml_record_path": ".//oai:record", "xml_identifier_path": "oai:header/oai:identifier",
     "identifier_pattern": r"^oai:de:slub-dresden:db:id-(?P<identifier>[0-9Xx-]+)$",
     "manifest_url_templates": ["https://iiif.slub-dresden.de/iiif/2/{identifier}/manifest.json"],
     "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 50,
                    "max_pages": 100, "next_token_path": ".//oai:resumptionToken", "token_keep_parameters": ["verb"]},
     "max_identifiers": 5000, "request_delay_seconds": 0.6,
     "coverage_note": "Public OAI-PMH record identifiers, with opaque continuation tokens. A catalogue record is not assumed to have IIIF: validate each template response. Run Manifest budget remains bounded."}))

linz_collection = "https://digi.landesbibliothek.at/viewer/api/v2/collections/DC/karten/"
definitions.append(({"name": "Upper Austrian State Library", "institution_url": "https://www.landesbibliothek.at/",
    "source_page_url": "https://digi.landesbibliothek.at/viewer/",
    "discovery_endpoint": linz_collection, "discovery_type": "Collection", "endpoint_role": "presentation_collection"},
    {"type": "paginated_json_manifest_links", "api_url": linz_collection, "records_path": "items",
     "manifest_url_path": "id", "manifest_url_pattern": r"/manifest/$",
     "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 50, "max_pages": 1},
     "request_delay_seconds": 0.6,
     "coverage_note": "Native Presentation 3 maps Collection. Generic Collection traversal handles declared first/next links; this fallback inspects one response. Not all library holdings."}))

additions = [a for a, skill in definitions]
manual_path = code / "Module_1/config/manual_providers.json"
manual = json.loads(manual_path.read_text(encoding="utf-8"))
known = {p.get("institution_url") for p in manual["providers"]}
for addition in additions:
    if addition["institution_url"] not in known:
        manual["providers"].append(addition)
save(root / "additional_provider_source.json", {"providers": additions})
save(root / "module1_registration.json", {"registry_sources": [], "manual_sources": [str(root / "additional_provider_source.json")],
    "output_directory": str(root / "registration/module1/output"), "log_directory": str(root / "registration/module1/log")})
run_pipeline(root / "module1_registration.json", institution_selection=["all"])
records = read_jsonl(root / "registration/module1/output/providers.jsonl")
assert len(records) == 7
census_path = code / "Module_1/data/output/providers.jsonl"
if not (root / "before_provider_census.jsonl").exists():
    (root / "before_provider_census.jsonl").write_bytes(census_path.read_bytes())
known_ids = {p.provider_id for p in read_jsonl(census_path)}
with census_path.open("a", encoding="utf-8", newline="\n") as output:
    for p in records:
        if p.provider_id not in known_ids:
            output.write(json.dumps(p.to_dict(), ensure_ascii=False) + "\n")
write_csv(census_path.with_suffix(".csv"), read_jsonl(census_path))
save(manual_path, manual)
providers = [p.to_dict() for p in records]
save(root / "providers.json", providers)
(root / "selected_providers.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in providers), encoding="utf-8")
entries = []
for p in providers:
    addition, skill = next(d for d in definitions if d[0]["name"] == p["name"])
    skill["skill_id"] = p["provider_id"] + "-public-native-catalogue"
    entries.append({"provider_id": p["provider_id"], "provider_name": p["name"],
        "investigation_id": "2026-10-22-third-seven-provider-discovery",
        "investigation_document": "knowledge/institutions/2026-10-22_third_seven_provider_completion.md", "skills": [skill]})
save(root / "new_knowledge_entries.json", entries)
save(root / "new_endpoint_entries.json", [])
save(root / "candidate_discovery_knowledge.json", {"knowledge_base_version": "1.0", "providers": entries})
save(root / "candidate_provider_endpoints.json", {"providers": []})
for filename in ["module2_validation.json", "module3_validation.json", "module4_validation.json"]:
    value = (previous / filename).read_text(encoding="utf-8").replace(str(previous).replace("\\", "\\\\"), str(root).replace("\\", "\\\\"))
    save(root / filename, json.loads(value))
save(root / "sample_selection.json", {})
print("Prepared:", [(p["name"], p["provider_id"]) for p in providers])
