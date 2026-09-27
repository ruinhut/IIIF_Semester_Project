# Module 6 — Metadata Extraction and Normalization

Module 6 reads the rights-cleared Manifests and image inventory produced by Module 5. It preserves every original IIIF metadata entry and maps recognizable values into stable core fields: identifier, title, description, creator, date, place, subject, type, language, rights, and source.

Normalization is conservative. Missing or ambiguous date/place values are retained and marked as partial; they are never invented or silently discarded. Dates are normalized only when an explicit ISO date, year, year range, or century can be recognized. Place names are cleaned but not geocoded in this module.

## Run

```powershell
cd Code_git/Module_6
python -m pip install -e .
python -m iiif_metadata_normalizer run --config config.example.json
```

For the checked-in small sample, replace the last file with `config.smoke.json`.

## Inputs

- `allowed_manifests.jsonl`: Module 5 records with `rights_assessment.decision = allow`.
- `allowed_resource_inventory.jsonl`: rights-cleared Canvas/image rows.
- Module 4 raw Manifest files, verified against the SHA-256 stored in the handoff.

## Outputs

- `normalized_records.jsonl`: lossless normalized object records plus raw metadata provenance.
- `normalized_resources.jsonl`: one image/body row per resource with a stable `resource_id`.
- `metadata_summary.csv` and `normalized_resources.csv`: convenient review tables.
- `failed_records.jsonl`: unreadable, invalid, or checksum-failing records.
- `data/log/Module6_<local-time>_log.txt`: run counts and paths.

Run tests with `python -m pytest -q`.
