# Module 1: IIIF Provider Census and Selector

Module 1 builds a reproducible census of IIIF provider entry points and selects the institutions to process in a given pipeline run. It is the first stage of the modular IIIF harvesting pipeline developed for the EPFL DHLAB semester project *IIIF Document Information Extraction*.

This module does not harvest Manifests or determine whether every candidate entry point is a valid IIIF API. Those checks belong to Modules 2 and 3. Its responsibility is to collect provider candidates from documented sources, normalize them into one data model, deduplicate their entry points, preserve provenance, and produce an explicit run selection.

## Schema 2.0: provider identity and endpoint list

Each JSONL line represents one institution. The open-ended `endpoints` array
retains every route supplied by the source, with `url`, `endpoint_role`,
`discovery_type`, verification state, and source provenance. Its length is
dynamic. The legacy `discovery_endpoint` field remains as the first-route
projection for compatibility.

Records merge only through evidence such as a stable provider ID, the same
canonical institution URL, or an already shared endpoint. Equal names alone do
not merge institutions. The CSV contains one row per endpoint, while JSONL
keeps one complete institution object per line.

## Pipeline position

```text
IIIF Registry ───────────────┐
Official IIIF resource guide ┤
Awesome IIIF list ───────────┼─> normalized census ─> deduplication ─> run selection
Project-maintained entries ──┘                                      │
                                                                   ├─> providers.jsonl
                                                                   ├─> selected_providers.jsonl
                                                                   ├─> providers.csv
                                                                   └─> timestamped TXT log
```

The resulting `selected_providers.jsonl` is the handoff to Module 2, which checks network accessibility, redirects, response types, JSON parsing, and basic IIIF validity. Module 3 can then discover Manifest URLs from validated Change Discovery streams or IIIF Collections.

## Source catalogues

The default configuration combines four inputs:

1. **IIIF Registry** — the machine-readable registry of voluntarily registered Change Discovery streams: `https://registry.iiif.io/index.json`.
2. **Official IIIF resource guide** — a generated local snapshot of the resource entries published at `https://guides.iiif.io/finding_resources/`.
3. **Awesome IIIF implementations** — a generated local snapshot of the community-maintained list at `https://github.com/IIIF/awesome-iiif/blob/main/implementations.md`.
4. **Project-maintained entries** — additional records in `config/manual_providers.json`.

Registry registration is voluntary and therefore cannot be treated as a complete census of IIIF adoption. The official guide and Awesome IIIF provide broader candidate coverage, but most of their links are human-facing collection or implementation pages rather than confirmed Change Discovery endpoints. Module 1 preserves that distinction:

- `OrderedCollection` identifies a registered machine-readable discovery stream.
- `InstitutionWebsite` identifies an entry from the official resource guide that still requires validation.
- `ImplementationWebsite` identifies an Awesome IIIF entry that still requires validation.

Awesome IIIF contains institutions, content projects, demonstrations, and software tools. All entries are retained as candidates so that the import remains faithful to the source; downstream validation must determine which entries expose harvestable cultural-heritage resources.

## Provider record

Every input is normalized to a `ProviderRecord`. Its principal fields are:

| Field | Meaning |
|---|---|
| `provider_id` | Stable identifier derived from the canonical entry-point URL |
| `name` | Provider or implementation name reported by the source |
| `institution_url` | Human-facing institution or collection page |
| `discovery_endpoint` | Entry point to be examined by the next module |
| `discovery_type` | Registered stream type or unverified catalogue-entry type |
| `stream_label` | Human-readable description of the entry point |
| `collection_focus` | Collection scope when the source provides it |
| `estimated_size` | Reported resource count when available |
| `rights_status` / `rights_values` | Source-level rights observations, without making a harvesting decision |
| `record_status` | Whether the source currently presents the record as active or removed |
| `source` | Catalogue type, public source URL, entry page, activity type, and observation time |
| `raw_source_record` | Original input record retained for auditability |

Unknown values remain `null` or explicitly `unknown`; the program does not infer missing rights, scale, or endpoint capabilities.

## Requirements

- Python 3.10 or later
- No third-party runtime dependencies

## Running the census

Run these commands from the `Module_1` directory.

Select every active candidate currently known to the module:

```powershell
python -m iiif_provider_census run --config config.example.json --institution all
```

Select one institution by its exact name:

```powershell
python -m iiif_provider_census run `
  --config config.example.json `
  --institution "Bodleian Libraries, University of Oxford"
```

Select several institutions by repeating the option:

```powershell
python -m iiif_provider_census run `
  --config config.example.json `
  --institution "Biblissima" `
  --institution "Internet Archive"
```

Name matching is exact but case-insensitive. An unknown or inactive name causes a clear error and prints the available active names. The special value `all` must be used alone.

## Outputs

Exchange data is written to `data/output/`:

- `providers.jsonl` — complete normalized census after entry-point deduplication;
- `selected_providers.jsonl` — records selected for the current run and passed to Module 2;
- `providers.csv` — flattened table for human inspection.

Each JSONL line contains one complete provider record. JSONL is the canonical exchange format because records can be streamed and processed independently while retaining nested provenance and raw source data.

Operational logs are written separately to:

```text
data/log/Module1_YYYY-MM-DD_HH-MM-SS_log.txt
```

Each log records the computer-local run time, the institution selection, every configured source and its record count, counts before and after deduplication, and the output paths.

## Refreshing the catalogue snapshots

The two generated JSON files record the exact Git revision from which they were produced:

- `config/iiif_guides_providers.json`
- `config/awesome_iiif_providers.json`

After obtaining current local checkouts of `IIIF/guides` and `IIIF/awesome-iiif`, regenerate both inputs with:

```powershell
python tools/build_catalog_inputs.py `
  --guides-repository <path-to-IIIF-guides> `
  --awesome-repository <path-to-awesome-iiif> `
  --output-directory config
```

The builder converts the published catalogues into the Module 1 input schema. It does not perform network or IIIF conformance checks.

## Tests

```powershell
python -m unittest discover -s tests -v
```

The test suite covers Registry pagination, current Registry actor structures, removal and update activities, manual and catalogue provenance, URL normalization, deduplication, exact-name selection, JSONL/CSV storage, timestamped logs, and catalogue conversion.

## Implementation structure

| Path | Responsibility |
|---|---|
| `iiif_provider_census/fetch.py` | Retrieve JSON from HTTP(S), file URLs, or local paths |
| `iiif_provider_census/registry.py` | Traverse Registry pages and normalize Registry/manual records |
| `iiif_provider_census/models.py` | Define the normalized provider data model and URL identity rules |
| `iiif_provider_census/selector.py` | Apply deterministic provider-selection criteria |
| `iiif_provider_census/store.py` | Read and write JSONL, CSV, and plain-text logs |
| `iiif_provider_census/pipeline.py` | Coordinate source loading, deduplication, selection, and output |
| `iiif_provider_census/cli.py` | Expose the `run` and `select` command-line interfaces |
| `tools/build_catalog_inputs.py` | Convert the two upstream catalogue repositories into local JSON inputs |

## Technical references

- [IIIF Change Discovery API 1.0](https://iiif.io/api/discovery/1.0/)
- [IIIF Registry](https://registry.iiif.io/)
- [IIIF Guides to finding resources](https://guides.iiif.io/finding_resources/)
- [Awesome IIIF implementations](https://github.com/IIIF/awesome-iiif/blob/main/implementations.md)
