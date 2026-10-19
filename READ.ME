# IIIF Semester Project

A modular IIIF harvesting pipeline developed for an EPFL DHLAB semester project.
It discovers institutional Manifests, validates their structure, preserves rights
and provenance, normalizes metadata, and downloads linked page images and
provider-supplied reference text for downstream OCR experiments.

## Pipeline

```text
Registry + official IIIF guides + community lists + maintained entries
                                  |
                         1. Provider census
                                  |
                         2. Endpoint checks
                                  |
                         3. Manifest discovery
                                  |
                         4. Fetch and validate
                                  |
                         5. Rights classification
                                  |
                         6. Metadata and text extraction
                                  |
                         7. Common-schema export
                                  |
                         8. Image and reference-text download
```

Each module has its own configuration, command-line entry point, tests, outputs,
and logs. `Pipeline_Runner` executes the configured modules in order and stops
if a module exits with an error.

| Directory under `Code_git/` | Core responsibility |
|---|---|
| `Module_1` | Combine provider sources, preserve candidate endpoints, deduplicate institutions, and select one institution or all known active institutions. |
| `Module_2` | Check every supplied endpoint; record HTTP status, redirects, elapsed time, content type, and JSON parsing results. |
| `Module_3` | Discover Manifest URLs through Collections, Change Discovery, direct links, bounded HTML discovery, and configurable institutional API recipes. Preserve reusable skills and provider configuration in its knowledge base. |
| `Module_4` | Retrieve and retain raw Manifest JSON, validate basic Presentation structure, and inventory image resources. |
| `Module_5` | Preserve rights statements, classify reuse restrictions, and produce separate research-retained and reuse-eligible outputs. Unknown or restricted rights are not relabelled as unrestricted. |
| `Module_6` | Extract and normalize document metadata, image resources, and identifiable institution-supplied OCR/transcription references. |
| `Module_7` | Validate and export common document records, image records, OCR document profiles, and linked institutional reference-text records. |
| `Module_8` | Download one example or all eligible images, together with three linked JSON files and any retrievable page-level reference text. |
| `Pipeline_Runner` | Orchestrate the modules and provide a reproducible, bounded, live end-to-end acceptance test. |

## Setup: Windows Command Prompt (cmd.exe)

Requires Git, Python **3.10 or newer**, and internet access for live harvesting.
Run these commands in **cmd.exe** from the folder in which you want the clone.
The commands use ordinary ASCII hyphens; they are not PowerShell commands.

```bat
git clone https://github.com/ruinhut/IIIF_Semester_Project.git
cd IIIF_Semester_Project\Code_git
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
for %M in (1 2 3 4 5 6 7 8) do .venv\Scripts\python.exe -m pip install -e .\Module_%M
.venv\Scripts\python.exe -m pip install -e .\Pipeline_Runner
.venv\Scripts\python.exe -m pip install pytest Pillow certifi
set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe -m certifi > .venv\certifi-path.txt
set /p SSL_CERT_FILE=<.venv\certifi-path.txt
```

The certificate setting uses a maintained CA bundle without disabling TLS
verification. When opening another terminal, repeat the last three environment
commands from `Code_git`. In a `.bat` file, replace `%M` with `%%M` in loops.

## Run all eight modules: small live verification

From `Code_git`, after setup:

```bat
.venv\Scripts\python.exe Pipeline_Runner\tools\run_full_acceptance.py
```

This runs **Module 1 through Module 8 separately for each of three fixed real
Manifest seeds**: BSB hOCR, FromThePage transcription, and an EPFL Plume item
without a declared page reference. It checks schemas, document/image/text joins,
image decoding, and output categories. Each case downloads one real image.
This verifies module handoffs; it does not benchmark discovery from arbitrary
institutional homepages or download an entire catalogue.

Results go to a new directory printed by the command:

```text
Code_git/Pipeline_Runner/data/full_acceptance_<computer-time>/
  acceptance_results.csv
  module_input_output_inventory.csv
  bsb_hocr/
  fromthepage_transcription/
  epfl_without_reference/
```

Each case contains `module_1` through `module_8`, configurations, and pipeline
logs. Module 8's downloaded files are under `module_8/output/example/`.

## Run the configured institutional census pipeline

From `Code_git`:

```bat
cd Pipeline_Runner
..\.venv\Scripts\python.exe -m iiif_pipeline_runner --config pipeline.self-run.json
```

This reads the maintained provider sources and runs all eight modules using
their `config.example.json` files. Module 3's configured discovery budgets
bound traversal; this is not an exhaustive harvest. By default, Module 8
downloads **one example across the resulting eligible images**. Network
availability and catalogue size affect runtime.

To resume after fixing an error, with the required upstream files still present:

```bat
..\.venv\Scripts\python.exe -m iiif_pipeline_runner --config pipeline.self-run.json --from-module 3 --to-module 8
```

Production outputs are under `Code_git/Module_N/data/output/`, with logs in
`Code_git/Module_N/data/log/`. Module 4 also retains `data/raw_manifests/`.

For an explicit bulk image download, return to `Code_git` and run:

```bat
cd ..
.venv\Scripts\python.exe -m iiif_image_downloader download-all --config Module_8\config.example.json
```

This downloads all eligible image records already exported by Module 7; it does
not discover additional Manifests. Output is `Module_8/data/output/all/`.

## Final output and reference text

Module 7 exports these JSONL files (one JSON object per line):

- `common_records.jsonl`: document records keyed by `record_id`.
- `common_media.jsonl`: images linked to documents through `record_id`, with
  their own `resource_id`, Canvas URL, and image URL/service information.
- `ocr_document_profiles.jsonl`: OCR-oriented document characteristics and
  metadata evidence, linked by `record_id`.
- `institution_reference_texts.jsonl`: institution-provided OCR/transcription
  references, with page associations where the source establishes them.

Module 8 creates a portable bundle for each downloaded image:

```text
output/example/ or output/all/
  with_reference/<document>/<image>/
  without_reference/<document>/<image>/
  reference_failed/<document>/<image>/
  download_index.jsonl
  download_summary.json
```

Every successful bundle contains the image, `common_record.json`,
`common_media.json`, and `ocr_document_profile.json`. `with_reference` also
contains `institution_reference_texts.json`, the saved reference source, and
plain text. A declared reference that cannot be retrieved is reported separately
from an image with no identified page reference. Document-level text is not
automatically treated as a page-aligned label. Provider OCR is reference data,
not a guarantee of manually corrected ground truth.

## Tests and current limits

From `Code_git`, run each test suite independently:

```bat
for %M in (1 2 3 4 5 6 7 8) do cmd /c "cd Module_%M && ..\.venv\Scripts\python.exe -m pytest -q"
cmd /c "cd Pipeline_Runner && ..\.venv\Scripts\python.exe -m pytest -q"
```

The 19 October 2026 upload-copy verification passed 194 tests plus 12 subtests
and three live full-chain cases; see the [verification summary](Code_git/Pipeline_Runner/verification/2026-10-19.json).
Live results depend on the source websites.
Discovery is bounded and institution coverage is incomplete. External
Presentation 2 AnnotationLists and external Presentation 3 AnnotationPages
are not yet fully traversed for reference-text enrichment. Runtime AI API
integration is not implemented: current recipes were investigated with AI
assistance and are executed using deterministic code and configuration.

Source code, configurations, schemas, knowledge notes, and tests are included.
Virtual environments, harvested datasets, downloaded images, raw-response
caches, local logs, and personal project documents are excluded from Git.
Module READMEs contain additional implementation and configuration details.
