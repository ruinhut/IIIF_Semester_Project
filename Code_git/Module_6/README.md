# Module 6 — Metadata Extraction and Normalization

Module 6 reads every research-retained Manifest and resource row produced by Module 5. This includes public-reuse-eligible, unknown-rights and restricted records.

It preserves every original IIIF metadata entry and maps recognizable values into stable core fields: identifier, title, description, creator, date, place, subject, type, language, rights and source. Rights restrictions remain attached to each normalized record and resource so Module 7 can keep research-only data separate from public-reuse data.

## Inputs

- `research_manifests.jsonl`: all Module 5 records with `research_status = retained`.
- `research_resource_inventory.jsonl`: all resources allowed for academic analysis.
- Module 4 raw Manifest files, read in their current local form.

## Outputs

- `normalized_records.jsonl`
- `normalized_resources.jsonl`
- `normalized_reference_texts.jsonl`: provider-declared OCR/transcription links,
  including their Manifest, Canvas, provider, format and alignment scope

- `metadata_summary.csv`
- `normalized_resources.csv`
- `failed_records.jsonl`
- `data/log/Module6_<local-time>_log.txt`

Normalization is conservative. Missing or ambiguous values are retained and marked partial; they are never invented or silently discarded.

### Optional public-catalogue reference enrichment

`provider_reference_sources` may point to reviewed provider configuration such
as `config/provider_reference_sources.json`. The generic enrichment reads
original-language transcription from a public item API when the Manifest does
not declare it. It caches the original JSON and preserves the exact text and
language field paths in provenance. It never substitutes an English
translation for an original-language OCR reference.

Current alignment requires one Canvas, one image body, one catalogue page,
and an image identifier matching the actual declared body/service URL.
Multi-page document text and ambiguous image matches are skipped with an
audited reason; valid image metadata remains available. Institutional text is
a reference candidate, not automatically manually corrected ground truth.
`catalogue_reference_audit.jsonl` records extraction, skips and failures.
`catalogue_reference_cache_directory` selects an explicit saved public-item
snapshot. A reviewed source may set `cache_only: true` for a reproducible
offline enrichment pass; absent item records are reported as
`not_in_selected_catalogue_snapshot`, not treated as evidence that the
institution has no transcription.

## Run and test

```powershell
python -m iiif_metadata_normalizer run --config config.example.json
python -m pytest -q
```
