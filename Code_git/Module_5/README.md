# Module 5 — IIIF Rights Identification and Filtering

Module 5 is a fully automatic stage. It reads structurally valid IIIF Manifests from Module 4, preserves and classifies their rights evidence, applies a versioned allow/exclude policy, and exports only rights-cleared resources downstream. It creates no manual-review queue.

A missing rights statement means **unknown rights**, not public domain. The output therefore labels missing evidence as `unknown` / “Unknown rights” and automatically excludes it from the rights-cleared dataset. Only explicit public-domain or accepted open-license evidence is allowed.

## Scope

The module:

- reads Module 4's validated Manifest JSONL, resource inventory, and cached raw JSON;
- verifies cached JSON against Module 4's SHA-256 when enabled;
- extracts `rights` and `license` at Manifest, Canvas, Annotation, and Body levels;
- retains rights-labelled metadata, `requiredStatement`, and legacy `attribution`;
- records original and normalized values, JSON path, resource scope, category, and matched rule;
- distinguishes decisive rights evidence from attribution-only notices;
- assigns English and Chinese display labels;
- automatically assigns `allow` or `exclude`;
- exports page/image rows only for allowed Manifests.

It does not discover resources, fetch Manifests, validate Presentation structure, download images, run OCR, or normalize descriptive metadata.

## Inputs

The default configuration consumes:

- `../Module_4/data/output/validated_manifests.jsonl`
- `../Module_4/data/output/manifest_resource_inventory.jsonl`
- cached raw JSON paths recorded by Module 4

Only Module 4 schema 1.0 records with `structural_validation.status: "valid"` are accepted.

## Automatic policy

The tracked policy is `policies/automatic-2026-09-25.json`.

| Category | Display meaning | Decision |
|---|---|---|
| `public_domain` | Public domain | allow |
| `open_license` | CC BY or CC BY-SA | allow |
| `noncommercial_or_limited` | Restricted reuse | exclude |
| `in_copyright` | In copyright | exclude |
| `no_known_copyright` | No known copyright | exclude |
| `institutional_terms` | Institution-specific terms | exclude |
| `unknown` | No decisive rights information supplied | exclude |
| `conflicting` | Conflicting rights information | exclude |

Operational evidence failures, including missing raw JSON or checksum mismatch, are also automatically excluded. They can never be changed into `allow` by a category policy.

RightsStatements.org entries are descriptive statements rather than licenses and use the canonical `/vocab/` URI. See the [RightsStatements FAQ](https://rightsstatements.org/en/documentation/faq) and [Creative Commons license guide](https://creativecommons.org/share-your-work/use-remix/cc-licenses/).

## Run

From `Code_git/Module_5`:

```powershell
python -m iiif_rights_filter run --config config.example.json
python -m iiif_rights_filter run --config config.smoke.json
python -m iiif_rights_filter run --config config.example.json --limit 20
```

## Outputs

Generated data under `data/output` and logs under `data/log` are ignored by Git.

- `rights_assessed_manifests.jsonl`: every processed Manifest, including excluded records and complete evidence;
- `allowed_manifests.jsonl`: Manifests accepted by the active policy;
- `excluded_manifests.jsonl`: every automatically excluded Manifest and its reason;
- `allowed_resource_inventory.jsonl/csv`: Module 4 resources belonging to allowed Manifests;
- `rights_summary.csv`: one compact row per Manifest, including English and Chinese labels;
- `Module5_YYYY-MM-DD_HH-MM-SS_log.txt`: configuration, policy, counts, and paths.

Each `rights_assessment` retains `category`, `decision`, bilingual `display_label`, `policy_version`, `policy_rule`, `effective_categories`, `reason_codes`, and every evidence item's exact source information.

## Validation

```powershell
python -W error::ResourceWarning -m unittest discover -s tests -v
```

The five-Manifest integration sample is expected to produce 1 allowed and 4 automatically excluded Manifests. Fragmentarium is allowed by CC BY and supplies 3 downstream page/image rows. BSB NoC-NC, Digital Commonwealth no-known-copyright wording, Gallica institutional terms, and Harvard unknown rights remain fully recorded but are excluded.
