import json
from pathlib import Path

import pytest

from iiif_pipeline_runner.runner import PipelineRunError, _validate_modules, run_pipeline, select_modules


def test_select_modules_respects_inclusive_range():
    modules = [{"number": n} for n in range(1, 9)]
    assert [item["number"] for item in select_modules(modules, first=3, last=5)] == [3, 4, 5]


def test_select_modules_rejects_reversed_range():
    with pytest.raises(ValueError, match="cannot exceed"):
        select_modules([{"number": 1}], first=5, last=2)


def test_configuration_rejects_duplicate_module_number():
    row = {"number": 1, "name": "x", "directory": ".", "package": "x", "config": "c", "arguments": []}
    with pytest.raises(ValueError, match="unique"):
        _validate_modules([row, row])


def test_configuration_defaults_to_run_and_accepts_custom_command():
    standard = {"number": 7, "name": "x", "directory": ".", "package": "x", "config": "c"}
    downloader = {**standard, "number": 8, "command": "download-example"}
    validated = _validate_modules([standard, downloader])
    assert validated[0]["command"] == "run"
    assert validated[1]["command"] == "download-example"


def _package(root: Path, name: str, exit_code: int = 0):
    directory = root / name
    package = directory / name
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "__main__.py").write_text(
        "import json,sys\nprint(json.dumps({'package': __package__}))\nraise SystemExit(%d)\n" % exit_code,
        encoding="utf-8",
    )
    (directory / "config.json").write_text("{}", encoding="utf-8")
    return directory


def _config(tmp_path: Path, definitions):
    rows = []
    for number, name, exit_code in definitions:
        directory = _package(tmp_path, name, exit_code)
        rows.append({"number": number, "name": name, "directory": str(directory), "package": name, "config": "config.json", "arguments": []})
    path = tmp_path / "pipeline.json"
    path.write_text(json.dumps({"log_directory": str(tmp_path / "logs"), "modules": rows}), encoding="utf-8")
    return path


def test_runner_executes_modules_in_order_and_writes_log(tmp_path):
    summary = run_pipeline(_config(tmp_path, [(1, "first", 0), (2, "second", 0)]))
    assert summary["status"] == "completed"
    assert summary["modules_run"] == [1, 2]
    assert Path(summary["log_file"]).is_file()


def test_runner_uses_configured_subcommand(tmp_path):
    config = _config(tmp_path, [(8, "downloader", 0)])
    value = json.loads(config.read_text())
    value["modules"][0]["command"] = "download-example"
    config.write_text(json.dumps(value), encoding="utf-8")
    summary = run_pipeline(config)
    assert "download-example" in summary["module_results"][0]["command"]


def test_runner_fails_fast(tmp_path):
    config = _config(tmp_path, [(1, "first", 1), (2, "second", 0)])
    with pytest.raises(PipelineRunError) as caught:
        run_pipeline(config)
    assert caught.value.module_number == 1
    assert caught.value.summary["modules_run"] == [1]


def test_runner_checks_config_exists_before_launch(tmp_path):
    config = _config(tmp_path, [(1, "first", 0)])
    value = json.loads(config.read_text()); value["modules"][0]["config"] = "missing.json"
    config.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        run_pipeline(config)
