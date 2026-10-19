# Module 3: IIIF Endpoint Resolution and Resource Discovery

Module 3 converts checked provider candidates into a deduplicated list of IIIF
Manifest URLs. It has two internal stages:

1. **Endpoint resolution** — use confirmed JSON responses, curated mappings,
   declared HTML links, embedded JSON-LD, and a bounded same-site crawl to find
   machine-readable IIIF entry points.
2. **Resource discovery** — traverse Change Discovery Activity Streams and
   Presentation API Collections, or accept a directly declared Manifest.

This module discovers resource URLs. It does not download and structurally
validate every Manifest; that is Module 4.

## Schema 2.1: provider-level discovery with reusable knowledge

Module 3 groups Module 2 rows by `provider_id` and processes every checked
route under one institution-level result. It attempts parseable JSON routes,
bounded HTML discovery, Change Discovery streams, Presentation Collections,
and explicit IIIF links found in provider-specific JSON APIs. Presentation
Collection `next` pagination is followed within the collection limit. A
provider succeeds when at least one route yields a Manifest; other route
outcomes remain in its audit report.

Schema 2.1 adds a persistent knowledge layer for providers whose public entry
points do not directly expose a Manifest, Collection, or Change Discovery
stream. A provider recipe supplies verified site facts, while a reusable skill
implements the discovery algorithm. The current generic skill paginates a JSON
API, extracts stable record identifiers, applies optional record filters, builds
candidate Manifest URLs from templates, and validates each candidate as IIIF
Presentation JSON. Skill attempts and outcomes are preserved in each provider's
audit record.

## Input

The default input is Module 2's complete checked-provider file:

```text
../Module_2/data/output/checked_entry_points.jsonl
```

Module 2 records remain unchanged inside each provider report. The optional
curated mapping is:

```text
config/provider_endpoints.json
```

The optional discovery knowledge base is:

```text
config/discovery_knowledge.json
```

The official-guide evidence library is stored separately:

```text
config/official_guide_knowledge.json
```

It contains the documented resource-finding operations for all 69 visible
provider/resource entries in the official IIIF guide index at source revision
`c94b51bc335c6050667a536f2ba737807b92f8dc`. These records are investigation
evidence and candidate skills. They are not executed automatically. A provider
recipe moves to `discovery_knowledge.json` only after its HTTP, JSON and IIIF
chain has been validated. The readable provider-by-provider index is
`knowledge/official_guides/provider_skill_inventory.md`.

Each knowledge entry links an institution to one or more generic skills. A
recipe may declare an item-list API, the JSON path containing its records, the
identifier field, an availability filter, and one or more Manifest URL
templates. Provider-specific URLs stay in configuration rather than Python
branches.

One curated entry has this shape:

```json
{
  "provider_id": "provider-example",
  "provider_name": "Example Library",
  "entry_points": ["https://example.org/iiif/activity/all-changes"],
  "html_seeds": ["https://example.org/digital-collections"]
}
```

`provider_id` is preferred; an exact case-insensitive `provider_name` is the
fallback. Curated URLs are still fetched and type-checked rather than trusted
without validation.

## Discovery rules

### Change Discovery

- `OrderedCollection` starts at `last` when available and walks backwards by
  `prev`, following the official incremental-processing direction.
- `OrderedCollectionPage.orderedItems` supplies resource references.
- `Create`, `Update`, `Add`, and `Move` can add current resources.
- `Delete` and `Remove` are preserved as stream semantics but do not produce
  Manifest harvest targets.

### Presentation Collections

- Presentation API 3 `items` and Presentation API 2 `manifests`, `collections`,
  and `members` are supported.
- Child Collections are traversed within the configured limit.
- Manifest URLs are deduplicated while retaining all provider and discovery
  evidence.

### HTML fallback

For a Module 2 `reachable_non_json` record, the resolver can inspect:

- explicit Manifest or IIIF data attributes;
- typed `<link>` declarations;
- typed JSON-LD blocks;
- strongly indicated IIIF, collection, viewer, object, or record links on a
  small number of same-site pages.

Every candidate is fetched and must decode to a recognized `Manifest`,
`Collection`, `OrderedCollection`, or `OrderedCollectionPage`. The crawler is
bounded by page depth, pages, candidate URLs, response size, and Manifest count.
It does not treat arbitrary HTML metadata as IIIF.

### Knowledge-assisted discovery

Knowledge skills run after direct machine-readable routes and before the noisy
HTML fallback. The first reusable skill is
`paginated_json_identifiers_to_manifest_templates`:

1. request a bounded institutional list API;
2. traverse the configured JSON record path and pagination convention;
3. select usable records from declarative filters;
4. extract stable identifiers;
5. render one or more Manifest URL templates;
6. fetch and validate candidates as Presentation 2 or 3 Manifests.

The investigation method is documented in `knowledge/discovery_playbook.md`.
Institution case reports record the evidence used to create each recipe, while
`knowledge/skills/` documents the reusable algorithm separately. This lets a
new institution with the same structural pattern use configuration alone.

Official IIIF guide operations are imported with
`tools/import_official_guide_knowledge.py`. The importer preserves the official
text, screenshots, links, checked date and source Git revision, then maps each
provider to candidate skills without claiming that those candidates already
work at catalogue scale.

