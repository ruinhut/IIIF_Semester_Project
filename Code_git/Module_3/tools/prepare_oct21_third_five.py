"""Register three additional institutions and prepare five bounded live runs."""
import json
from pathlib import Path
import sys

module = Path(__file__).resolve().parents[1]
code = module.parent
sys.path.insert(0, str(code / "Module_1"))
from iiif_provider_census.pipeline import run_pipeline
from iiif_provider_census.store import read_jsonl, write_csv

root = module / "evaluation/2026-10-21_third_five_provider_completion"
previous = module / "evaluation/2026-10-21_second_five_provider_completion"


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


manual_path = code / "Module_1/config/manual_providers.json"
manual = json.loads(manual_path.read_text(encoding="utf-8"))
additions = [
    {"name": "Victoria and Albert Museum", "institution_url": "https://www.vam.ac.uk/",
     "source_page_url": "https://developers.vam.ac.uk/guide/v2/images/iiif.html",
     "discovery_endpoint": "https://api.vam.ac.uk/v2/objects/search?q=manuscript&images_exist=true&page_size=6",
     "endpoint_role": "catalogue_api", "discovery_type": "JSON API"},
    {"name": "National Diet Library of Japan", "institution_url": "https://www.ndl.go.jp/",
     "source_page_url": "https://ndlsearch.ndl.go.jp/help/api/specifications",
     "discovery_endpoint": "https://ndlsearch.ndl.go.jp/api/opensearch?dpid=ndl-dl&title=%E6%BA%90%E6%B0%8F%E7%89%A9%E8%AA%9E&until=1900&cnt=6",
     "endpoint_role": "catalogue_api", "discovery_type": "OpenSearch RSS"},
    {"name": "Heidelberg University Library", "institution_url": "https://www.ub.uni-heidelberg.de/",
     "source_page_url": "https://www.ub.uni-heidelberg.de/helios/kataloge/datenschnittstellen.html",
     "discovery_endpoint": "https://digi.ub.uni-heidelberg.de/cgi-bin/digioai.cgi?verb=ListRecords&metadataPrefix=oai_dc&from=2026-10-20",
     "endpoint_role": "catalogue_api", "discovery_type": "OAI-PMH"},
]
existing_urls = {p.get("institution_url") for p in manual["providers"]}
for provider in additions:
    if provider["institution_url"] not in existing_urls:
        manual["providers"].append(provider)
save(manual_path, manual)
save(root / "additional_provider_source.json", {"providers": additions})
save(root / "module1_registration.json", {
    "registry_sources": [], "manual_sources": [str(root / "additional_provider_source.json")],
    "output_directory": str(root / "registration/module1/output"),
    "log_directory": str(root / "registration/module1/log")})
run_pipeline(root / "module1_registration.json", institution_selection=["all"])
new_records = read_jsonl(root / "registration/module1/output/providers.jsonl")
census_path = code / "Module_1/data/output/providers.jsonl"
backup = root / "before_provider_census.jsonl"
if not backup.exists():
    backup.write_bytes(census_path.read_bytes())
old_records = read_jsonl(census_path)
known = {p.provider_id for p in old_records}
with census_path.open("a", encoding="utf-8", newline="\n") as output:
    for provider in new_records:
        if provider.provider_id not in known:
            output.write(json.dumps(provider.to_dict(), ensure_ascii=False) + "\n")
write_csv(census_path.with_suffix(".csv"), read_jsonl(census_path))
census = [json.loads(s) for s in census_path.read_text(encoding="utf-8").splitlines() if s.strip()]
restored = {
    "provider-acb86cbbcb639914": ("https://www.bl.uk/collection/digitised-manuscripts-archives", "https://www.bl.uk/collection/digitised-manuscripts-archives"),
    "provider-3acece25cdf777e4": ("https://digitreaties.org/treaties/treaties/", "https://media.newmexicoculture.org/press_releases.php/1195/?action=detail&releaseID=1195"),
}
for provider in census:
    if provider["provider_id"] not in restored:
        continue
    url, evidence = restored[provider["provider_id"]]
    endpoint = {"url": url, "endpoint_role": "catalogue_listing", "discovery_type": "HTML",
                "label": "Public catalogue discovered 2026-10-21", "verification_status": "unverified",
                "source": {"source_type": "institution_documentation", "source_url": evidence,
                           "source_page_url": evidence, "observed_at": "2026-10-21T18:48:00Z"}}
    if not any(e["url"] == url for e in provider["endpoints"]):
        provider["endpoints"].append(endpoint)
        provider["endpoint_count"] = len(provider["endpoints"])
    if not any(p.get("provider_id") == provider["provider_id"] for p in manual["providers"]):
        manual["providers"].append({"provider_id": provider["provider_id"], "name": provider["name"],
            "institution_url": provider["institution_url"], "source_page_url": evidence, "endpoints": [endpoint]})
