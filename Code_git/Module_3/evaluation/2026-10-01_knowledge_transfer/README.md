# 2026-10-01 knowledge-transfer evaluation

This evaluation contains two institutions that were unresolved in the
2026-09-28 full run:

- EPFL Plume: the institution used to derive the investigation and discovery
  skill;
- Art Institute of Chicago: a held-out institution with a different API shape,
  used to test transfer of the same Python skill through configuration only.

Run from this directory:

```powershell
python prepare_cases.py
python -m iiif_resource_discovery run --config config.json
```

To verify the Module 4 handoff, run from `Code_git/Module_4`:

```powershell
python -m iiif_manifest_validator run --config ../Module_3/evaluation/2026-10-01_knowledge_transfer/module4_config.json
```

The run is intentionally bounded to ten identifiers and ten Manifests per
provider. It tests resolution and transfer, not complete institutional harvest.
The Art Institute recipe keeps the institution's documented one-request-per-
second delay.

## Observed result

The Module 3 run at `2026-10-01T21:11:04+02:00` processed both providers and
validated 20 unique Manifest URLs: ten from EPFL Plume and ten from the Art
Institute of Chicago. Both providers were resolved by the knowledge skill and
both carry a truncation flag because the configured ten-Manifest evaluation
limit was reached.

The Module 4 handoff run at `2026-10-01T21:11:42+02:00` classified all 20
Manifests as valid and inventoried 5,570 Canvases, 5,570 image bodies, and
5,570 Image Services. The timestamped logs under `log/` and `module4_log/`
contain the reproducible counts.
