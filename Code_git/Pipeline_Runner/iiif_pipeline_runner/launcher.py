"""Single-command orchestration with isolated per-run configuration snapshots.

No changes to module schemas or shared example configurations are required.
Every inter-module path is made explicit, including M4's raw-cache base.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

from .runner import PipelineRunError, run_pipeline

CODE_ROOT = Path(__file__).resolve().parents[2]
PACKAGES = {1: "iiif_provider_census", 2: "iiif_entry_validator", 3: "iiif_resource_discovery",
            4: "iiif_manifest_validator", 5: "iiif_rights_filter", 6: "iiif_metadata_normalizer",
            7: "iiif_common_exporter", 8: "iiif_image_downloader"}


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_modules(text: str) -> list[int]:
    """Accept inclusive ranges and lists, e.g. 1-4 or 1,2,4-8."""
    numbers = set()
    try:
        for item in text.split(","):
            endpoints = item.strip().split("-")
            if len(endpoints) == 1:
                numbers.add(int(endpoints[0]))
            elif len(endpoints) == 2:
                start, stop = map(int, endpoints)
                if start > stop or start < 1 or stop > 8:
                    raise ValueError()
                numbers.update(range(start, stop + 1))
            else:
                raise ValueError()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use module numbers/ranges such as 1-4 or 6,7,8") from exc
    if not numbers or not numbers <= set(range(1, 9)):
        raise argparse.ArgumentTypeError("Module numbers must be between 1 and 8")
    return sorted(numbers)


def positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Must be a positive integer")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the IIIF pipeline from one command; no manual module-by-module setup.")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--modules", type=parse_modules, help="Modules to run: 1-8, 1-3, or 6,7,8")
    selection.add_argument("--module-count", type=positive, help="Run the first N modules (1-8)")
    parser.add_argument("--from-module", type=int, choices=range(1, 9))
    parser.add_argument("--to-module", type=int, choices=range(1, 9))
    parser.add_argument("--institution", action="append", help="Institution name; repeat for multiple; default all")
    parser.add_argument("--manifest-url", action="append", help="Optional fixed Manifest seed for a small handoff demonstration")
    parser.add_argument("--max-manifests", type=positive, help="Per-provider discovery budget; new runs default to 10")
    parser.add_argument("--download", choices=["example", "all"], help="One example across the output, or all exported images")
    parser.add_argument("--require-reference", action="store_true", default=None, help="M8 must retrieve page-linked reference text")
    parser.add_argument("--run-dir", type=Path, help="Isolated output directory; printed automatically when omitted")
    parser.add_argument("--resume", action="store_true", help="Reuse saved configs/upstream files in --run-dir")
    parser.add_argument("--force-refresh", action="store_true", help="Refetch M4 Manifests rather than reuse its cache")
    parser.add_argument("--dry-run", action="store_true", help="Prepare configs and display the plan without contacting institutions")
    parser.add_argument("--config", type=Path, help="Advanced: use an existing pipeline config without generating snapshots")
    llm = parser.add_argument_group("Optional Module 3 LLM investigation (disabled by default)")
    enable = llm.add_mutually_exclusive_group()
    enable.add_argument("--llm", action="store_true", default=None, help="Investigate unresolved providers with your LLM API")
    enable.add_argument("--no-llm", dest="llm", action="store_false", default=None, help="Disable paid investigation; keep replaying verified knowledge")
    llm.add_argument("--llm-model", help="Your API model ID; alternatively set IIIF_LLM_MODEL")
    llm.add_argument("--llm-base-url", help="API root; default https://api.openai.com/v1")
    llm.add_argument("--llm-mode", choices=["responses", "chat_completions"])
    llm.add_argument("--llm-key-file", type=Path, help="Local token text/JSON file; its contents are never copied into configs")
    llm.add_argument("--llm-key-env", help="Environment variable containing your API token")
    llm.add_argument("--llm-key-prompt", action="store_true", help="Read a hidden token once, without saving it")
    llm.add_argument("--llm-web-search", action="store_true", default=None, help="Use Responses hosted web search if supported by your model")
    llm.add_argument("--llm-max-providers", type=positive, help="Unresolved providers to investigate per run; default 3")
    llm.add_argument("--llm-max-rounds", type=positive, help="LLM calls per investigated provider; default 6, maximum 30")
    llm.add_argument("--llm-max-fetches", type=positive, help="Public GET requests per investigated provider; default 16, maximum 200")
    return parser


def selected_modules(args, parser) -> list[int] | None:
    if (args.modules or args.module_count is not None) and (args.from_module or args.to_module):
        parser.error("Use --modules/--module-count OR --from-module/--to-module")
    if args.module_count is not None:
        if args.module_count > 8:
            parser.error("--module-count must be 1-8")
        return list(range(1, args.module_count + 1))
    if args.modules:
        return args.modules
    if args.from_module or args.to_module:
        first, last = args.from_module or 1, args.to_module or 8
        if first > last:
            parser.error("--from-module cannot exceed --to-module")
        return list(range(first, last + 1))
    return None


def configure_llm(value: dict, args):
    """Store non-secret settings only; enabling requests is always explicit."""
    config = value.setdefault("llm_discovery", {})
    if args.llm is not None:
        config["enabled"] = args.llm
    fields = {"llm_model": "model", "llm_base_url": "base_url", "llm_mode": "api_mode",
              "llm_key_env": "api_key_env", "llm_web_search": "web_search",
              "llm_max_providers": "max_providers", "llm_max_rounds": "max_rounds",
              "llm_max_fetches": "max_fetches_per_provider"}
    for option, field in fields.items():
        if getattr(args, option) is not None:
            config[field] = getattr(args, option)
    if args.llm_key_file:
        config["api_key_file"] = str(args.llm_key_file.resolve())
    if args.llm_key_prompt:
        config.pop("api_key_file", None)
        config["api_key_env"] = "IIIF_LLM_API_KEY"
    if config.get("web_search") and config.get("api_mode", "responses") != "responses":
        raise ValueError("--llm-web-search requires --llm-mode responses and a supporting model")
    if int(config.get("max_rounds", 6)) > 30 or int(config.get("max_fetches_per_provider", 16)) > 200:
        raise ValueError("LLM limits: at most 30 rounds and 200 public fetches per provider")


def prepare_run(args, *, code_root: Path = CODE_ROOT) -> tuple[Path, Path]:
    run = (args.run_dir or code_root / "Pipeline_Runner/data/runs" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")).resolve()
    pipeline_path = run / "pipeline.json"
    if args.resume:
        if not args.run_dir or not pipeline_path.is_file():
            raise ValueError("--resume requires --run-dir with a previously prepared pipeline.json")
        if args.institution or args.manifest_url:
            raise ValueError("Resume keeps the original institution/seed selection; start a new run to change it")
        pipeline = json.loads(pipeline_path.read_text(encoding="utf-8-sig"))
        config3 = Path(pipeline["modules"][2]["config"])
        value = json.loads(config3.read_text(encoding="utf-8-sig"))
        configure_llm(value, args)
        if args.max_manifests is not None:
            value.setdefault("limits", {})["max_manifests_per_provider"] = args.max_manifests
        write_json(config3, value)
        module8 = pipeline["modules"][7]
        if args.download:
            module8["command"] = "download-" + args.download
        if args.require_reference:
            value = json.loads(Path(module8["config"]).read_text(encoding="utf-8-sig"))
            value["require_reference_text"] = True
            write_json(Path(module8["config"]), value)
        if args.force_refresh:
            path4 = Path(pipeline["modules"][3]["config"])
            value = json.loads(path4.read_text(encoding="utf-8-sig"))
            value.setdefault("run", {})["force_refresh"] = True
            write_json(path4, value)
        write_json(pipeline_path, pipeline)
        return pipeline_path, run
    if run.exists() and any(run.iterdir()):
        raise ValueError("Run directory is not empty; use --resume or choose a new directory")
    configs = run / "configs"
    configs.mkdir(parents=True, exist_ok=True)
    out = {n: run / f"module_{n}/output" for n in range(1, 9)}
    values = {}
    # Only these fields refer to existing assets; unknown textual config values
    # must never be interpreted as paths or rewritten.
    assets = {1: ["manual_sources"], 3: ["curated_endpoints", "knowledge_base", "learned_knowledge_base"],
              5: ["policy_file"], 6: ["provider_reference_sources"],
              7: ["profile_json", "record_schema_json", "media_schema_json", "ocr_profile_schema_json"]}
    for n in range(1, 9):
        directory = code_root / f"Module_{n}"
        value = json.loads((directory / "config.example.json").read_text(encoding="utf-8-sig"))
        for field in assets.get(n, []):
            if field not in value:
                continue
            if isinstance(value[field], list):
                value[field] = [str((directory / p).resolve()) for p in value[field]]
            elif value[field]:
                value[field] = str((directory / value[field]).resolve())
        value.update(output_directory=str(out[n]), log_directory=str(run / f"module_{n}/log"))
        values[n] = value
    if args.manifest_url:
        providers = []
        for i, url in enumerate(args.manifest_url, 1):
            parts = urlsplit(url)
            if parts.scheme not in {"http", "https"} or not parts.netloc or parts.username or parts.password:
                raise ValueError("--manifest-url must be an HTTP(S) URL without credentials")
            providers.append({"name": f"Direct Manifest seed {i}", "institution_url": f"{parts.scheme}://{parts.netloc}/",
                "discovery_endpoint": url, "endpoint_role": "manifest", "discovery_type": "Manifest"})
        seed = configs / "manifest_seeds.json"
        write_json(seed, {"providers": providers})
        values[1].update(registry_sources=[], manual_sources=[str(seed)])
        institutions = ["all"]
    else:
        institutions = args.institution or ["all"]
    values[2]["input_jsonl"] = str(out[1] / "selected_providers.jsonl")
    values[3]["input_jsonl"] = str(out[2] / "checked_entry_points.jsonl")
    values[3].setdefault("limits", {})["max_manifests_per_provider"] = args.max_manifests or 10
    configure_llm(values[3], args)
    values[4].update(input_jsonl=str(out[3] / "manifest_urls.jsonl"), raw_manifest_directory=str(run / "module_4/raw_manifests"))
    values[4].setdefault("run", {})["force_refresh"] = args.force_refresh
    # M4's relative raw_manifest_path is relative to its config directory.
    values[5].update(validated_manifests_jsonl=str(out[4] / "validated_manifests.jsonl"),
        resource_inventory_jsonl=str(out[4] / "manifest_resource_inventory.jsonl"), module_4_directory=str(configs))
    values[6].update(research_manifests_jsonl=str(out[5] / "research_manifests.jsonl"),
        research_resource_inventory_jsonl=str(out[5] / "research_resource_inventory.jsonl"), module_4_directory=str(configs))
    for key, filename in [("normalized_records_jsonl", "normalized_records.jsonl"),
                          ("normalized_resources_jsonl", "normalized_resources.jsonl"),
                          ("normalized_reference_texts_jsonl", "normalized_reference_texts.jsonl")]:
        values[7][key] = str(out[6] / filename)
    for key, filename in [("common_records_jsonl", "common_records.jsonl"), ("common_media_jsonl", "common_media.jsonl"),
                          ("ocr_document_profiles_jsonl", "ocr_document_profiles.jsonl"),
                          ("institution_reference_texts_jsonl", "institution_reference_texts.jsonl")]:
        values[8][key] = str(out[7] / filename)
    values[8]["require_reference_text"] = bool(args.require_reference)
    modules = []
    for n, value in values.items():
        path = configs / f"module_{n}.json"
        write_json(path, value)
        arguments = [x for name in institutions for x in ("--institution", name)] if n == 1 else []
        modules.append({"number": n, "name": PACKAGES[n], "directory": str(code_root / f"Module_{n}"),
            "package": PACKAGES[n], "config": str(path), "arguments": arguments,
            "command": "download-" + (args.download or "example") if n == 8 else "run"})
    write_json(pipeline_path, {"log_directory": str(run / "log"), "modules": modules})
    return pipeline_path, run


def check_dependencies(pipeline_path: Path, selected: list[int] | None):
    """Reject skipped stages without their real upstream files, before HTTP work."""
    pipeline = json.loads(pipeline_path.read_text(encoding="utf-8-sig"))
    modules = pipeline["modules"]
    selected_set = set(selected or [m["number"] for m in modules])
    inputs = {2: (1, "input_jsonl"), 3: (2, "input_jsonl"), 4: (3, "input_jsonl"),
              5: (4, "validated_manifests_jsonl"), 6: (5, "research_manifests_jsonl"),
              7: (6, "normalized_records_jsonl"), 8: (7, "common_media_jsonl")}
    for m in modules:
        n = m["number"]
        if n not in selected_set or n not in inputs:
            continue
        previous, key = inputs[n]
        if previous in selected_set:
            continue
        config_path = Path(m["config"])
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        source = Path(config[key])
        if not source.is_absolute():
            source = config_path.parent / source
        if not source.is_file():
            raise ValueError(f"Module {n} needs {source}. Run its upstream modules first, then use --resume --run-dir.")


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = selected_modules(args, parser)
    try:
        if args.config:
            llm_options = any(v is not None and v is not False for k, v in vars(args).items() if k.startswith("llm"))
            if args.llm is False:
                llm_options = True
            if args.run_dir or args.resume or args.institution or args.manifest_url or args.max_manifests or args.download or args.require_reference or args.force_refresh or llm_options:
                parser.error("--config uses its saved settings; do not combine with generated-run options")
            path = args.config.resolve()
            run = path.parent
        else:
            if args.llm_key_prompt and not args.dry_run:
                os.environ["IIIF_LLM_API_KEY"] = getpass.getpass("LLM API token (hidden, not saved): ")
            path, run = prepare_run(args)
        print("Run directory:", run, flush=True)
        print("Pipeline configuration:", path, flush=True)
        if args.dry_run:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            print("Modules:", selected or [m["number"] for m in value["modules"]])
            print("Dry run: configuration only; no institution or LLM requests.")
            return 0
        if not args.config:
            check_dependencies(path, selected)
        summary = run_pipeline(path, only_modules=selected)
        print(json.dumps({key: summary[key] for key in ("status", "modules_run", "log_file")},
                         ensure_ascii=False, indent=2))
        return 0
    except PipelineRunError as exc:
        print(json.dumps(exc.summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return exc.return_code
    except (OSError, ValueError, RuntimeError) as exc:
        print("error:", str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
