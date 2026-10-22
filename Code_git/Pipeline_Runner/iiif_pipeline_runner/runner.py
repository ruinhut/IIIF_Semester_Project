"""Validated, fail-fast orchestration for Modules 1–8."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping


def run_pipeline(config_path: Path, *, first: int | None = None, last: int | None = None) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    modules = select_modules(_validate_modules(config.get("modules")), first=first, last=last)
    if not modules:
        raise ValueError("No modules selected")
    base = config_path.parent
    log_dir = _resolve(base, str(config.get("log_directory", "data/log")))
    log_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now().astimezone()
    module_results: list[dict[str, Any]] = []

    highest_module = max(item["number"] for item in modules)
    for module in modules:
        directory = _resolve(base, module["directory"])
        module_config = _resolve(directory, module["config"])
        if not directory.is_dir():
            raise FileNotFoundError(f"Module directory does not exist: {directory}")
        if not module_config.is_file():
            raise FileNotFoundError(f"Module config does not exist: {module_config}")
        command = [
            sys.executable,
            "-m",
            module["package"],
            module["command"],
            "--config",
            str(module_config),
            *module["arguments"],
        ]
        print(
            f"[Module {module['number']}/{highest_module}] Starting: {module['name']}",
            file=sys.stderr,
            flush=True,
        )
        module_started = datetime.now().astimezone()
        completed = subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding="utf-8", errors="replace")
        result = {
            "number": module["number"], "name": module["name"],
            "started_at": module_started.isoformat(timespec="seconds"),
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "return_code": completed.returncode,
            "command": command, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip(),
        }
        module_results.append(result)
        if completed.returncode != 0:
            print(
                f"[Module {module['number']}/{highest_module}] Failed with exit code "
                f"{completed.returncode}",
                file=sys.stderr,
                flush=True,
            )
            summary = _summary(started, module_results, status="failed")
            _write_log(log_dir, started, summary)
            raise PipelineRunError(module["number"], completed.returncode, summary)
        print(
            f"[Module {module['number']}/{highest_module}] Completed",
            file=sys.stderr,
            flush=True,
        )

    summary = _summary(started, module_results, status="completed")
    log = _write_log(log_dir, started, summary)
    summary["log_file"] = str(log)
    return summary


class PipelineRunError(RuntimeError):
    def __init__(self, module_number: int, return_code: int, summary: Mapping[str, Any]) -> None:
        super().__init__(f"Module {module_number} failed with exit code {return_code}")
        self.module_number = module_number
        self.return_code = return_code
        self.summary = dict(summary)


def select_modules(modules: list[dict[str, Any]], *, first: int | None, last: int | None) -> list[dict[str, Any]]:
    lower = first if first is not None else min(item["number"] for item in modules)
    upper = last if last is not None else max(item["number"] for item in modules)
    if lower > upper:
        raise ValueError("--from-module cannot exceed --to-module")
    return [item for item in modules if lower <= item["number"] <= upper]


def _validate_modules(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("Configuration requires a non-empty modules list")
    output: list[dict[str, Any]] = []
    seen: set[int] = set()
    for raw in value:
        if not isinstance(raw, Mapping):
            raise ValueError("Each module configuration must be an object")
        number = raw.get("number")
        if not isinstance(number, int) or isinstance(number, bool) or number < 1 or number > 8 or number in seen:
            raise ValueError("Module numbers must be unique integers from 1 to 8")
        for key in ("name", "directory", "package", "config"):
            if not isinstance(raw.get(key), str) or not str(raw[key]).strip():
                raise ValueError(f"Module {number} requires {key}")
        arguments = raw.get("arguments", [])
        if not isinstance(arguments, list) or not all(isinstance(item, str) for item in arguments):
            raise ValueError(f"Module {number} arguments must be a list of strings")
        command = raw.get("command", "run")
        if not isinstance(command, str) or not command.strip():
            raise ValueError(f"Module {number} command must be a non-empty string")
        output.append({
            **dict(raw),
            "command": command.strip(),
            "arguments": list(arguments),
        })
        seen.add(number)
    return sorted(output, key=lambda item: item["number"])


def _summary(started: datetime, results: list[dict[str, Any]], *, status: str) -> dict[str, Any]:
    return {
        "pipeline": "Modular IIIF Harvesting Pipeline",
        "status": status,
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "modules_run": [item["number"] for item in results],
        "module_results": results,
    }


def _write_log(log_dir: Path, started: datetime, summary: Mapping[str, Any]) -> Path:
    path = log_dir / f"Pipeline_{started.strftime('%Y-%m-%d_%H-%M-%S')}_log.json"
    path.write_text(json.dumps(dict(summary), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()
