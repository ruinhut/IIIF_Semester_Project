"""Consolidate explicitly selected successful batches without hiding failures."""

import argparse
import json
from pathlib import Path


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recovery", type=Path, action="append", default=[])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "evaluation/2026-10-15_five_provider_completion"
    main_output = root / "final_validation/module3/output"
    reports, sources = {}, {}
    for source in [main_output, *[p.resolve() for p in args.recovery]]:
        for report in rows(source / "provider_discovery.jsonl"):
            pid = report["provider_id"]
            if pid not in reports or (reports[pid]["resource_discovery"]["manifest_count"] == 0 and report["resource_discovery"]["manifest_count"] > 0):
                reports[pid] = report
                sources[pid] = source
    expected = {p["provider_id"] for p in json.loads((root / "providers.json").read_text(encoding="utf-8"))}
    if any(pid not in reports or reports[pid]["resource_discovery"]["manifest_count"] == 0 for pid in expected):
        raise RuntimeError("Not all five providers succeeded. Inspect request logs and explicitly rerun failed providers.")
    manifests = {}
    for source in set(sources.values()):
        for row in rows(source / "manifest_urls.jsonl"):
            if any(sources.get(p["provider_id"]) == source for p in row["providers"]):
                manifests[row["manifest_url"]] = row
    output = root / "combined/module3/output"
    output.mkdir(parents=True, exist_ok=True)
    for name, data in (("provider_discovery.jsonl", reports.values()), ("manifest_urls.jsonl", manifests.values()), ("unresolved_providers.jsonl", [])):
        (output / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in data), encoding="utf-8")
    (root / "combined/batch_sources.json").write_text(json.dumps({pid: str(p) for pid, p in sources.items()}, indent=2), encoding="utf-8")
    print(f"Consolidated {len(expected)} successful providers and {len(manifests)} Manifest URLs; original attempts retained.")


if __name__ == "__main__":
    main()
