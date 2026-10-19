# Module 7 — Common-Schema and OCR Handoff Exporter

Module 7 validates Module 6 data and exports a versioned delivery bundle. It keeps the existing object and media outputs and adds an OCR-oriented handoff for Arsha's engine selection and ground-truth planning. The current common schema remains provisional because the team's final schema has not yet been supplied.

The export contains:

1. **Object records** — one row per IIIF Manifest.
2. **Media records** — one row per Canvas/image, linked through `record_id`.

Each media record distinguishes the provider-supplied image identifier from a
directly retrievable image URL. `image.source_id` preserves the original
Presentation body ID, `image.service_urls` preserves IIIF Image API service
bases, `image.info_json_url` describes the service, and `image.download_url`
(also exposed as `image.id`) is the URL to use when downloading image bytes.
This distinction matters because opening an Image API service base commonly
returns `info.json` rather than an image.

All Module 5 records retained for research may reach Module 7. Each object and media row keeps:

- rights category and public-reuse decision;
- `research_status`;
- academic-analysis permission;
- public-distribution and commercial-use flags;
- `public_reuse_eligible`.

Research-only records are valid output records. Their restriction flags prevent them from being mistaken for the public-reuse subset.

Invalid structures, duplicate IDs and orphan media rows are written to rejection files. `dataset_manifest.json` records output counts, byte sizes and SHA-256 checksums.

## OCR handoff

For every Manifest, the OCR profile records reported languages, normalized dates and centuries, explicit scripts, document types, and a metadata-based production category: `printed`, `handwritten`, `mixed`, `visual_or_non_textual`, or `unknown`. It also keeps the Manifest URL, provider, media count, rights, and explicit mentions of Fraktur, blackletter, long s, or ligatures.

The module does not infer missing facts. Image-dependent conditions such as microfilm, bleed-through, damaged pages, blur, skew, and low contrast are marked `unknown` with status `not_assessed_no_image_pixels`. They require a later pixel-level sample inspection.

Ground-truth candidates are selected deterministically to cover different providers, production methods, languages, centuries, scripts, and reported typeface features. `metadata_supported_ocr_candidate` means that metadata identifies printed, handwritten, or mixed material; `visual_triage_required` means that the page should be viewed before admission to a ground-truth set. These rows are page candidates, not completed transcriptions.

## Run

```powershell
python -m iiif_common_exporter run --config config.example.json
python -m pytest -q
```

## Output bundle

- `common_records.jsonl/csv`
- `common_media.jsonl/csv`
- `rejected_records.jsonl`
- `rejected_media.jsonl`
- `ocr_document_profiles.jsonl/csv`: one OCR profile per Manifest
- `ocr_dataset_summary.json`: aggregate language, century, script, production-method, and coverage counts
- `ocr_ground_truth_candidates.jsonl/csv`: representative pages with Manifest, Canvas, image, and Image API references
- `institution_reference_texts.jsonl`: provider-supplied OCR/transcription
  resources linked to the exact `common_media.resource_id`. These are reference
  labels, not an automatic claim of manually corrected gold truth.
- `dataset_manifest.json`
- `data/log/Module7_<local-time>_log.txt`

JSONL is the authoritative lossless format. CSV is provided for inspection.

The candidate sample is controlled by `ocr_profile` in the configuration: `max_ground_truth_records`, `pages_per_record`, and `max_records_per_provider`.
