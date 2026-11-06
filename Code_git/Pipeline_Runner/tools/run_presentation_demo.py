"""Run two bounded M1-8 demos: an old print with OCR and a medieval manuscript.

This wrapper calls the existing launcher twice. Each case downloads one image;
it does not change Module 8's global one-example behavior or download a whole
book. Both cases use explicit Manifest seeds, not homepage discovery.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
CODE = ROOT / "Code_git"
PYTHON = CODE / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
CASES = (
    ("with_reference_case", "with_reference", "Bavarian State Library: 1694 German print",
     "https://api.digitale-sammlungen.de/iiif/presentation/v2/bsb12188327/manifest"),
    ("without_reference_case", "without_reference", "Fragmentarium F-u3vo: medieval manuscript fragment",
     "https://fragmentarium.ms/metadata/iiif/F-u3vo/manifest.json"),
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def execute(command, console):
    """Show real stage progress while retaining a complete local console log."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    with console.open("w", encoding="utf-8") as stream:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        for line in process.stdout:
            print(line, end="", flush=True)
            stream.write(line)
            stream.flush()
        return process.wait()


def verify(case, category):
    output = case / "module_8/output"
    summary = read(output / "example/download_summary.json")
    index = [json.loads(line) for line in (output / "example/download_index.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(index) != 1 or summary["downloaded_images"] != 1 or summary["cached_images"]:
        raise RuntimeError("Expected one freshly downloaded image in a new case directory")
    row = index[0]
    if row["output_category"] != category:
        raise RuntimeError(f"Expected {category}, received {row['output_category']}")
    bundle = output / row["bundle_directory"]
    image = output / row["image_path"]
    record = read(bundle / "common_record.json")
    media = read(bundle / "common_media.json")
    profile = read(bundle / "ocr_document_profile.json")
    if not image.is_file() or not image.stat().st_size:
        raise RuntimeError("Downloaded image is missing or empty")
    if not (record["record_id"] == media["record_id"] == profile["record_id"] == row["record_id"]):
        raise RuntimeError("Document identifiers differ between the linked JSON files")
    if category == "with_reference" and row["reference_texts"] < 1:
        raise RuntimeError("The reference-bearing example did not retrieve institutional text")
    logs = sorted((case / "log").glob("Pipeline_*_log.json"), key=lambda p: p.stat().st_mtime)
    run = read(logs[-1])
    if run["status"] != "completed" or run["modules_run"] != list(range(1, 9)):
        raise RuntimeError("Not all eight modules completed")
    check = subprocess.run([str(PYTHON), str(CODE / "Module_3/tools/verify_linked_download_bundles.py"),
                            "--output-root", str(output), "--mode", "example",
                            "--report", str(case / "bundle_verification.json")], cwd=ROOT)
    if check.returncode:
        raise RuntimeError("Bundle schema/identifier/reference checks failed")
    return {"category": category, "modules_completed": 8, "manifest_url": media["source_manifest_url"],
            "record_title": record["object"]["title"], "date_evidence": record["object"].get("dates", []),
            "image_path": str(image), "bundle_directory": str(bundle), "canvas": media["canvas"],
            "downloaded_images": summary["downloaded_images"], "reference_texts": row["reference_texts"],
            "failed_images": summary["failed_images"], "failed_bundles": summary["failed_bundles"],
            "reference_text_failures": summary["reference_text_failures"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, help="New empty directory for both cases")
    args = parser.parse_args()
    output = (args.output_root or CODE / "Pipeline_Runner/data/runs" /
              ("paired_heritage_demo_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))).resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Choose a new empty output directory; old demo files are not overwritten")
    if not PYTHON.is_file():
        parser.error("Project environment missing; run python pipeline.py --setup first")
    output.mkdir(parents=True, exist_ok=True)
    summary = {"status": "running", "scope": "Two explicit historical Manifest seeds; each case runs M1-8 and downloads one example",
               "output_root": str(output), "cases": []}
    save(output / "demo_summary.json", summary)
    print(f"Paired demo output: {output}", flush=True)
    for slug, category, title, manifest in CASES:
        case = output / slug
        print(f"\n=== {title} | expected {category} ===", flush=True)
        command = [str(PYTHON), str(ROOT / "pipeline.py"), "--modules", "1-8", "--manifest-url", manifest,
                   "--max-manifests", "1", "--download", "example", "--force-refresh", "--no-llm",
                   "--run-dir", str(case)]
        if category == "with_reference":
            command.append("--require-reference")
        try:
            if execute(command, output / f"{slug}_console.txt"):
                raise RuntimeError(f"Pipeline failed; inspect {output / (slug + '_console.txt')}")
            result = verify(case, category)
        except Exception as exc:
            summary.update(status="failed", failed_case=slug, error=str(exc))
            save(output / "demo_summary.json", summary)
            print(str(exc), file=sys.stderr)
            return 1
        summary["cases"].append(result)
        save(output / "demo_summary.json", summary)
        print(f"PASS {category}: {result['image_path']}", flush=True)
    summary["status"] = "completed"
    save(output / "demo_summary.json", summary)
    print(f"\nPASS: two images, two complete M1-8 runs, six base JSON files. Summary: {output / 'demo_summary.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
