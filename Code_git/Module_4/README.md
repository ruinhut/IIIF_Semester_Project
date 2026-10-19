# Module 4: IIIF Manifest Fetcher and Structural Validator

Module 4 consumes the deduplicated Manifest URL handoff from Module 3. It
downloads each Manifest, preserves the exact parseable JSON response in a local
cache, validates basic IIIF Presentation structure, and exports page/image
references for rights filtering and OCR selection.

It does not discover new resources, decide whether rights permit use, normalize
descriptive metadata, download full image files, or run OCR.

## Input

The default input is:

~~~text
../Module_3/data/output/manifest_urls.jsonl
~~~

Each JSONL record must contain Module 3's stable manifest_id and manifest_url.
Provider identities and discovery evidence are preserved unchanged.

## Processing

For every selected record, Module 4:

1. reuses the cached raw JSON unless force refresh is requested;
2. otherwise sends a bounded HTTP request with redirects, retries, timeout,
   response-size limit, Accept header, and an academic User-Agent;
3. parses JSON and preserves the exact response bytes plus SHA-256 checksum;
4. checks that the root declares Manifest and has id or @id;
5. recognizes Presentation API 3 items/Canvas structure or Presentation API 2
   sequences/canvases structure;
6. inventories Canvas labels, image bodies, Image Services, auxiliary files,
   and top-level rights/license values;
7. classifies the record as valid, manual_review, invalid, or unavailable.

Missing context, no usable Canvas, or no image body goes to manual review.
Wrong resource type, malformed required structure, and invalid JSON go to the
invalid output. Network and HTTP failures remain separately auditable.

## Outputs

### Missing source identifiers

`normalization.infer_missing_manifest_id` defaults to `true`. If a response
declares an IIIF Presentation Manifest and lacks its top-level `id`/`@id`,
Module 4 may infer only that identifier from the successful final retrieval
URL. Original bytes remain unchanged. A separate `.normalized.json`,
`source_structural_validation` and `structural_normalization` preserve the
source error, patch and evidence. No Canvas, image or descriptive content is
invented. Set the option to `false` for strict source rejection. A valid
normalized result means basic project checks passed, not full IIIF conformance.

Explicitly imported Module 3 HTTP snapshots may be reused as cache; their
metadata retains the original retrieval time and import trace. A cache hit
must not be reported as an independent new HTTP request.

Runtime files are written under data/ and ignored by Git except placeholders:

- data/raw_manifests/<manifest_id>.json - exact parseable response bytes;
- data/raw_manifests/<manifest_id>.meta.json - request metadata;
- data/output/validated_manifests.jsonl - valid handoff for Module 5;
- data/output/manifest_resource_inventory.jsonl - one row per Canvas/body;
- data/output/manifest_resource_inventory.csv - spreadsheet form;
- data/output/manual_review.jsonl - Manifest-like records needing review;
- data/output/invalid_manifests.jsonl - JSON or structure failures;
- data/output/unavailable_manifests.jsonl - HTTP and network failures;
- data/log/Module4_YYYY-MM-DD_HH-MM-SS_log.txt - run summary.

The resource inventory contains provider names, rights values, Canvas identity
and order, body URL/type/format, and Image Service URLs. Module 5 must still
apply the agreed rights policy before formal downstream use.

## Run

From Code_git/Module_4:

~~~powershell
python -m iiif_manifest_validator run --config config.example.json
~~~

Bounded smoke run:

~~~powershell
python -m iiif_manifest_validator run --config config.example.json --limit 5
~~~

Ignore cached responses and request the selected records again:

~~~powershell
python -m iiif_manifest_validator run --config config.example.json --limit 5 --force-refresh
~~~

A five-provider public sample is available through config.smoke.json.

## Test

Canvas identifiers retain their URI fragments, such as `#canvas`. These
fragments distinguish logical resources and are not removed like fragments
on HTTP retrieval URLs. Raw publisher responses remain unchanged.

~~~powershell
python -m unittest discover -s tests -v
~~~

The tests use a local HTTP server and cover Presentation 2 and 3, Choice image
bodies, redirects, HTTP restrictions, response-size limits, invalid JSON,
wrong resource types, manual-review conditions, output classification, and
cache reuse.

## Implementation structure

| Path | Responsibility |
|---|---|
| iiif_manifest_validator/models.py | Module 3 contract, stable IDs, result models |
| iiif_manifest_validator/fetch.py | Bounded HTTP retrieval and error classification |
| iiif_manifest_validator/validator.py | Presentation 2/3 checks and media inventory |
| iiif_manifest_validator/store.py | Raw JSON, JSONL, CSV, and log persistence |
| iiif_manifest_validator/pipeline.py | Configuration, cache, orchestration, and outputs |
| iiif_manifest_validator/cli.py | Command-line interface |
| tests/ | Deterministic unit and integration tests |

## Git policy

Source code, tests, documentation, example configurations, and small sample
inputs are tracked. Downloaded raw Manifests, generated outputs, logs, caches,
and credentials are not tracked. Python source files are never globally
ignored.
