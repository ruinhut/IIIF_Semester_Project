"""Enumerate reviewed catalogue recipes with page snapshots and resumable evidence."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from iiif_resource_discovery.fetch import HttpFetcher
from iiif_resource_discovery.skills import catalogue_request, _path_value, _path_values


def main():
    """Save every source page before advancing; catalogue IDs are not validated Manifests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true", help="Reuse saved pages from this explicit catalogue snapshot")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pages_dir = args.output / "pages"
    pages_dir.mkdir(exist_ok=True)
    recipes = json.loads(args.recipes.read_text(encoding="utf-8"))
    fetcher = HttpFetcher(timeout_seconds=25, retries=2, backoff_seconds=1, max_response_bytes=32 * 1024 * 1024)
    records, reports = {}, []
    for recipe in recipes:
        pagination = recipe["pagination"]
        report = {"skill_id": recipe["skill_id"], "collection_name": recipe.get("collection_name"),
                  "declared_count": recipe.get("source_declared_total"), "identifiers": 0,
                  "pages": 0, "stop_reason": None, "errors": []}
        seen_pages, seen_ids = set(), set()
        for page in range(pagination["max_pages"]):
            number = pagination.get("start_page", 0) + page * pagination.get("page_step", 1)
            url, options = catalogue_request(recipe, number, pagination["page_size"])
            identity = json.dumps({"url": url, **options}, sort_keys=True)
            key = sha256(identity.encode()).hexdigest()[:24]
            body_file = pages_dir / (key + ".json")
            event = {"at": datetime.now(timezone.utc).isoformat(), "recipe_id": recipe["skill_id"],
                     "page_number": number, "url": url, "request_options": options,
                     "response_file": str(body_file.resolve())}
            try:
                if args.resume and body_file.exists():
                    value = json.loads(body_file.read_text(encoding="utf-8"))
                    event["source"] = "snapshot_resume"
                else:
                    time.sleep(recipe.get("request_delay_seconds", 0.2))
                    doc = fetcher.fetch(url, accept="application/json", **options)
                    value = doc.json()
                    body_file.write_bytes(doc.body)
                    event.update(source="network", status_code=doc.status_code, bytes=len(doc.body))
                entries = _path_value(value, recipe.get("records_path", "$"))
                if not isinstance(entries, list):
                    raise ValueError("Configured records_path did not return a list")
                signature = sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
                if entries and signature in seen_pages:
                    report["stop_reason"] = "repeated_page"
                    raise ValueError("Source repeated an already enumerated page")
                seen_pages.add(signature)
                report["pages"] += 1
                event["records"] = len(entries)
                total_path = pagination.get("total_path")
                total = _path_value(value, total_path) if total_path else None
                if isinstance(total, int):
                    report["response_declared_total"] = total
                for entry in entries:
                    for identifier in _path_values(entry, recipe["identifier_path"]):
                        if not isinstance(identifier, (str, int)) or isinstance(identifier, bool):
                            continue
                        identifier = str(identifier)
                        seen_ids.add(identifier)
                        source = {"recipe_id": recipe["skill_id"], "page_number": number, "response_file": str(body_file.resolve())}
                        if identifier not in records:
                            records[identifier] = {"identifier": identifier, "record": entry, "sources": [source]}
                        else:
                            records[identifier]["sources"].append(source)
                if len(entries) < pagination["page_size"]:
                    if isinstance(total, int) and number + len(entries) < total:
                        raise ValueError("Short page before declared total; page-size clamping or pagination needs investigation")
                    report["stop_reason"] = "terminal_short_or_empty_page"
            except Exception as exc:
                event.update(error_type=getattr(exc, "error_type", type(exc).__name__), message=str(exc))
                report["errors"].append(event)
                report["stop_reason"] = report["stop_reason"] or "request_or_shape_failure"
            with (args.output / "requests.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
            if report["stop_reason"]:
                break
        report["identifiers"] = len(seen_ids)
        report["stop_reason"] = report["stop_reason"] or "configured_page_budget"
        reports.append(report)
        (args.output / "collection_checkpoints.json").write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"collection": report["collection_name"], "ids": report["identifiers"],
                          "unique_total": len(records), "stop": report["stop_reason"]}, ensure_ascii=True), flush=True)
    with (args.output / "catalogue_records.jsonl").open("w", encoding="utf-8") as handle:
        for row in records.values():
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    result = {"unique_catalogue_identifiers": len(records), "collections": len(reports),
              "finished_collections": sum(p["stop_reason"] == "terminal_short_or_empty_page" for p in reports),
              "failed_collections": sum(bool(p["errors"]) for p in reports),
              "note": "Enumerated catalogue IDs only; these are not yet validated Manifest or image counts."}
    (args.output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
