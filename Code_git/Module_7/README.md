# Module 7 — Common-Schema Validator and Exporter

Module 7 converts Module 6 output into a versioned, validated delivery bundle. The current profile is deliberately provisional because the team common schema has not yet been supplied. The mapping is isolated here, so replacing the profile does not require changes to Modules 1–6.

The export uses two linked tables:

1. **Object records** — one row per IIIF Manifest, with identifier, descriptive metadata, normalized date/place values, rights, source, quality, and provenance.
2. **Media records** — one row per Canvas/image, linked to its object through `record_id`, with the direct image and IIIF Image API service URLs.

Only records explicitly allowed by Module 5 reach this module. Invalid rows are written to rejection files with machine-readable issue paths. Duplicate IDs and media records without a valid parent are rejected. Every delivery file is listed with its byte count and SHA-256 checksum in `dataset_manifest.json`.

## Run

```powershell
cd Code_git/Module_7
python -m pip install -e .
python -m iiif_common_exporter run --config config.example.json
python -m pytest -q
```

## Output bundle

- `common_records.jsonl` and `common_records.csv`
- `common_media.jsonl` and `common_media.csv`
- `rejected_records.jsonl` and `rejected_media.jsonl`
- `dataset_manifest.json`
- `data/log/Module7_<local-time>_log.txt`

JSONL is the authoritative lossless format; CSV is provided for inspection and downstream tools. The tracked JSON Schema documents describe profile `provisional-0.1`.
