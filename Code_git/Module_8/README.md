# Module 8: Linked Image Downloader

If a declared body URL is stale or requests an unsupported image format,
Module 8 can read the image's declared IIIF `info.json`, validate its Image API
context and dimensions, and request JPEG through that service. The algorithm
is provider-independent and retains the failed URL and every fallback attempt
in `download_index.jsonl`. Authentication failures are not treated as URL repairs.

The bundle's `common_media.json` records the URL and MIME type actually used;
`image.source_id` preserves the original identifier. Cached reruns preserve the
previously verified URL. The three successful live transfer cases from
2026-10-15 are Göttingen, Leiden and the National Library of Wales.

Module 8 downloads the image URLs exported by Module 7. Every successfully
downloaded image is packaged with the three JSON records needed to interpret
it independently:

- `common_record.json`: the Manifest-level common record;
- `common_media.json`: the exact Canvas/image record;
- `ocr_document_profile.json`: the Manifest-level OCR profile.
- `institution_reference_texts.json`: declarations and download provenance for
  provider-supplied OCR/transcription linked to this image, when available;
- `institution_reference_001.*` and `institution_reference_001.txt`: the
  original structured reference (for example hOCR) and a plain-text view.

The module does not discover new Manifests, change rights decisions, or run
OCR. It consumes the validated Module 7 handoff and preserves its identifiers
and rights flags.

## Input

The configuration points to these Module 7 JSONL files:

- `common_records.jsonl`
- `common_media.jsonl`
- `ocr_document_profiles.jsonl`
- `institution_reference_texts.jsonl` (optional; required when
  `require_reference_text` is true)

Rows are joined by `record_id`. The image URL comes from
`common_media.image.download_url`, with `image.id` as a compatibility fallback.
By default, only rows with `academic_analysis_allowed: true` are eligible.
This includes research-retained records whose rights category is unknown or
restricted when Module 7 explicitly permits academic analysis.

## The only two download commands

From `Code_git/Module_8`:

```powershell
python -m iiif_image_downloader download-example --config config.example.json
python -m iiif_image_downloader download-all --config config.example.json
```

`download-example` tries eligible rows in deterministic input order until one
image succeeds. `download-all` attempts every eligible row. Existing valid
image bundles are reused unless `overwrite_existing` is enabled in the
configuration.

Every run is partitioned into `with_reference/`, `without_reference/`, and
`reference_failed/`. A bundle enters `with_reference/` only after at least one
linked institutional OCR/transcription resource has been downloaded. Set
`require_reference_text` to true when producing a training-only sample.

## Validation and safeguards

- follows HTTP redirects;
- applies timeouts, bounded retries and exponential backoff;
- downloads sequentially with a configurable delay;
- enforces a maximum image size;
- accepts only recognized raster-image bytes, so JSON, HTML and Image API
  `info.json` responses cannot be mistaken for image files;
- writes through a temporary file and renames only after validation;
- records failures and skipped rows without silently discarding them.

## Output

Example mode writes under `data/output/example/`; all mode writes under
`data/output/all/`. A successful image bundle has this form:

```text
<record_id>/
  <sequence>_<resource_id>/
    image.jpg
    common_record.json
    common_media.json
    ocr_document_profile.json
```

Each mode also writes:

- `download_index.jsonl`: one row per downloaded or reused image;
- `failed_downloads.jsonl`: request and validation failures;
- `skipped_downloads.jsonl`: ineligible or missing-URL rows;
- `download_summary.json`: counts, byte total and run status.

A timestamped text log is written to `data/log/`.

Index `image_path` and `bundle_directory` values are relative to the configured
`output_directory`, including the `all/` or `example/` prefix. This base stays
the same when an existing image is reused on a later run.

## Tests

```powershell
python -m pytest -q
```

The tests use a local HTTP server. They cover valid images, misleading JSON
responses, size limits, Module 7 linkage, example/all behavior, portable JSON
bundles and resumable reuse. They do not contact live institutions.
