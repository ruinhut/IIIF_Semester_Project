# Keyed catalogues, SPARQL and source-filtered public indexes

Investigated on 21 October 2026. These are deterministic discovery operations;
there is no runtime LLM API call.

## Keyed records from a public frontend

The Vatican frontend declares `data-url="pickup/digital_gallery"` and requests
JSON with `format=ajax`. Resolve that relative route against the actual page
URL. It is not `/ajax/pickup/...`. Its response is a `result` dictionary keyed
by shelfmark, not a JSON array. Each value contains an explicit `id`.

Configure `records_path: result`, `records_format: mapping_values` and
`identifier_path: id`. The opt-in prevents unrelated metadata objects from
being treated as catalogue arrays. Expand the verified native route
`https://digi.vatlib.it/iiif/{identifier}/manifest.json` and independently check
the response. The public gallery is a selected subset, not the entire catalogue.
The separate category API also exists but large categories timed out in this
investigation; it has not been promoted as an exhaustive enumerator.

## Read-only SPARQL pagination plus Linked Art

Getty exposes an ActivityStreams catalogue feed and a public SPARQL endpoint.
The activity feed includes people and groups, so its total is not a Manifest
count. For an object enumerator, select CIDOC CRM Human-Made Objects and read
the SPARQL JSON `results.bindings[].s.value`. Use `ORDER BY ?s` to make
LIMIT/OFFSET pagination deterministic for a fixed dataset; changes during a
long harvest still require reconciliation.

`query_parameter_templates` explicitly allows string replacements for
`{page_number}` and `{page_size}` inside a query parameter. These are numeric
page/offset values. Ordinary literal SPARQL braces remain unchanged; no code
or expressions from the provider are evaluated. With a page step equal to
page size, the first value can be offset zero.

Fetch each declared object URL, then read `subject_of[].id`. Accept only the
reviewed `https://media.getty.edu/iiif/manifest/3/` namespace. The existing
identifier-followup operation handles this; downstream contracts are unchanged.
An object without an explicit Manifest link is not an error in the source and
must not be assigned an invented Manifest URL.

## Source-filtered aggregator index

Cultural Japan publishes an OpenAPI description at
`https://api.cultural.jp/openapi.json`. Its `/search` accepts 1-based `page`,
`size` and facets named `fc-{field}`. Facet keys use Japanese labels even when
English display labels are requested. Derive exact keys from the response or
documentation and preserve Unicode; Windows stdin can corrupt non-ASCII
literal strings, so use UTF-8 script files or escaped Unicode.

Use `fc-_media=IIIF`, inspect `hits.hits[].manifest[]`, then fetch every
candidate. The generic source uses upstream/native URLs; source-specific
recipes additionally restrict the native namespace for Harvard Art Museums.
Europeana's native namespace was also investigated, but the tested image links
were restricted, stale or served non-image content; that recipe was not promoted
as a completed source. This proves the indexed subset, not the full catalogue.
It does not require or bypass a provider API key. The provider's own API may
still be the better full-catalogue route if authorized credentials are supplied.

The `/search` total is capped at 10,000; `/count` is documented for exact
matching-index counts. Neither figure is a validated Manifest or image count.
The optional `/collection` endpoint returns a standard IIIF Collection but
also reflects a bounded query window; do not invent a next link if absent.

Indexed links may return 404, 500 or unusable media. Preserve those failures,
continue within the configured search window and separately validate image
downloads. Two aggregator sources can expose the same native Manifest:
deduplicate documents and media while retaining both discovery provenances.

## Partial results and verification

A catalogue-fetch or shape failure now marks the skill result `truncated`.
For example, one successful page followed by HTTP 429 cannot be a complete
harvest. Candidate Manifest failure is separate from catalogue completeness.
Success means valid samples were found, not every indexed URL works.

Tests cover keyed records and duplicate IDs, rejecting a mapping without
opt-in, literal query braces and offsets, and preserving partial output when
a later catalogue page fails. Live evidence, independent Module 4 fetches,
image/JSON checks and coverage limits are recorded under
`../../evaluation/2026-10-21_five_provider_completion/`.

## Public Primo catalogue and native library Manifests

NGA Library's official IIIF guide starts at the catalogue, not the museum's
artwork database. Its public Primo endpoint is `/primaws/rest/pub/pnxs`, with
the institution's `vid`, a query, `offset` and `limit`. The response lists
`docs[].pnx.control.sourcerecordid[0]` MMS identifiers and includes digital and
physical records. A thumbnail or catalogue match alone does not prove a Manifest.

The reviewed library route is
`https://libraryimage.nga.gov/manifest/mms/{identifier}.json`. Validate each
response and reject 404s; then use the declared `api.nga.gov` image service.
The experiment's `grandezze` query is a deliberately small keyword subset.
Do not count catalogue matches as digitized books, or extrapolate the subset
to the whole NGA Library. No change to the M4–8 provider contract is needed.

## Untyped seeAlso is not a reference label

Getty declares Linked Art catalogue objects as `Text` in seeAlso without a
text MIME type. Type `Text` alone is not OCR evidence. Module 6 now excludes
such unknown-format or JSON catalogue resources unless explicit OCR/transcription
signals exist. Plain text references, hOCR/ALTO and inline supplementing bodies
retain their existing handling; raw source Manifests retain the catalogue links.
