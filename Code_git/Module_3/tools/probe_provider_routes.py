"""Bounded, evidence-preserving public endpoint probes for provider investigations.

This tool does not mark providers resolved. It saves responses for inspection;
Module 3/4 must still validate the proposed recipe and its Manifest handoff.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen


class Links(HTMLParser):
    def __init__(self, base: str):
        super().__init__()
        self.base = base
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in ("href", "src", "data-manifest", "data-iiif-manifest"):
            if values.get(key):
                url = urljoin(self.base, values[key])
                if urlsplit(url).scheme in {"http", "https"}:
                    self.links.append({"tag": tag, "attribute": key, "url": url})


def probe(requests, output: Path, *, workers: int = 6, timeout: float = 12,
          max_bytes: int = 8 * 1024 * 1024):
    output.mkdir(parents=True, exist_ok=True)
    bodies = output / "responses"
    bodies.mkdir(exist_ok=True)
    locks = {urlsplit(row["url"]).netloc: threading.Lock() for row in requests}

    def fetch(row):
        result = {**row, "checked_at": datetime.now(timezone.utc).isoformat()}
        start = time.monotonic()
        url = row["url"]
        try:
            with locks[urlsplit(url).netloc]:
                time.sleep(0.2)
                req = Request(url, headers={
                    "User-Agent": "EPFL-DHLAB-IIIF-discovery-audit/1.0 (academic research)",
                    "Accept": "application/ld+json, application/json, text/html;q=0.9, */*;q=0.5",
                })
                try:
                    response = urlopen(req, timeout=timeout)
                except HTTPError as error:
                    response = error
                with response:
                    result.update(status=response.status, final_url=response.url,
                                  content_type=response.headers.get("Content-Type", ""))
                    body = response.read(max_bytes + 1)
            result["truncated"] = len(body) > max_bytes
            body = body[:max_bytes]
            result["bytes"] = len(body)
            # Hashing only names evidence files; it never rejects provider data.
            key = sha256(url.encode()).hexdigest()[:20]
            text = body.decode("utf-8-sig", "replace")
            try:
                value = json.loads(text)
                ext = ".json"
                result["json_parseable"] = True
                result["json_type"] = type(value).__name__
                if isinstance(value, dict):
                    result["keys"] = list(value)[:35]
                    result["declared_type"] = value.get("type", value.get("@type"))
                    result["context"] = value.get("@context")
                    for name in ("total", "totalItems", "numFound", "count", "totalResults", "resultCount"):
                        if name in value:
                            result[name] = value[name]
                    result["arrays"] = {k: len(v) for k, v in value.items() if isinstance(v, list)}
                elif isinstance(value, list):
                    result["array_length"] = len(value)
            except (ValueError, TypeError):
                ext = ".html" if "html" in result.get("content_type", "") else ".txt"
                result["json_parseable"] = False
                parser = Links(result["final_url"])
                parser.feed(text)
                result["links"] = parser.links[:500]
                result["platform_signals"] = [s for s in (
                    "Omeka", "CONTENTdm", "Blacklight", "Samvera", "DigiTool",
                    "Visual Library", "UniversalViewer", "Mirador", "Drupal",
                ) if s.casefold() in text.casefold()]
                result["iiif_lines"] = [line[:1800] for line in text.splitlines()
                                        if re.search(r"iiif|manifest|/api/|/sru", line, re.I)][:30]
            path = bodies / (key + ext)
            path.write_bytes(body)
            result["response_file"] = str(path.resolve())
        except Exception as error:
            result.update(error_type=type(error).__name__, error=str(error))
        result["elapsed_seconds"] = round(time.monotonic() - start, 3)
        return result

    rows = []
    with (output / "checks.jsonl").open("a", encoding="utf-8") as log:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(fetch, row) for row in requests]
            for future in as_completed(futures):
                row = future.result()
                rows.append(row)
                log.write(json.dumps(row, ensure_ascii=False) + "\n")
                log.flush()
                print(json.dumps({k: row.get(k) for k in (
                    "provider_name", "purpose", "url", "status", "declared_type",
                    "error_type", "bytes", "elapsed_seconds",
                )}, ensure_ascii=True), flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("--max-bytes", type=int, default=8 * 1024 * 1024)
    args = parser.parse_args()
    requests = json.loads(args.requests.read_text(encoding="utf-8-sig"))
    probe(requests, args.output, workers=args.workers, timeout=args.timeout,
          max_bytes=args.max_bytes)


if __name__ == "__main__":
    main()
