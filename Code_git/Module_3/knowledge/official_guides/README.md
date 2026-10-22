# Official IIIF Resource-Guide Knowledge

`config/official_guide_knowledge.json` preserves the human operations documented
by every visible provider entry in the official IIIF resource guides.  It also
maps those operations to a small set of reusable candidate discovery skills.

This file is documentary knowledge, not an allowlist of executable recipes.
An official screenshot showing a Manifest button proves that an item-level
route exists; it does not by itself provide a catalogue enumerator, stable URL
template, or validated API contract.  A candidate becomes executable only after
the institution investigation playbook verifies its entire HTTP/JSON/IIIF
chain and stores the resulting provider facts in `config/discovery_knowledge.json`.

## Stored evidence

Each provider record contains:

- the official guide URL, homepage, title and consortium status;
- concise action-bearing text and screenshot alt text;
- source hyperlinks and screenshot filenames;
- candidate generic skill identifiers;
- the dated status from the earlier Module 3 run;
- a validation state distinguishing official documentation from executable
  knowledge.

The generic skill catalogue covers filtered search enumeration, record-page
Manifest extraction, viewer configuration, identifier templates, catalogue
APIs, IIIF Collections, Wikidata P6108, Image API filename resolution and
legacy-platform review.

## Regeneration

From `Code_git/Module_3`, with a current checkout of `IIIF/guides`:

```powershell
python tools/import_official_guide_knowledge.py `
  --guides-repository <path-to-IIIF-guides> `
  --provider-census ../Module_1/data/output/providers.jsonl `
  --previous-results data/output/provider_discovery.jsonl `
  --executable-knowledge config/discovery_knowledge.json `
  --checked-date 2026-10-08 `
  --output config/official_guide_knowledge.json `
  --markdown-output knowledge/official_guides/provider_skill_inventory.md
```

The importer excludes non-provider tutorials and hidden guide pages, preserves
balanced parentheses in Markdown URLs, records the source Git revision and
validates all candidate skill references before writing UTF-8 JSON.

The 2026-10-08 import contains 69 visible provider/resource guides and nine
generic candidate skills. Five providers had already produced Manifests in the
earlier bounded baseline; EPFL Plume also has a separately validated executable
recipe. The remaining 63 records are official documentary candidates and must
not be reported as working automated harvesters yet.
