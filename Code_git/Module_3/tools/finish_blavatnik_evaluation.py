"""Checkpoint the long public-item audit, then refresh and reconcile final outputs."""

from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pixel-python", type=Path, help="Optional Python interpreter with Pillow installed")
    args = parser.parse_args()
    module = Path(__file__).resolve().parents[1]
    root = module / "evaluation/2026-10-16_blavatnik_investigation"
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    last_reported = None
    while True:
        summary = json.loads((root / "item_snapshot/summary.json").read_text(encoding="utf-8"))
        processed = summary.get("counts", {}).get("processed", 0)
        bucket = processed // 1000
        if bucket != last_reported:
            print(json.dumps({"waiting_for_item_snapshot": True, "processed": processed,
                              "original_transcripts": summary.get("counts", {}).get("original_transcript", 0)}), flush=True)
            last_reported = bucket
        if summary.get("stop_reason") or datetime.now(timezone.utc) >= datetime(2026, 10, 16, 19, 36, tzinfo=timezone.utc):
            break
        time.sleep(30)
    commands = [
        ([module / "tools/complete_blavatnik_downstream.py", "--refresh-references"], None, sys.executable),
        ([module / "tools/prepare_additional_reference_downloads.py", "--limit", "150"], None, sys.executable),
        (["-m", "iiif_image_downloader", "download-all", "--config", root / "module8_additional_references.json"], module.parent / "Module_8", sys.executable),
        ([module / "tools/verify_catalogue_reference_bundles.py", "--module8-output", root / "additional_references/module8/output",
          "--report", root / "additional_reference_bundle_verification.json"], None, sys.executable),
    ]
    if args.pixel_python:
        commands.append(([module / "tools/verify_downloaded_pixels.py", "--module8-output", root / "additional_references/module8/output",
            "--raw-manifest-directory", root / "final/module4/raw_manifests", "--report", root / "additional_reference_image_verification.json"], None, str(args.pixel_python)))
    commands.extend([
        ([module / "tools/summarize_blavatnik_investigation.py"], None, sys.executable),
        ([module / "tools/report_blavatnik_catalogue.py"], None, sys.executable),
    ])
    results = []
    for arguments, cwd, python in commands:
        remaining = (datetime(2026, 10, 16, 20, 0, tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            raise RuntimeError("Wall-time checkpoint reached; completed evidence remains on disk")
        process = subprocess.run([python, *map(str, arguments)], env=environment, cwd=cwd, timeout=remaining,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        results.append({"at": datetime.now(timezone.utc).isoformat(), "arguments": list(map(str, arguments)),
                        "exit_code": process.returncode, "output": process.stdout})
        (root / "final_reconciliation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(process.stdout, flush=True)
        if process.returncode:
            raise RuntimeError("Final reconciliation failed; checkpoint evidence is retained")
    session = json.loads((root / "session.json").read_text(encoding="utf-8"))
    session["last_reconciled_at_utc"] = datetime.now(timezone.utc).isoformat()
    session["item_snapshot_stop_reason"] = summary.get("stop_reason")
    (root / "session.json").write_text(json.dumps(session, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
