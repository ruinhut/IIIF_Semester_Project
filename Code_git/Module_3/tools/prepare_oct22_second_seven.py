"""Prepare seven new public sources for the 93-entry validation milestone."""
import json
from pathlib import Path
import sys

module = Path(__file__).resolve().parents[1]
code = module.parent
sys.path.insert(0, str(code / "Module_1"))
from iiif_provider_census.pipeline import run_pipeline
from iiif_provider_census.store import read_jsonl, write_csv

root = module / "evaluation/2026-10-22_second_seven_provider_completion"
previous = module / "evaluation/2026-10-22_seven_provider_completion"
root.mkdir(exist_ok=True)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# All IDs below came from actual native top Collections or the official partner
# list. A shared portal is not registered as an additional institution.
definitions = [
    ("Oldenburg State Library", "https://www.lb-oldenburg.de/",
     "https://digital.lb-oldenburg.de/i3f/v21/collection/785124",
     "https://digital.lb-oldenburg.de/", "Manuscripts Collection", "members", None),
    ("University of Graz Library", "https://ub.uni-graz.at/",
     "https://unipub.uni-graz.at/obvugrscript/i3f/v21/collection/all",
     "https://unipub.uni-graz.at/obvugrscript", "Digi SCRIPT manuscript portal", "members",
     {"from_prefix": "https://unipub.uni-graz.at/i3f/v21/collection/",
      "to_prefix": "https://unipub.uni-graz.at/obvugrscript/i3f/v21/collection/"}),
    ("Leipzig University Library", "https://www.ub.uni-leipzig.de/",
     "https://iiif.ub.uni-leipzig.de/static/collections/GriechischeHandschriften/collection.json",
     "https://iiif.ub.uni-leipzig.de/static/collections/toplevel.json", "Greek manuscripts", "manifests", None),
    ("Potsdam University Library - Digitales Brandenburg", "https://www.ub.uni-potsdam.de/",
     "https://digital.ub.uni-potsdam.de/i3f/v21/collection/all",
     "https://digital.ub.uni-potsdam.de/", "Public catalogue, including cooperating holders", "members", None),
    ("Trier Seminary Library", "https://www.bps-trier.de/",
     "https://www.dilibri.de/pstr/i3f/v21/collection/all",
     "https://www.dilibri.de/pstr", "Seminary library's Dilibri branch", "members",
     {"from_prefix": "https://www.dilibri.de/i3f/v21/collection/",
      "to_prefix": "https://www.dilibri.de/pstr/i3f/v21/collection/"}),
    ("Koblenz City Library", "https://www.koblenz-stadtbibliothek.de/",
     "https://www.dilibri.de/stbkodfg/i3f/v21/collection/all",
     "https://www.dilibri.de/stbkodfg", "Koblenz city library DFG branch", "members",
     {"from_prefix": "https://www.dilibri.de/i3f/v21/collection/",
      "to_prefix": "https://www.dilibri.de/stbkodfg/i3f/v21/collection/"}),
    ("Worms City Library", "https://www.worms.de/neu-de/bildung-bieten/stadtbibliothek/",
     "https://www.dilibri.de/stbwo/i3f/v21/collection/all",
     "https://www.dilibri.de/stbwo", "Worms city library Dilibri branch", "members",
     {"from_prefix": "https://www.dilibri.de/i3f/v21/collection/",
      "to_prefix": "https://www.dilibri.de/stbwo/i3f/v21/collection/"}),
]
additions = [{"name": name, "institution_url": institution, "discovery_endpoint": endpoint,
    "discovery_type": "Collection", "endpoint_role": "presentation_collection", "source_page_url": evidence}
    for name, institution, endpoint, evidence, subset, path, rewrite in definitions]
manual_path = code / "Module_1/config/manual_providers.json"
manual = json.loads(manual_path.read_text(encoding="utf-8"))
known_urls = {p.get("institution_url") for p in manual["providers"]}
for addition in additions:
    if addition["institution_url"] not in known_urls:
        manual["providers"].append(addition)
save(root / "additional_provider_source.json", {"providers": additions})
save(root / "module1_registration.json", {"registry_sources": [],
    "manual_sources": [str(root / "additional_provider_source.json")],
    "output_directory": str(root / "registration/module1/output"),
    "log_directory": str(root / "registration/module1/log")})
run_pipeline(root / "module1_registration.json", institution_selection=["all"])
records = read_jsonl(root / "registration/module1/output/providers.jsonl")
census_path = code / "Module_1/data/output/providers.jsonl"
if not (root / "before_provider_census.jsonl").exists():
    (root / "before_provider_census.jsonl").write_bytes(census_path.read_bytes())
known_ids = {p.provider_id for p in read_jsonl(census_path)}
with census_path.open("a", encoding="utf-8", newline="\n") as handle:
    for record in records:
        if record.provider_id not in known_ids:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
write_csv(census_path.with_suffix(".csv"), read_jsonl(census_path))
save(manual_path, manual)
providers = [p.to_dict() for p in records]
save(root / "providers.json", providers)
(root / "selected_providers.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in providers), encoding="utf-8")
entries = []
for provider in providers:
    name, institution, endpoint, evidence, subset, path, rewrite = next(d for d in definitions if d[0] == provider["name"])
    skill = {"skill_id": provider["provider_id"] + "-native-reviewed-collection",
        "type": "paginated_json_manifest_links", "api_url": endpoint,
        "records_path": path, "manifest_url_path": "@id", "manifest_url_pattern": r"/manifest(?:\.json)?$",
        "pagination": {"page_parameter": "", "page_size_parameter": "", "page_size": 20, "max_pages": 1},
        "request_delay_seconds": 0.6,
        "coverage_note": subset + ". First-page fallback only. Main generic Collection walker handles nested Collections and next links subject to a bounded run budget. Sample success is not a complete institution harvest."}
    if rewrite:
        skill["collection_url_rewrites"] = [rewrite]
        skill["coverage_note"] += " Preserve the virtual collection prefix on same-origin Collection requests only; do not change declared Manifest or image URLs."
    entries.append({"provider_id": provider["provider_id"], "provider_name": provider["name"],
        "investigation_id": "2026-10-22-second-seven-provider-discovery",
        "investigation_document": "knowledge/institutions/2026-10-22_second_seven_provider_completion.md", "skills": [skill]})
save(root / "new_knowledge_entries.json", entries)
save(root / "new_endpoint_entries.json", [])
save(root / "candidate_discovery_knowledge.json", {"knowledge_base_version": "1.0", "providers": entries})
save(root / "candidate_provider_endpoints.json", {"providers": []})
for filename in ["module2_validation.json", "module3_validation.json", "module4_validation.json"]:
    value = (previous / filename).read_text(encoding="utf-8").replace(str(previous).replace("\\", "\\\\"), str(root).replace("\\", "\\\\"))
    save(root / filename, json.loads(value))
save(root / "sample_selection.json", {})
print("Prepared:", [(p["name"], p["provider_id"]) for p in providers])
