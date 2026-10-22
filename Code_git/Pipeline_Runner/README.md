# Modular IIIF Harvesting Pipeline Runner

## Live acceptance test: Modules 1–8 and reference routing

Run `tools/run_full_acceptance.py` with the project virtual environment and a
`--pixel-python` interpreter that has Pillow. It creates isolated, timestamped
outputs and runs all eight modules for three fixed real Manifest seeds: BSB
hOCR, FromThePage transcription, and EPFL without a page reference. It then
checks schemas, record/resource/Canvas joins, image decoding, fresh downloads,
and `with_reference` / `without_reference` routing. This is a bounded contract
test, not an exhaustive provider discovery or text-format coverage claim.

See the [repository README](../../README.md) for portable Windows cmd setup,
full-pipeline commands, module responsibilities, and output categories.
Detailed local Chinese reports remain in `output/` and are not versioned.

This runner executes Modules 1–8 in numerical order, records each command and its output, and stops at the first failure. Each module remains independently runnable and owns its own configuration, outputs, and logs. Module 8 uses `download-example` in runner configurations so a routine validation run downloads only one image; bulk download remains an explicit operator action.

## Full run

```powershell
cd Code_git/Pipeline_Runner
python -m pip install -e .
python -m iiif_pipeline_runner --config pipeline.example.json
```

For a researcher-owned rerun that re-fetches Module 4 Manifests instead of
reusing the existing raw cache:

```powershell
python -m iiif_pipeline_runner --config pipeline.self-run.json
```

The complete Chinese command guide is
`完整流水线命令行运行手册.md`.

Module 1 is configured with `--institution all`. A full run performs live network work in Modules 1–4 and can take substantial time, depending on provider availability and the number of discovered Manifests.

## Resume or bounded run

```powershell
python -m iiif_pipeline_runner --config pipeline.example.json --from-module 3 --to-module 8
```

Use this after fixing a downstream module when its upstream files already exist. The runner validates every module directory/config before launch, uses the current Python interpreter, fails fast, and writes `data/log/Pipeline_<local-time>_log.json`.

## Cached smoke run

```powershell
python -m iiif_pipeline_runner --config pipeline.smoke.json
```

This runs Modules 4–8 against the checked local sample and normally uses Module 4's raw cache. Run unit tests with `python -m pytest -q`.
## Bounded live Module 1–8 validation

```powershell
python -m iiif_pipeline_runner --config pipeline.fragmentarium-smoke.json
```

This selects one known provider, caps discovery at two Manifests, and writes isolated results under `data/e2e_validation/`. It checks every module boundary without starting a large harvest.
