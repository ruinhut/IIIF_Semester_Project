# Modular IIIF Harvesting Pipeline Runner

This runner executes Modules 1–7 in numerical order, records each command and its output, and stops at the first failure. Each module remains independently runnable and owns its own configuration, outputs, and logs.

## Full run

```powershell
cd Code_git/Pipeline_Runner
python -m pip install -e .
python -m iiif_pipeline_runner --config pipeline.example.json
```

Module 1 is configured with `--institution all`. A full run performs live network work in Modules 1–4 and can take substantial time, depending on provider availability and the number of discovered Manifests.

## Resume or bounded run

```powershell
python -m iiif_pipeline_runner --config pipeline.example.json --from-module 3 --to-module 7
```

Use this after fixing a downstream module when its upstream files already exist. The runner validates every module directory/config before launch, uses the current Python interpreter, fails fast, and writes `data/log/Pipeline_<local-time>_log.json`.

## Cached smoke run

```powershell
python -m iiif_pipeline_runner --config pipeline.smoke.json
```

This runs Modules 4–7 against the checked local sample and normally uses Module 4's raw cache. Run unit tests with `python -m pytest -q`.
