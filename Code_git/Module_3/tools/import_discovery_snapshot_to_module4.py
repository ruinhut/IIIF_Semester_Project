"""Import explicitly selected HTTP evidence into a Module 4 raw cache.

This avoids downloading the same fresh response a second time. It does not
manufacture validation results: Module 4 still parses, validates and inventories
every imported response. The source trace and original retrieval time remain
attached to the cache metadata. Unknown URLs are left for normal HTTP fetching.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--trace", type=Path, action="append", required=True)
    parser.add_argument("--raw-directory", type=Path, required=True)
    args = parser.parse_args()
    responses = {}
    for trace in args.trace:
        for line in trace.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("event") in {"response_received", "response_snapshot_reused"} and row.get("status_code") == 200:
                responses[row["url"]] = (row, str(trace.resolve()))
    args.raw_directory.mkdir(parents=True, exist_ok=True)
    imported, missing = 0, []
    for line in args.input.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        evidence = responses.get(row["manifest_url"])
        if not evidence or not Path(evidence[0]["body_file"]).exists():
            missing.append(row["manifest_url"])
            continue
        response, trace = evidence
        source = Path(response["body_file"])
        target = args.raw_directory / (row["manifest_id"] + ".json")
        body = source.read_bytes()
        # Import the original bytes, including any publisher structural defects.
        shutil.copyfile(source, target)
        metadata = {
            "fetch_source": "imported_discovery_http_snapshot",
            "requested_url": row["manifest_url"], "final_url": response["final_url"],
            "status_code": response["status_code"], "content_type": response["content_type"],
            "fetched_at": response.get("original_fetched_at", response["at"]),
            "response_time_ms": round(response.get("elapsed_seconds", 0) * 1000),
            "attempt_count": 1, "sha256": sha256(body).hexdigest(), "response_bytes": len(body),
            "import_provenance": {"trace": trace, "body_file": str(source.resolve()),
                                  "request_id": response["request_id"],
                                  "note": "Shared HTTP evidence; not an independent second network request."},
        }
        target.with_suffix(".meta.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        imported += 1
    summary = {"imported_raw_responses": imported, "not_in_snapshot": len(missing),
               "missing_urls": missing, "note": "No validation decisions were made by the cache import."}
    (args.raw_directory.parent / "cache_import_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "missing_urls"}))


if __name__ == "__main__":
    main()
