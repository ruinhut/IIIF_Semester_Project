"""Snapshot a reviewed public item API, with durable progress and a time bound.

This utility only reads public catalogue records. It reports transcription
availability separately from image alignment; a nonempty field is not proof
that its text belongs to an individual page or is corrected ground truth.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from iiif_resource_discovery.fetch import FetchError, HttpFetcher


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--url-template", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--deadline-utc", required=True)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--priority-types", default="Letter,Document,Diary,Notebook,Book,Booklets,Periodical,Newspaper,Pamphlet,Article,Leaflet,Clipping,Ephemera,Identification,Postcard",
                        help="Read text-bearing item types first; remaining types are still visited")
    args = parser.parse_args()
    deadline = datetime.fromisoformat(args.deadline_utc.replace("Z", "+00:00"))
    if "{identifier}" not in args.url_template:
        raise ValueError("URL template must contain {identifier}")
    cache = args.output / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in args.catalogue.read_text(encoding="utf-8").splitlines()]
    # Prioritize text-bearing material for OCR collaborators, then cover the rest.
    priority = {value.strip(): i for i, value in enumerate(args.priority_types.split(","))}
    rows.sort(key=lambda row: priority.get(row["record"]["generalInfo"].get("itemType"), len(priority)))
    fetcher = HttpFetcher(timeout_seconds=20, retries=1, max_response_bytes=16 * 1024 * 1024)
    counts, languages, types = Counter(), Counter(), Counter()
    events = args.output / "requests.jsonl"

    def checkpoint(stop_reason=None):
        result = {"at": datetime.now(timezone.utc).isoformat(), "catalogue_ids": len(rows),
                  "counts": dict(counts), "reference_languages": dict(languages),
                  "reference_item_types": dict(types), "stop_reason": stop_reason,
                  "note": "Original-transcription availability only; per-image alignment requires Module 6."}
        checkpoint_path = args.output / "summary.json.part"
        checkpoint_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        checkpoint_path.replace(args.output / "summary.json")
        print(json.dumps({"processed": counts["processed"], "original_transcript": counts["original_transcript"],
                          "failed": counts["failed"], "stop": stop_reason}), flush=True)

    for row in rows:
        if datetime.now(timezone.utc) >= deadline:
            checkpoint("deadline_checkpoint")
            return
        identifier = row["identifier"]
        url = args.url_template.replace("{identifier}", quote(identifier, safe=""))
        path = cache / (sha256(url.encode()).hexdigest()[:24] + ".json")
        event = {"at": datetime.now(timezone.utc).isoformat(), "identifier": identifier,
                 "url": url, "raw_json_path": str(path.resolve())}
        try:
            value = None
            if path.exists():
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                    event["fetch_source"] = "cache"
                except (OSError, ValueError) as exc:
                    event["rejected_cache_reason"] = str(exc)
            if value is None:
                time.sleep(max(0.0, args.delay))
                response = fetcher.fetch(url, accept="application/json")
                value = response.json()
                temporary = path.with_suffix(".json.part")
                temporary.write_bytes(response.body)
                temporary.replace(path)
                event.update(fetch_source="network", status_code=response.status_code)
            record = value.get("data")
            if not isinstance(record, dict):
                raise ValueError("Item response did not contain a data object")
            original = record.get("originalTranscript")
            pages = record.get("pages", [])
            event.update(status="record_received", has_original_transcript=isinstance(original, str) and bool(original.strip()),
                         catalogue_page_count=len(pages) if isinstance(pages, list) else None,
                         original_language=record.get("originalTranscriptLanguages"))
            counts["received"] += 1
            if event["has_original_transcript"]:
                counts["original_transcript"] += 1
                if event["catalogue_page_count"] == 1:
                    counts["single_page_original_transcript"] += 1
                languages[str(event["original_language"] or "unknown")] += 1
                types[row["record"]["generalInfo"].get("itemType", "unknown")] += 1
        except (FetchError, ValueError, OSError) as exc:
            event.update(status="failed", error_type=getattr(exc, "error_type", type(exc).__name__), message=str(exc))
            counts["failed"] += 1
            if getattr(exc, "status_code", None) in {403, 429}:
                event["status_code"] = exc.status_code
                with events.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event, ensure_ascii=False) + "\n")
                counts["processed"] += 1
                checkpoint("access_or_rate_limit_requires_recheck")
                return
        counts["processed"] += 1
        with events.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        if counts["processed"] % 100 == 0:
            checkpoint()
    checkpoint("all_catalogue_ids_visited")


if __name__ == "__main__":
    main()
