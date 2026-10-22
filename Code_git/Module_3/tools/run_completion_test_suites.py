"""Run the Module 3-8 regression suites and retain exact test summaries."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.evaluation_root.resolve()
    code = Path(__file__).resolve().parents[2]
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    def run(number):
        result = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                                cwd=code / f"Module_{number}", env=environment,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                encoding="utf-8")
        passed = re.search(r"(\d+) passed", result.stdout)
        subtests = re.search(r"(\d+) subtests passed", result.stdout)
        row = {"module": number, "exit_code": result.returncode,
               "passed": int(passed.group(1)) if passed else 0,
               "subtests": int(subtests.group(1)) if subtests else 0,
               "output": result.stdout}
        print(json.dumps({k: v for k, v in row.items() if k != "output"}), flush=True)
        return row

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(run, range(3, 9)))
    (root / "test_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    if any(r["exit_code"] or not r["passed"] for r in results):
        raise SystemExit("A suite failed; inspect test_results.json")


if __name__ == "__main__":
    main()
