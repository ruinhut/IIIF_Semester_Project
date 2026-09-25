# Module 5 — IIIF Rights Identification and Filtering

Module 5 reads the structurally valid IIIF Manifests produced by Module 4, preserves rights evidence from the original JSON, maps it to stable categories, and applies a versioned project policy. Only resources whose Manifest receives an `allow` decision are exported downstream. The result is an auditable project decision, not a legal determination.

## Scope

The module:

- reads Module 4's validated Manifest JSONL, resource inventory, and cached raw JSON;
- verifies cached JSON against Module 4's SHA-256 when enabled;
- extracts `rights` and `license` at Manifest, Canvas, Annotation, and Body levels;
- retains rights-labelled metadata, `requiredStatement`, and legacy `attribution`;
- records original and normalized values, JSON path, resource scope, category, and matched rule;
- distinguishes decisive rights evidence from attribution-only notices;
- applies a versioned JSON policy and routes uncertain cases to manual review;
- exports page/image rows only for allowed Manifests.

It does not discover resources, fetch Manifests, validate Presentation structure, download images, run OCR, or normalize descriptive metadata.

## Inputs

The default configuration consumes:

- `../Module_4/data/output/validated_manifests.jsonl`
- `../Module_4/data/output/manifest_resource_inventory.jsonl`
- cached raw JSON paths recorded by Module 4

Only Module 4 schema 1.0 records with `structural_validation.status: "valid"` are accepted.

## Baseline policy

The tracked policy is `policies/baseline-2026-09-25.json`.

| Category | Examples | Decision |
|---|---|---|
| `public_domain` | CC0, Public Domain Mark | allow |
| `open_license` | CC BY, CC BY-SA | allow |
| `noncommercial_or_limited` | CC BY-NC, CC BY-ND, NoC-NC and other limited NoC statements | review |
| `in_copyright` | InC family, explicit “all rights reserved” | deny |
| `no_known_copyright` | NKC and equivalent wording | review |
| `institutional_terms` | unrecognized provider terms | review |
| `unknown` | no decisive evidence or unreadable raw evidence | review |
| `conflicting` | incompatible decisive categories | review |

This conservative allowlist still requires supervisor confirmation. Add a new versioned policy file when behavior changes; do not silently rewrite a policy used by a recorded run. RightsStatements.org entries are descriptive statements rather than licenses and use the canonical `/vocab/` URI. See the [RightsStatements FAQ](https://rightsstatements.org/en/documentation/faq) and [Creative Commons license guide](https://creativecommons.org/share-your-work/use-remix/cc-licenses/).

## Run

From `Code_git/Module_5`:

```powershell
python -m iiif_rights_filter run --config config.example.json
python -m iiif_rights_filter run --config config.smoke.json
python -m iiif_rights_filter run --config config.example.json --limit 20
```

## Outputs

Generated data under `data/output` and run logs under `data/log` are ignored by Git.

- `rights_assessed_manifests.jsonl`: every Manifest with full evidence audit;
- `allowed_manifests.jsonl`: policy-approved Manifests;
- `denied_manifests.jsonl`: explicit policy denials;
- `manual_review.jsonl`: uncertain, limited, local, conflicting, or unreadable cases;
- `allowed_resource_inventory.jsonl/csv`: Module 4 resources belonging to allowed Manifests;
- `rights_summary.csv`: one compact row per Manifest;
- `Module5_YYYY-MM-DD_HH-MM-SS_log.txt`: configuration, counts, and paths.

Each `rights_assessment` retains `category`, `decision`, `policy_version`, `policy_rule`, `effective_categories`, `reason_codes`, and every evidence item's `evidence_type`, `json_path`, `raw_value`, `normalized_value`, `category`, `matched_rule`, `decisive`, and resource scope.

## Validation

```powershell
python -W error::ResourceWarning -m unittest discover -s tests -v
```

Verified on 25 September 2026:

- 14/14 automated tests passed;
- five cached real Manifests from BSB, Gallica, Harvard Art Museums, Digital Commonwealth, and Fragmentarium were processed and their SHA-256 values verified;
- decisions: 1 allow and 4 review;
- categories: one each for open license, noncommercial/limited, no known copyright, institutional terms, and unknown;
- the allowed Fragmentarium CC BY Manifest yielded 3 page/image rows.
