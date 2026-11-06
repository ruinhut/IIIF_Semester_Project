"""Meaningful checks for selection, isolation, resumption and data contracts."""
import json
import argparse
from pathlib import Path
import pytest
from iiif_pipeline_runner.launcher import build_parser, check_dependencies, parse_modules, prepare_run, selected_modules

CODE = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("text,expected", [("1-4", [1,2,3,4]), ("6,7,8", [6,7,8]), ("3,1-2,2", [1,2,3])])
def test_selection(text, expected):
    assert parse_modules(text) == expected


@pytest.mark.parametrize("text", ["0", "1-9", "4-1", "", "one", "1,,2"])
def test_invalid_selection(text):
    with pytest.raises(argparse.ArgumentTypeError):
        parse_modules(text)


def test_module_count_and_conflict():
    parser = build_parser()
    assert selected_modules(parser.parse_args(["--module-count", "3"]), parser) == [1,2,3]
    with pytest.raises(SystemExit):
        selected_modules(parser.parse_args(["--modules", "1-4", "--from-module", "2"]), parser)


def test_isolated_configs_preserve_shared_assets_and_raw_base(tmp_path):
    parser = build_parser()
    before = (CODE / "Module_3/config.example.json").read_bytes()
    args = parser.parse_args(["--run-dir", str(tmp_path / "isolated"), "--institution", "Example", "--max-manifests", "2"])
    path, run = prepare_run(args, code_root=CODE)
    pipeline = json.loads(path.read_text(encoding="utf-8"))
    cfg3 = json.loads(Path(pipeline["modules"][2]["config"]).read_text(encoding="utf-8"))
    cfg5 = json.loads(Path(pipeline["modules"][4]["config"]).read_text(encoding="utf-8"))
    assert cfg3["limits"]["max_manifests_per_provider"] == 2
    assert cfg3["llm_discovery"]["enabled"] is False
    assert Path(cfg3["knowledge_base"]).is_file()
    assert cfg5["module_4_directory"] == str(run / "configs")
    assert (CODE / "Module_3/config.example.json").read_bytes() == before
    assert pipeline["modules"][0]["arguments"] == ["--institution", "Example"]
    assert pipeline["modules"][7]["command"] == "download-example"
    with pytest.raises(ValueError, match="not empty"):
        prepare_run(args, code_root=CODE)


def test_resume_keeps_upstream_and_switches_download_mode(tmp_path):
    parser = build_parser()
    path, run = prepare_run(parser.parse_args(["--run-dir", str(tmp_path / "run")]), code_root=CODE)
    data = run / "module_7/output/common_media.jsonl"
    data.parent.mkdir(parents=True); data.write_text("{}\n")
    args = parser.parse_args(["--run-dir", str(run), "--resume", "--download", "all", "--require-reference"])
    prepare_run(args, code_root=CODE)
    check_dependencies(path, [8])
    assert data.read_text() == "{}\n"
    pipeline = json.loads(path.read_text(encoding="utf-8"))
    assert pipeline["modules"][7]["command"] == "download-all"
    with pytest.raises(ValueError, match="needs"):
        check_dependencies(path, [4])


def test_fixed_seed_does_not_claim_homepage_discovery(tmp_path):
    parser = build_parser()
    path, run = prepare_run(parser.parse_args(["--run-dir", str(tmp_path / "seed"), "--manifest-url", "https://example.org/iiif/item/manifest"]), code_root=CODE)
    seed = json.loads((run / "configs/manifest_seeds.json").read_text(encoding="utf-8"))
    cfg = json.loads((run / "configs/module_1.json").read_text(encoding="utf-8"))
    assert cfg["registry_sources"] == []
    assert seed["providers"][0]["discovery_type"] == "Manifest"


def test_atlas_export_uses_isolated_output_and_default_contract(tmp_path):
    parser = build_parser()
    path, run = prepare_run(parser.parse_args(["--run-dir", str(tmp_path / "atlas"), "--atlas-export"]), code_root=CODE)
    pipeline = json.loads(path.read_text(encoding="utf-8"))
    cfg7 = json.loads(Path(pipeline["modules"][6]["config"]).read_text(encoding="utf-8"))
    assert cfg7["time_atlas"]["enabled"] is True
    assert cfg7["time_atlas"]["output_directory"] == str(run / "atlas")
    assert Path(cfg7["time_atlas"]["profile_json"]).is_file()
    assert cfg7["output_directory"] == str(run / "module_7/output")


def test_resume_can_enable_atlas_without_reharvesting(tmp_path):
    parser = build_parser()
    path, run = prepare_run(parser.parse_args(["--run-dir", str(tmp_path / "resume")]), code_root=CODE)
    own = tmp_path / "profile.json"
    own.write_text("{}")
    prepare_run(parser.parse_args(["--run-dir", str(run), "--resume", "--modules", "7", "--atlas-profile", str(own)]), code_root=CODE)
    pipeline = json.loads(path.read_text(encoding="utf-8"))
    cfg7 = json.loads(Path(pipeline["modules"][6]["config"]).read_text(encoding="utf-8"))
    assert cfg7["time_atlas"]["profile_json"] == str(own)
    assert cfg7["time_atlas"]["enabled"] is True


def test_llm_settings_and_key_path_are_preserved_without_copying_token(tmp_path):
    key = tmp_path / "private-token.txt"
    key.write_text("do-not-copy-this-token")
    parser = build_parser()
    args = parser.parse_args(["--run-dir", str(tmp_path / "run"), "--llm", "--llm-model", "my-model",
                             "--llm-key-file", str(key), "--llm-max-rounds", "4"])
    path, run = prepare_run(args, code_root=CODE)
    cfg = json.loads((run / "configs/module_3.json").read_text())
    assert cfg["llm_discovery"]["enabled"] is True
    assert cfg["llm_discovery"]["api_key_file"] == str(key.resolve())
    assert cfg["llm_discovery"]["max_rounds"] == 4
    assert "do-not-copy-this-token" not in "".join(p.read_text() for p in (run / "configs").glob("*.json"))
    assert Path(cfg["learned_knowledge_base"]).parent == CODE / "Module_3/config"
    prepare_run(parser.parse_args(["--run-dir", str(run), "--resume", "--no-llm"]), code_root=CODE)
    assert json.loads((run / "configs/module_3.json").read_text())["llm_discovery"]["enabled"] is False
