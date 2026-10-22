"""Run the real Module 3 pipeline with request traces and provider checkpoints."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from iiif_resource_discovery import pipeline
from iiif_resource_discovery.fetch import FetchedDocument


def main():
    """Add evaluation-only observability without changing downstream contracts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--resume", action="store_true", help="Reuse successful request snapshots from this output directory")
    parser.add_argument("--resume-from", type=Path, action="append", default=[],
                        help="Reuse successful responses from an explicitly chosen request trace")
    parser.add_argument("--replay-without-delay", action="store_true",
                        help="Skip catalogue pacing for local snapshots; real HTTP still observes --network-delay")
    parser.add_argument("--network-delay", type=float, default=0.2)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if args.timeout:
        config["network"]["timeout_seconds"] = args.timeout
        config["network"]["retries"] = 0
        # Keep the exact effective parameters beside the original configuration.
        config_path = config_path.with_name(config_path.stem + "_effective.json")
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    configured_output = Path(config["output_directory"])
    output = (configured_output if configured_output.is_absolute() else config_path.parent / configured_output).resolve().parent
    output.mkdir(parents=True, exist_ok=True)
    bodies = output / "request_bodies"
    bodies.mkdir(exist_ok=True)
    events = output / "requests.jsonl"
    original_fetcher = pipeline.HttpFetcher
    original_discover = pipeline.ResourceDiscoverer.discover
    response_cache = {}
    cache_enabled = args.resume or bool(args.resume_from)
    trace_sources = list(args.resume_from)
    if args.resume:
        trace_sources.append(events)
    for trace in trace_sources:
        if not trace.exists():
            continue
        for line in trace.read_text(encoding="utf-8").splitlines():
            try:
                saved = json.loads(line)
            except json.JSONDecodeError:
                continue  # A truncated last checkpoint is retried, never treated as success.
            required = {"final_url", "status_code", "content_type", "body_file", "request_id"}
            if saved.get("event") in {"response_received", "response_snapshot_reused"} and required.issubset(saved):
                response_cache[saved["request_id"]] = saved

    def event(value):
        value["at"] = datetime.now(timezone.utc).isoformat()
        with events.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False) + "\n")

    class AuditedFetcher(original_fetcher):
        def __init__(self, *positional, **options):
            super().__init__(*positional, **options)
            self.network_sleeper = self.sleeper
            self.last_network_end = 0.0
            if args.replay_without_delay:
                self.sleeper = lambda _: None

        def fetch(self, url, **kwargs):
            start = time.monotonic()
            method = kwargs.get("method", "GET")
            request_identity = {"url": url, "method": method, "json_body": kwargs.get("json_body")}
            if kwargs.get("headers"):
                request_identity["headers"] = kwargs["headers"]
            identity = json.dumps(request_identity, sort_keys=True)
            request_id = sha256(identity.encode()).hexdigest()[:20]
            event({"event": "request_started", "url": url, "method": method,
                   "json_body": kwargs.get("json_body"), "request_id": request_id})
            try:
                saved = response_cache.get(request_id)
                if cache_enabled and saved and Path(saved["body_file"]).exists():
                    try:
                        document = FetchedDocument(url, saved["final_url"], saved["status_code"],
                                                   saved["content_type"], Path(saved["body_file"]).read_bytes())
                        # HTML snapshots are valid too. Corrupt JSON is fetched again.
                        if "json" in str(document.content_type).lower():
                            document.json()
                        reused = dict(saved)
                        reused.update(event="response_snapshot_reused", url=url, request_id=request_id,
                                      original_fetched_at=saved.get("original_fetched_at", saved.get("at")))
                        event(reused)
                        return document
                    except (OSError, ValueError):
                        event({"event": "response_snapshot_rejected", "url": url,
                               "request_id": request_id, "reason": "unreadable_or_invalid_json"})
                sleeper = self.sleeper
                if args.replay_without_delay:
                    time.sleep(max(0.0, args.network_delay - (time.monotonic() - self.last_network_end)))
                    self.sleeper = self.network_sleeper  # Preserve HTTP retry backoff.
                try:
                    document = super().fetch(url, **kwargs)
                finally:
                    self.last_network_end = time.monotonic()
                    self.sleeper = sleeper
                filename = request_id + ".body"
                (bodies / filename).write_bytes(document.body)
                saved_response = {"event": "response_received", "url": url, "final_url": document.final_url,
                       "request_id": request_id, "method": method,
                       "status_code": document.status_code, "content_type": document.content_type,
                       "bytes": len(document.body), "body_file": str(bodies / filename),
                       "elapsed_seconds": round(time.monotonic() - start, 3)}
                event(saved_response)
                response_cache[request_id] = saved_response
                return document
            except Exception as exc:
                event({"event": "request_failed", "url": url, "error_type": getattr(exc, "error_type", type(exc).__name__),
                       "request_id": request_id, "method": method,
                       "message": str(exc), "elapsed_seconds": round(time.monotonic() - start, 3)})
                raise

    def checkpoint(discoverer, provider, **kwargs):
        print(json.dumps({"provider_started": provider.name}, ensure_ascii=True), flush=True)
        event({"event": "provider_started", "provider_id": provider.provider_id, "provider_name": provider.name})
        result = original_discover(discoverer, provider, **kwargs)
        (output / (provider.provider_id + ".json")).write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        unique_count = len({finding.manifest_url for finding in result.manifests})
        event({"event": "provider_completed", "provider_id": provider.provider_id, "status": result.status,
               "manifest_count": unique_count, "finding_count": len(result.manifests)})
        print(json.dumps({"provider_completed": provider.name, "status": result.status,
                          "manifest_count": unique_count}, ensure_ascii=True), flush=True)
        return result

    pipeline.HttpFetcher = AuditedFetcher
    pipeline.ResourceDiscoverer.discover = checkpoint
    try:
        result = pipeline.run_pipeline(config_path)
        print(json.dumps({"processed_providers": result.processed_provider_count,
                          "statuses": result.provider_status_counts, "unique_manifests": result.unique_manifest_count,
                          "manifest_urls_jsonl": str(result.manifest_urls_jsonl)}, ensure_ascii=True), flush=True)
    finally:
        pipeline.HttpFetcher = original_fetcher
        pipeline.ResourceDiscoverer.discover = original_discover


if __name__ == "__main__":
    main()
