# Module 5 — Rights Identification and Research-Retention Policy

Module 5 reads structurally valid IIIF Manifests from Module 4, extracts rights evidence, normalizes it, and applies a versioned policy.

The schema 2.0 contract separates two questions:

1. May the project retain the URL and metadata and use them for academic analysis?
2. Is the resource eligible for public distribution or commercial reuse?

Every processed record is retained for research and sent downstream. The policy decision `allow` or `exclude` applies only to public reuse.

## Rights states

| Category | Public-reuse decision | Research downstream |
|---|---|---|
| `public_domain` | `allow` | retained |
| `open_license` | `allow` | retained |
| `noncommercial_or_limited` | `exclude` | retained |
| `in_copyright` | `exclude` | retained |
| `no_known_copyright` | `exclude` | retained |
| `institutional_terms` | `exclude` | retained |
| `unknown` | `exclude` | retained |
| `conflicting` | `exclude` | retained |

An `exclude` decision therefore means “excluded from the public-reuse subset,” not “deleted from the pipeline.”

Each assessment records:

- the original and normalized rights evidence;
- the JSON path and resource scope of each value;
- `decision_scope: public_reuse`;
- `research_status: retained`;
- URL/metadata retention and academic-analysis permissions;
- public-distribution and commercial-use eligibility;
- policy version, rule, reason codes, provider and Manifest provenance.

## Inputs

- `../Module_4/data/output/validated_manifests.jsonl`
- `../Module_4/data/output/manifest_resource_inventory.jsonl`
- raw Manifest JSON files cached by Module 4

Only structurally valid Module 4 schema 1.0 records are processed.

## Outputs

- `research_manifests.jsonl`: every processed Manifest and its full rights assessment; canonical Module 6 input.
- `research_only_manifests.jsonl`: records retained for research but excluded from public reuse.
- `reuse_eligible_manifests.jsonl`: records eligible for public reuse.
- `research_resource_inventory.jsonl/csv`: all resource rows retained for research; canonical Module 6 input.
- `reuse_eligible_resource_inventory.jsonl/csv`: the public-reuse-eligible resource subset.
- `rights_summary.csv`: one audit row per Manifest.
- `data/log/Module5_<local-time>_log.txt`: counts, policy and output paths.

Operational evidence failures remain in `research_manifests.jsonl` with their URL, metadata and failure reason. They are not public-reuse eligible.

## Run

```powershell
python -m iiif_rights_filter run --config config.example.json
python -m iiif_rights_filter run --config config.smoke.json
python -m iiif_rights_filter run --config config.example.json --limit 20
```

## Test

```powershell
python -W error::ResourceWarning -m unittest discover -s tests -v
```