save(manual_path, manual)
census_path.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in census), encoding="utf-8")
write_csv(census_path.with_suffix(".csv"), read_jsonl(census_path))
ids = ["provider-acb86cbbcb639914", "provider-3acece25cdf777e4"] + [p.provider_id for p in new_records]
providers = [next(p for p in census if p["provider_id"] == identifier) for identifier in ids]
save(root / "providers.json", providers)
(root / "selected_providers.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in providers), encoding="utf-8")
new_by_name = {p.name: p.provider_id for p in new_records}
recipes = {
    ids[0]: {"skill_id": "british-library-public-highlight-manifest-links",
        "type": "paginated_html_identifiers_to_manifest_templates",
        "api_url": "https://www.bl.uk/collection/digitised-manuscripts-archives",
        "record_url_pattern": r"https://bl\.digirati\.io/(?:iiif|manifests)/ark:/81055/(?P<identifier>[^/?#]+)",
        "manifest_url_templates": ["https://bl.digirati.io/iiif/ark:/81055/{identifier}", "https://bl.digirati.io/manifests/ark:/81055/{identifier}"],
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 100, "max_pages": 1},
        "max_identifiers": 100,
        "coverage_note": "Nine public digitised highlights on the official BL page; not the whole BL catalogue. Viewer fragments contain explicitly declared native Manifest URLs."},
    ids[1]: {"skill_id": "ida-digitreaties-public-catalogue-manifests",
        "type": "paginated_html_identifiers_to_manifest_templates",
        "api_url": "https://digitreaties.org/treaties/treaties/",
        "record_url_pattern": r"^https://digitreaties\.org/treaties/treaty/(?P<identifier>\d+)/$",
        "manifest_url_templates": ["https://digitreaties.org/treaties/treaty/{identifier}/manifest/"],
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 1000, "max_pages": 1},
        "max_identifiers": 100,
        "coverage_note": "Public DigiTreaties project of the Indigenous Digital Archive, using National Archives images. This does not restore all content of the old boarding-school archive. Project continuity is documented in the Museum of Indian Arts and Culture press release."},
    new_by_name["Victoria and Albert Museum"]: {"skill_id": "vam-public-object-ids-to-iiif-manifests",
        "type": "paginated_json_identifiers_to_manifest_templates",
        "api_url": "https://api.vam.ac.uk/v2/objects/search",
        "query_parameters": {"q": "manuscript", "images_exist": "true"},
        "records_path": "records", "identifier_path": "systemNumber",
        "identifier_pattern": r"^(?P<identifier>O\d+)$",
        "manifest_url_templates": ["https://iiif.vam.ac.uk/collections/{identifier}/manifest.json"],
        "pagination": {"page_parameter": "page", "page_size_parameter": "page_size", "page_size": 6, "max_pages": 100},
        "max_identifiers": 600,
        "coverage_note": "Image-bearing manuscript search subset. The documented systemNumber template works even when _iiif_presentation_url is null; each candidate is validated."},
    new_by_name["National Diet Library of Japan"]: {"skill_id": "ndl-opensearch-rss-pids-to-iiif-manifests",
        "type": "paginated_xml_identifiers_to_manifest_templates",
        "api_url": "https://ndlsearch.ndl.go.jp/api/opensearch",
        "query_parameters": {"dpid": "ndl-dl", "title": "源氏物語", "until": "1900"},
        "xml_namespaces": {"rdfs": "http://www.w3.org/2000/01/rdf-schema#", "os": "http://a9.com/-/spec/opensearchrss/1.0/"},
        "xml_record_path": ".//item", "xml_identifier_path": "rdfs:seeAlso",
        "xml_identifier_attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
        "identifier_pattern": r"^https://dl\.ndl\.go\.jp/pid/(?P<identifier>\d+)$",
        "manifest_url_templates": ["https://dl.ndl.go.jp/api/iiif/{identifier}/manifest.json"],
        "pagination": {"page_parameter": "idx", "page_size_parameter": "cnt", "page_size": 6, "start_page": 1, "page_step": 6, "max_pages": 20, "xml_total_path": ".//os:totalResults"},
        "max_identifiers": 120,
        "coverage_note": "Historical Genji title query until 1900. Catalogue metadata availability does not guarantee public image delivery; rejected Manifest and image requests remain failures."},
    new_by_name["Heidelberg University Library"]: {"skill_id": "heidelberg-oai-explicit-manifest-links",
        "type": "paginated_xml_identifiers_to_manifest_templates",
        "api_url": "https://digi.ub.uni-heidelberg.de/cgi-bin/digioai.cgi",
        "query_parameters": {"verb": "ListRecords", "metadataPrefix": "oai_dc", "from": "2026-10-20"},
        "xml_namespaces": {"oai": "http://www.openarchives.org/OAI/2.0/", "dc": "http://purl.org/dc/elements/1.1/"},
        "xml_record_path": ".//oai:record", "xml_identifier_path": ".//dc:hasFormat",
        "identifier_pattern": r"^https://digi\.ub\.uni-heidelberg\.de/diglit/iiif/(?P<identifier>[^/]+)/manifest\.json$",
        "manifest_url_templates": ["https://digi.ub.uni-heidelberg.de/diglit/iiif/{identifier}/manifest.json"],
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 50, "max_pages": 100, "next_token_path": ".//oai:resumptionToken", "token_keep_parameters": ["verb"]},
        "max_identifiers": 5000,
        "coverage_note": "DWork records updated since 2026-10-20. Explicit dc:hasFormat links, with opaque OAI continuation tokens; public documented machine endpoint, without bypassing protected HTML pages."},
}
entries = []
for p in providers:
    recipe = recipes[p["provider_id"]]
    recipe["request_delay_seconds"] = 0.6
    entries.append({"provider_id": p["provider_id"], "provider_name": p["name"],
        "investigation_id": "2026-10-21-third-five-provider-discovery",
        "investigation_document": "knowledge/institutions/2026-10-21_third_five_provider_completion.md", "skills": [recipe]})
save(root / "new_knowledge_entries.json", entries)
save(root / "new_endpoint_entries.json", [])
save(root / "candidate_discovery_knowledge.json", {"knowledge_base_version": "1.0", "providers": entries})
save(root / "candidate_provider_endpoints.json", {"providers": []})
for name in ["module2_validation.json", "module3_validation.json", "module4_validation.json"]:
    text = (previous / name).read_text(encoding="utf-8").replace(str(previous).replace("\\", "\\\\"), str(root).replace("\\", "\\\\"))
    save(root / name, json.loads(text))
save(root / "sample_selection.json", {})
print("Prepared five sources:", ids)
