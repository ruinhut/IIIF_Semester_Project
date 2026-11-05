"""Independently validate saved XML-feed and native Collection recipes.

Keep request bodies and inspect actual OAI continuation. A capped RSS feed is
never reported as a completed catalogue. Extra audit Manifests are not added to
the end-to-end resource counts.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlencode, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

module = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(module))
from iiif_resource_discovery.fetch import HttpFetcher
from iiif_resource_discovery.skills import execute_skill


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.evaluation_root.resolve()
    evidence = root / "recipe_checks"
    evidence.mkdir(exist_ok=True)

    def save(filename, value):
        (root / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    class EvidenceFetcher(HttpFetcher):
        def __init__(self):
            super().__init__(timeout_seconds=35, retries=0, max_response_bytes=64 * 1024 * 1024)
            self.responses = []

        def fetch(self, url, **options):
            time.sleep(0.6)
            document = super().fetch(url, **options)
            body = evidence / (sha256(url.encode()).hexdigest()[:20] + ".body")
            body.write_bytes(document.body)
            self.responses.append(document)
            with (evidence / "requests.jsonl").open("a", encoding="utf-8") as output:
                output.write(json.dumps({"url": url, "final_url": document.final_url,
                    "status_code": document.status_code, "body_file": str(body), "bytes": len(document.body)}) + "\n")
            return document

    entries = json.loads((root / "new_knowledge_entries.json").read_text(encoding="utf-8"))
    fallbacks, pages = [], []
    for entry in entries:
        skill = entry["skills"][0]
        fetcher = EvidenceFetcher()
        result = execute_skill(skill, fetcher, investigation_id=entry["investigation_id"], max_manifests=2)
        fallbacks.append({"provider_name": entry["provider_name"], "audit": result.audit,
            "issues": [str(i) for i in result.issues],
            "validated_manifest_urls": [m.manifest_url for m in result.manifests],
            "added_to_downstream_count": False})
        save("fallback_recipe_validation.json", fallbacks)
        assert len(result.manifests) == 2, (entry["provider_name"], result.audit, result.issues)
        document = fetcher.responses[0]
        check = {"provider_name": entry["provider_name"], "catalogue_url": document.final_url}
        if skill["type"].startswith("paginated_xml"):
            xml = ET.fromstring(document.body)
            ns = skill.get("xml_namespaces", {})
            records = xml.findall(skill["xml_record_path"], ns)
            check["catalogue_record_count"] = len(records)
            token_path = skill["pagination"].get("next_token_path")
            if token_path:
                token = xml.find(token_path, ns)
                check["declared_continuation_token_present"] = token is not None and bool(token.text)
                if token is not None and token.text:
                    p = urlsplit(skill["api_url"])
                    parameters = {k: v for k, v in skill["query_parameters"].items()
                                  if k in skill["pagination"].get("token_keep_parameters", ["verb"])}
                    parameters["resumptionToken"] = token.text.strip()
                    following = fetcher.fetch(urlunsplit((p.scheme, p.netloc, p.path, urlencode(parameters), "")))
                    xml2 = ET.fromstring(following.body)
                    records2 = xml2.findall(skill["xml_record_path"], ns)
                    path = skill["xml_identifier_path"]
                    first_ids = {r.findtext(path, namespaces=ns) for r in records}
                    second_ids = {r.findtext(path, namespaces=ns) for r in records2}
                    assert records2 and first_ids != second_ids
                    check.update(next_page_url=following.final_url, next_page_record_count=len(records2), distinct_pages=True)
            else:
                # XML executor has a conservative size heuristic; it is not an
                # actual server-declared next link and must not be called one.
                check.update(declared_next=None, pagination_verified=False,
                    coverage="Capped public RSS subset only; no catalogue completeness claim.")
        else:
            value = document.json()
            check.update(catalogue_record_count=len(value[skill["records_path"]]),
                         declared_next=value.get("next"), coverage=skill["coverage_note"])
        pages.append(check)
        save("pagination_validation.json", pages)
        print(json.dumps({"provider": entry["provider_name"], "independent_manifest_checks": 2}), flush=True)

    ownership, seen = [], set()
    manifests = root / "validation/module4/output/validated_manifests.jsonl"
    for line in manifests.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        name = item["providers"][0]["provider_name"]
        assert item["manifest_url"] not in seen, "The same Manifest was counted twice across institutions"
        seen.add(item["manifest_url"])
        raw = json.loads((root / item["raw_manifest"]["raw_manifest_path"]).read_bytes())
        holders = [m for m in raw.get("metadata", [])
                   if "Owner of" in json.dumps(m.get("label"), ensure_ascii=False)]
        if name in {"Kiel University Library", "Kiel City Archives"}:
            required = "Universitätsbibliothek Kiel" if name == "Kiel University Library" else "Stadtarchiv Kiel"
            assert holders and all(m["value"] == required for m in holders), (name, holders)
        ownership.append({"provider_name": name, "manifest_url": item["manifest_url"],
            "source_declared_holder_fields": holders, "attribution": raw.get("attribution"),
            "shared_portal_holder_verified": bool(holders) if name.startswith("Kiel ") else None})
    save("institution_ownership_verification.json", {"records_checked": len(ownership),
        "manifest_urls_overlap_between_sources": False, "records": ownership})
    print(json.dumps({"recipes_verified": len(fallbacks), "provenance_records_checked": len(ownership)}))


if __name__ == "__main__":
    main()