## Outputs

Files are written to `data/output/`:

- `provider_discovery.jsonl` — one complete audit report per provider;
- `resolved_endpoints.jsonl` — confirmed machine-readable IIIF resources;
- `manifest_urls.jsonl` — deduplicated Manifest URLs for Module 4;
- `unresolved_providers.jsonl` — providers for which no Manifest was found;
- `provider_discovery.csv` — human-readable provider summary.

The canonical Module 4 handoff record contains:

- stable `manifest_id`;
- canonical `manifest_url`;
- provider identities;
- every discovery method, source URL, activity type, and activity time observed;
- `module_3_schema_version`.

Timestamped logs are written to:

```text
data/log/Module3_YYYY-MM-DD_HH-MM-SS_log.txt
```

## Run

From the `Module_3` directory:

```powershell
python -m iiif_resource_discovery run --config config.example.json
```

For a bounded provider smoke run:

```powershell
python -m iiif_resource_discovery run --config config.example.json --limit 5
```

The configured limits and the `truncated` field make partial discovery explicit.

## Test

```powershell
python -m unittest discover -s tests -v
```

Tests use a local HTTP site with Activity Stream pages, Presentation 2 and 3
Collections, Manifests, HTML declarations, embedded JSON-LD, duplicate URLs,
deleted activities, malformed JSON, and pages without IIIF evidence.

## Implementation structure

| Path | Responsibility |
|---|---|
| `models.py` | Input validation, provenance, stable IDs, and output records |
| `fetch.py` | Bounded HTTP and JSON retrieval |
| `html_discovery.py` | Declared-link extraction and bounded HTML crawl |
| `discovery.py` | Activity Stream and Collection traversal |
| `knowledge.py` | Load and match versioned provider knowledge |
| `skills.py` | Execute reusable, configuration-driven discovery skills |
| `official_guide_knowledge.py` | Import and validate official guide evidence and candidate skills |
| `store.py` | JSONL, CSV, and text persistence |
| `pipeline.py` | Configuration, orchestration, deduplication, and logging |
| `cli.py` | Command-line interface |

## Bounded live knowledge-transfer evaluation

The 2026-10-01 evaluation in
`evaluation/2026-10-01_knowledge_transfer/` used two previously unresolved
providers:

- **EPFL Plume** was the investigation case. Its Omeka S item API and two
  documented IIIF Manifest route patterns were encoded as a provider recipe.
- **Art Institute of Chicago** was a transfer case. The same generic skill was
  reused with a different API shape, pagination keys, filter, and URL template;
  no provider-specific Python code was added.

Module 3 resolved both providers and validated 20 Manifest URLs in total under
an intentional limit of ten per provider. A Module 4 handoff then validated all
20 Manifests and inventoried 5,570 Canvases, image bodies, and Image Services.
These counts demonstrate bounded transfer of the method; they are not complete
institutional harvest totals.

## Technical references

The 2026-10-15 provider investigation is recorded in
`knowledge/institutions/2026-10-15_provider_routes.md`. New reusable catalogue
skills extract declared Manifest URLs from paginated JSON or identifiers from
targeted HTML listings; Collection traversal supports `first` as well as `next`.
Executable recipes retain the existing EPFL and Chicago knowledge. Live results
and per-provider failures are kept in the isolated evaluation directory, not
mixed into the production outputs. These are bounded samples, not full harvests.

The subsequent five-provider completion is documented in
`knowledge/institutions/2026-10-15_five_provider_completion.md`. Its isolated
evaluation validates 100 Manifests and completes five real linked-image
downloads through Modules 5-8. Exact source batches and failures are retained
under `evaluation/2026-10-15_five_provider_completion/`; no production output
directory is replaced by these samples.

- [IIIF Change Discovery API 1.0](https://iiif.io/api/discovery/1.0/)
- [IIIF Presentation API 3.0](https://iiif.io/api/presentation/3.0/)
- [IIIF Presentation API 2.1](https://iiif.io/api/presentation/2.1/)
- [Omeka S REST API](https://omeka.org/s/docs/developer/api/rest_api/)
- [Omeka S IIIF Presentation module](https://omeka.org/s/docs/developer/module_docs/IiifPresentation/)
- [Omeka S IIIF Server module](https://omeka.org/s/modules/IiifServer/)
- [Art Institute of Chicago API](https://api.artic.edu/docs/)

## Reviewed POST search and larger catalogues

Catalogue recipes also support explicitly reviewed read-only POST requests,
JSON-body pagination and catalogue-only headers. A configured `total_path`
detects a short page before the source's declared total instead of silently
claiming complete enumeration. See
[`knowledge/skills/public_post_search_and_pagination.md`](knowledge/skills/public_post_search_and_pagination.md).

Discovery evidence uses a set index rather than repeatedly scanning all earlier
findings. Distinct sources are preserved while Manifest counts remain unique
by URL. The Blavatnik investigation and current source limitations are recorded
in [`knowledge/institutions/2026-10-16_blavatnik.md`](knowledge/institutions/2026-10-16_blavatnik.md).
