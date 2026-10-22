# Five reviewed source entries — 21 October 2026

Evidence directory: `../../evaluation/2026-10-21_five_provider_completion/`.
Five previously unresolved census entries completed discovery, independent live
Module 4 retrieval, Modules 5–7 and an actual Module 8 image download each.

| Source entry | M4-valid Manifest associations | M7 image associations | Discovery route |
|---|---:|---:|---|
| DigiVatLib | 6 | 1,961 | Public selected-gallery JSON dictionary → shelfmark ID → native Manifest |
| J. Paul Getty Trust | 6 | 19 | Ordered SPARQL object IDs → Linked Art details → explicit native P3 links |
| Cultural Japan | 6 | 6 | Public source index → explicitly declared upstream/native Manifests |
| Harvard Art Museum | 6 | 7 | Same index filtered to Harvard → native Harvard Manifests |
| National Gallery of Art Library | 3 | 999 | Public Primo catalogue → MMS IDs → native library Manifests |

One Harvard Manifest is also found through Cultural Japan. Thus the final
deduplicated output is **26 Manifests and 2,991 image associations/URLs**, not
27 Manifests or 2,992 images. Five images were really downloaded, without cache
hits, with 15 schema-valid linked JSON files. All decode successfully.

## Primary sources and live routes

- [Vatican IIIF guide](https://iiif.io/guides/guides/vatlib.it/) and the
  [institutional frontend](https://digi.vatlib.it/). Its public `site.js`
  requests the gallery's declared relative URL with `format=ajax`:
  `https://digi.vatlib.it/pickup/digital_gallery?format=ajax`.
  `result` contains 14 keyed selected-manuscript records in this investigation.
  Example verified native Manifest:
  `https://digi.vatlib.it/iiif/MSS_Vat.lat.3225/manifest.json`.
  Large category enumeration timed out; full Vatican coverage is not claimed.
- [Getty IIIF guide](https://iiif.io/guides/guides/search.getty.edu/),
  [Getty API documentation](https://data.getty.edu/) and the live public
  endpoint `https://data.getty.edu/museum/collection/sparql` with a read-only
  SELECT query. Getty's ActivityStreams feed contains multiple entity types;
  its 4.5-million-scale event total is not a count of available Manifests.
  Select `crm:E22_Human-Made_Object`, order by object URI and use LIMIT/OFFSET.
  Object details declare P3 Manifest URLs in `subject_of[].id` under
  `https://media.getty.edu/iiif/manifest/3/`. No inferred image-only object is
  converted into an invented Manifest.
- [Cultural Japan](https://cultural.jp/), its public
  [OpenAPI description](https://api.cultural.jp/openapi.json) and
  [API interface](https://api.cultural.jp/spec). The indexed IIIF query uses
  `fc-_media=IIIF`, 1-based `page` and `size`; explicit native links are read
  from `hits.hits[].manifest[]`. Dynamic Cultural Japan-generated Manifests
  are excluded from the generic native-link recipe. The experiment reached
  two pages to validate six Manifests. `/search` totals are capped at 10,000.
- [Harvard Art Museums official IIIF documentation](https://github.com/harvardartmuseums/api-docs/blob/master/sections/iiif.md)
  documents the native route separately from the main data API. The exact
  Cultural Japan source facet is `ハーバード美術館API` (Japanese key, not its
  English label). Restrict candidate links to
  `https://iiif.harvardartmuseums.org/manifests/object/<id>` and validate them.
  One stale candidate returned 500 before the next page supplied a sixth
  valid Manifest. Coverage is Cultural Japan's indexed Harvard subset.
- [NGA Library official IIIF guide](https://iiif.io/guides/guides/library.nga.gov/)
  starts with the library catalogue. The public frontend's Primo route is
  `https://library.nga.gov/primaws/rest/pub/pnxs`. Supply `vid=01NGA_INST:NGA`,
  the query and offset/limit pagination. Read
  `docs[].pnx.control.sourcerecordid[0]`; test the native library route
  `https://libraryimage.nga.gov/manifest/mms/<id>.json`.
  The `grandezze` experiment covers 18 catalogue matches, including physical
  titles, and yields three valid digital books. This is not a whole-library
  enumeration and not the separate NGA museum collection.

## Reusable changes and reference quality

- M3 adds explicit `records_format=mapping_values` and
  `query_parameter_templates` for numeric LIMIT/OFFSET. Literal SPARQL braces
  remain intact. Old recipes keep their default behavior.
- Catalogue fetch/shape errors mark partial traversal incomplete. A reachable
  HTML page skipped because HTML traversal is disabled is no longer described
  as a network-unreachable endpoint.
- Getty's untyped-format seeAlso links declare catalogue Linked Art objects as
  `Text`. M6 now requires transcription evidence for such unknown/JSON links,
  retaining raw links in source Manifests. Tests preserve genuine declared
  transcriptions and existing hOCR/ALTO handling.
- Final source sample has zero OCR reference descriptors. The 37 sampling
  candidate rows are not verified institutional transcriptions; all five image
  bundles are correctly in `without_reference`.
- M3–8 regression tests: **173 passed plus seven subtests**. M4 freshly fetched
  all final 26 Manifests, with zero cache hits. The subsequent M3 diagnostic
  refresh replays same-day snapshots; it does not replace independent M4 checks.

## Download limits and partial investigations

NGA's downloaded image is 2818×4096, while its Canvas declares 3302×4800.
Other four downloaded samples match their Canvas dimensions. Getty's sample
is 483×600 and Harvard's is 299×1024: valid declared images, not a claim of
archival/original resolution. Preserve actual dimensions and apply scaling
before transferring page coordinates. No full-resolution guarantee is made.

Europeana was initially selected: six native Manifests passed M4, but the
sample image returned 403. Other reviewed media links were stale, HTML instead
of JPEG, or failed TLS. Native Manifest availability is therefore not proof of
image availability. It was replaced by NGA in the five complete cases; the
Europeana evidence remains in `first_attempt/initial_europeana_batch/` and
`unresolved_investigations.json`, outside the five promoted recipes.
Folger/Leeds single Manifests and other blocked/retired sources likewise are
not presented as completed bulk discovery. No CAPTCHA, credentials or TLS
verification were bypassed.

Cumulative conservative completed-source evidence: **54 → 59 / 94**, with
**35 entries outside that success set**. This is the existing source census,
which includes aggregators and aliases, not 59 independent global institutions.
Europeana remains a partially resolved exception, not an assertion that no
Manifest can be fetched. Older successful sources were not all re-fetched.
Knowledge entries increase from 28 to 33; all previous recipes and 18 curated
endpoint configurations remain unchanged. Changes are local, not yet pushed.

See [generic skills](../skills/keyed_catalogues_sparql_and_aggregator_indexes.md).
