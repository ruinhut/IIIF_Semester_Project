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
| `store.py` | JSONL, CSV, and text persistence |
| `pipeline.py` | Configuration, orchestration, deduplication, and logging |
| `cli.py` | Command-line interface |

## Technical references

- [IIIF Change Discovery API 1.0](https://iiif.io/api/discovery/1.0/)
- [IIIF Presentation API 3.0](https://iiif.io/api/presentation/3.0/)
- [IIIF Presentation API 2.1](https://iiif.io/api/presentation/2.1/)

