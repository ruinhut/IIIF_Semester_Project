# Fourth five-source completion — 21 October 2026

Evidence: `evaluation/2026-10-21_fourth_five_provider_completion/`.
All five are **new institutions outside the previous 97-entry census**. They
do not reduce the 28 still unresolved old entries. Cumulative evidence is now
74/102 source entries, not an independent-institution count or a full harvest.

| Institution | Verified discovery route | M4-valid Manifests | Exported image associations |
|---|---|---:|---:|
| Berlin State Library | OAI-PMH header PPN → documented native Manifest | 6 | 681 |
| National Library of Norway | Public digital-book search → HAL presentation links | 5 | 1,380 |
| Pennsylvania State University Libraries | Native CONTENTdm diary Collection → declared Manifest | 1 | 57 |
| University Library of Bern | Official IIIF manual → Haller GGA Collection → volume Manifests | 6 | 6,212 |
| University of Manchester Library | Website's JSONAdvanced search → item.id[0] → native Manifest | 6 | 1,864 |

## Reusable methods and exact scope

1. **Manchester.** The [official help page](https://www.digitalcollections.manchester.ac.uk/help/)
   identifies Cambridge collaboration and XTF indexing. Its search page loads
   `page-advanced-search-results-179630aff71c8179bb33.js`, which declares the
   read-only `/search/JSONAdvanced` request. The page computes `start=(page-1)*20`
   and `end=page*20`. Confirmed requests for ranges 0–20 and 20–40 have different
   records. Read `items[].item.id[0]`, then request
   `https://www.digitalcollections.manchester.ac.uk/iiif/{id}`. Query `manuscript`
   declared 1,124 search hits; only six were validated here. Server returns 20
   records even when the requested end is 6, so do not assume an arbitrary page
   size. The generic executor now supports `{page_end}` with a regression test.
   Some Manifest image IDs are bare Image service roots; use the declared
   service and actual JPEG request, not its info document. The selected Arabic
   manuscript image is 1543×2000, smaller than its 4243×5500 Canvas declaration.
2. **Penn State.** Its public CONTENTdm collection-list API is
   `https://digital.libraries.psu.edu/digital/bl/dmwebservices/index.php?q=dmGetCollectionList/json`.
   It declares the `ejb` (Elisha J. Bracken Civil War Diary) alias. The native
   `https://digital.libraries.psu.edu/iiif/2/ejb/manifest.json` is a Collection
   declaring the compound diary Manifest, not one Manifest per scanned page.
   One Manifest contains 57 image associations. Native image delivery is through
   the explicitly declared `cdm17287.contentdm.oclc.org` host. This run covers
   that diary, not all Penn State collections. The
   [OCLC Presentation documentation](https://help.oclc.org/Metadata_Services/CONTENTdm_classic_version/Advanced_website_customization/API_Reference/IIIF_API_reference/Work_with_the_IIIF_Presentation_API)
   explains Collection traversal; the actual installation's declared routes
   take precedence over older `/iiif/info/` examples.
3. **Norway.** The [official OpenAPI document](https://api.nb.no/catalog/v1/items/api-docs)
   documents the public catalogue, HAL links, digital filters and pagination.
   Use `https://api.nb.no/catalog/v1/items` with `q=mediatype:bøker AND digital:Ja`,
   `filter=date:[15000101 TO 19001231]`, `digitalAccessibleOnly=true` and `size=6`.
   Follow `_embedded.items[]._links.presentation.href`; never infer public images
   from metadata alone. A query filtering `contentClasses:public` but omitting
   `digital:Ja` returned non-digitized catalogue records, so it was rejected as
   the harvesting recipe. Five Manifests were found by the bounded generic
   discovery run. The configured fallback was separately tested successfully;
   its extra result is not added to the downstream count. Access checks remain
   active; no login or geographic restriction is bypassed.
4. **Berlin.** [Official OAI/IIIF documentation](https://lab.sbb.berlin/dc/?lang=en)
   gives `https://oai.sbb.berlin/?verb=ListRecords&metadataPrefix=oai_dc` and the
   header identifier `oai:digital.staatsbibliothek-berlin.de:PPN...`.
   Extract the entire PPN (including an optional `X`), then request
   `https://content.staatsbibliothek-berlin.de/dc/{PPN}/manifest`.
   This reuses the generic XML skill added in the preceding batch. Continuation
   tokens are opaque: preserve percent characters rather than decoding their
   embedded parameter syntax. Six first-page Manifests were independently
   fetched by M4. Three of these declare 97 Canvas-level ALTO reference links.
5. **Bern.** The [institutional IIIF server manual](https://ub-unibe-ch.github.io/IIIF_Server/presentation_api/)
   directly declares the Haller GGA Collection
   `https://iiif.ub.unibe.ch/presentation/v2.1/collection/691e6e0c-afc2-4f17-aee5-d9f88be15865/`.
   Follow native volume Manifests instead of inventing UUIDs. Six sampled volumes
   supplied 6,212 image associations; this is one project subset of Bern holdings.

## Reference text and downstream quality

- The Berlin sample `PPN1000056597`, first Canvas, is a German printed page dated
  1719 with historical typefaces. Its Manifest declares the corresponding ALTO
  OCR URL. The sample image is 2221×3540; the downloaded ALTO Page declares the
  same pixel dimensions. It contains 47 nonempty word elements. Image, raw XML,
  extracted text and linked JSON are stored under `with_reference`.
- The 97 exported links are **declared reference descriptors**. One reference
  was actually downloaded and checked here. Neither quantity certifies manually
  corrected gold truth or all reference endpoints being available.
- Inspection found M8's previous XML text flattening included ALTO processing
  settings and filenames. ALTO now uses namespace-aware XML parsing and only
  `String/@CONTENT` in reading order, with line breaks and decoded XML entities.
  Source ALTO remains intact. Metadata-only ALTO is empty and follows the
  `reference_failed` path. Standard `application/alto+xml` responses are accepted.
- Actual ALTO namespace is v4, while the source Manifest's profile link mentions
  v2; preserve both facts. Local JSON schema checks are not ALTO XSD validation.
- No institution-specific changes were needed in Modules 4–7. M5 retained all
  24 records for academic analysis while preserving restrictive/unknown rights;
  zero were marked eligible for unrestricted reuse by the current policy.

## Verification and preservation

- M1 registered five sources; all previous 97 census records remain unchanged.
- M2 checked five routes: all reachable, four JSON and one XML/non-JSON.
  XML/non-JSON does not mean the Berlin endpoint is inaccessible.
- M4 fetched all 24 Manifests freshly, with zero cache hits; all were valid.
- M7 exported 24 documents, 10,194 image associations, 24 OCR profiles and 97
  reference descriptors. M8 initially downloaded five real images and one ALTO
  resource, with zero failures. A subsequent M8 run reused those image files and
  re-fetched the reference to regenerate clean text; initial evidence is retained.
- Five images decode, and all 15 linked JSON files pass schemas/ownership checks.
- M3–8: **187 tests passed plus seven subtests**. This includes one range-pagination
  test and four ALTO extraction/failure-handling tests added in this batch.
- Discovery knowledge increased 42→47 entries; all previous 42 recipes and 19
  curated endpoint entries remain unchanged. Runtime AI API integration was not added.
- Investigated but not counted: Trinity's CAPTCHA, Cornell's 403, an unreachable
  Edinburgh image host, and other unconfirmed candidate routes. RBGE's valid
  specimen service was investigated but not registered or counted in this batch.
