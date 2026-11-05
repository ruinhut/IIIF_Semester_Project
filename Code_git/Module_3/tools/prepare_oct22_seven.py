"""Register seven distinct libraries and isolate their bounded validation run."""
import json
from pathlib import Path
import sys

module = Path(__file__).resolve().parents[1]
code = module.parent
sys.path.insert(0, str(code / "Module_1"))
from iiif_provider_census.pipeline import run_pipeline
from iiif_provider_census.store import read_jsonl, write_csv

root = module / "evaluation/2026-10-22_seven_provider_completion"
previous = module / "evaluation/2026-10-22_five_provider_completion"
root.mkdir(exist_ok=True)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


definitions = [
    ("Wienbibliothek im Rathaus", "https://www.wienbibliothek.at/",
     "https://www.digital.wienbibliothek.at/i3f/v21/collection/2612535",
     "https://www.digital.wienbibliothek.at/", "Culture and literature collection", None),
    ("Lippische Landesbibliothek Detmold", "https://www.llb-detmold.de/",
     "https://digitale-sammlungen.llb-detmold.de/i3f/v21/collection/all",
     "https://digitale-sammlungen.llb-detmold.de/", "All-title catalogue sample", None),
    ("Cologne Archdiocesan and Cathedral Library", "https://www.dombibliothek-koeln.de/",
     "https://digital.dombibliothek-koeln.de/i3f/v21/collection/381367",
     "https://digital.dombibliothek-koeln.de/", "Historical holdings", None),
    ("Rheinland-Pfalz State Library Centre", "https://lbz.rlp.de/",
     "https://www.dilibri.de/rlb/i3f/v21/collection/all",
     "https://www.dilibri.de/rlb", "Institution-scoped public Dilibri catalogue", "rlb"),
    ("Trier University Library", "https://www.uni-trier.de/bibliothek/",
     "https://www.dilibri.de/ubtr/i3f/v21/collection/all",
     "https://www.dilibri.de/ubtr", "Institution-scoped public Dilibri catalogue", "ubtr"),
    ("Trier City Library", "https://www.stadtbibliothek-weberbach.de/",
     "https://www.dilibri.de/stbtr/i3f/v21/collection/all",
     "https://www.dilibri.de/stbtr", "Institution-scoped public Dilibri catalogue", "stbtr"),
    ("Mainz City Library", "https://www.mainz.de/microsite/bibliotheken/",
     "https://www.dilibri.de/stbmz/i3f/v21/collection/all",
     "https://www.dilibri.de/stbmz", "Institution-scoped public Dilibri catalogue", "stbmz"),
]
additions = [{"name": name, "institution_url": institution, "discovery_endpoint": endpoint,
    "discovery_type": "Collection", "endpoint_role": "presentation_collection", "source_page_url": evidence}
    for name, institution, endpoint, evidence, subset, branch in definitions]
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
records = read_jsonl(root / "registration/module1/output/providers.jsonl")
census_path = code / "Module_1/data/output/providers.jsonl"
backup = root / "before_provider_census.jsonl"
if not backup.exists():
    backup.write_bytes(census_path.read_bytes())
existing = read_jsonl(census_path)
known = {p.provider_id for p in existing}
with census_path.open("a", encoding="utf-8", newline="\n") as handle:
    for record in records:
        if record.provider_id not in known:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
write_csv(census_path.with_suffix(".csv"), read_jsonl(census_path))
save(manual_path, manual)
providers = [p.to_dict() for p in records]
save(root / "providers.json", providers)
(root / "selected_providers.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in providers), encoding="utf-8")
entries = []
for provider in providers:
    name, institution, endpoint_url, evidence, subset, branch = next(d for d in definitions if d[0] == provider["name"])
    recipe = {"skill_id": provider["provider_id"] + "-reviewed-native-collection",
        "type": "paginated_json_manifest_links", "api_url": endpoint_url,
        "records_path": "members", "manifest_url_path": "@id", "manifest_url_pattern": r"/manifest$",
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 20, "max_pages": 1},
        "request_delay_seconds": 0.6,
        "coverage_note": subset + ". Supplementary fallback reads first-page explicit Manifest links only. Main generic traversal follows child Collections and next links within the run budget; it is not a complete institution harvest."}
    if branch:
        recipe["collection_url_rewrites"] = [{"from_prefix": "https://www.dilibri.de/i3f/v21/collection/",
            "to_prefix": "https://www.dilibri.de/" + branch + "/i3f/v21/collection/"}]
        recipe["coverage_note"] += " Native next and child Collection URLs omit this institution's virtual path. The reviewed same-origin Collection-only mapping preserves it; Manifest URLs remain as declared. Different Dilibri libraries are separate holders; the portal itself is not an eighth institution. Public HTML listing pages may return a browser challenge; no challenge is bypassed."
    entries.append({"provider_id": provider["provider_id"], "provider_name": provider["name"],
        "investigation_id": "2026-10-22-seven-provider-discovery",
        "investigation_document": "knowledge/institutions/2026-10-22_seven_provider_completion.md", "skills": [recipe]})
save(root / "new_knowledge_entries.json", entries)
save(root / "new_endpoint_entries.json", [])
save(root / "candidate_discovery_knowledge.json", {"knowledge_base_version": "1.0", "providers": entries})
save(root / "candidate_provider_endpoints.json", {"providers": []})
for filename in ["module2_validation.json", "module3_validation.json", "module4_validation.json"]:
    text = (previous / filename).read_text(encoding="utf-8").replace(str(previous).replace("\\", "\\\\"), str(root).replace("\\", "\\\\"))
    save(root / filename, json.loads(text))
save(root / "sample_selection.json", {})
print("Prepared:", [(p["name"], p["provider_id"]) for p in providers])
