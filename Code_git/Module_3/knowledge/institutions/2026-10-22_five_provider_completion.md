# Five-source completion — 22 October 2026

Evidence: `evaluation/2026-10-22_five_provider_completion/`.
Restored one old entry, **KU Leuven**, and registered four additional libraries:
Karlsruhe, Bonn, Frankfurt and Paderborn. Cumulative evidence is **79/106 source
entries**, with **27 old entries still unresolved**. Prior successes were not all
re-fetched today. These are bounded collection samples, not completed catalogues.

| Institution | Saved route | M4-valid Manifests | M7 image associations |
|---|---|---:|---:|
| KU Leuven | Public Lovaniensia catalogue → detail page → explicit native Manifest | 6 | 1,162 |
| Badische Landesbibliothek Karlsruhe | Native incunabula Collection 178827 → members | 6 | 812 |
| Bonn University and State Library | Native medieval manuscripts Collection 10250864 → members | 6 | 2,786 |
| Frankfurt University Library | Native all Collection → members | 5 | 135 |
| Paderborn University Library | Native Zugschwerdt Collection 8437472 → members | 6 | 1,644 |

## KU Leuven: retain the failed old entry and add the working public route

The [official IIIF guide](https://iiif.io/guides/kuleuven.limo.libis.be/)
describes finding a Manifest in the catalogue interface. The old census retained
only the Limo homepage. It remains reachable HTML but is not a bulk IIIF list.
KU's [digital preservation documentation](https://bib.kuleuven.be/english/collections-access-borrowing/collection-policy/digitale-preservatie-en-langetermijnbewaring)
explains the Teneo/LIBIS ecosystem. Historical lecture material contains working
single-item examples but its Jesuitica Collection route now returned 404; it was
not promoted as an operational batch endpoint.

The public [Lovaniensia catalogue](https://www.lovaniensia.be/items/browse)
provides the reproducible path:

1. Read `/items/browse?page=1`, then the explicitly linked next result page.
   The current site exposes **10 item links per page**. The recipe detects
   explicit next-page links rather than treating an assumed page size as proof
   that the catalogue has ended. Pages 1 and 2 were separately fetched and their
   record sets differ.
2. Follow `/items/show/{catalogue_id}`. Example: `6217`.
3. Read the page's explicit IIIF anchor, e.g.
   `https://data.lovaniensia.be/IE17067641/manifest`. This is a second identifier;
   the catalogue item number is **not** the IE identifier. Do not extrapolate
   integer ranges or construct an IE identifier from the detail-page ID.
4. Validate the native Presentation 3 Manifest; follow its declared Image API
   request, e.g. the `lib.is/IE17067641/iiif/2/FL17067843/.../default.jpg` image.

All six sampled Manifests explicitly locate the original at **KU Leuven
Libraries Special Collections**, verified in `ku_leuven_ownership_validation.json`.
Lovaniensia is a collaboration: future results must preserve the original holder
instead of automatically assigning every project record to KU Leuven.

The Omeka catalogue API `/api/items?per_page=6&page=1` returned **403**. The saved
recipe uses ordinary public listing/detail pages and their declared links; it
does not bypass that API restriction. The old provider ID, Limo endpoint and
source fields are preserved. No new Leuven institution entry was counted.

This uses the existing generic HTML-listing → HTML-detail → Manifest skill.
Platform identification alone is not a successful download: every arrow has
actual response evidence, independent M4 validation and a real M8 image.

## Four VisualLibrary installations: reuse native Collections

Official portals and interface documentation:

- [Karlsruhe interfaces](https://digital.blb-karlsruhe.de/blbdd/wiki/schnittstellen)
- [Paderborn digital collections](https://digital.ub.uni-paderborn.de/)
- [Bonn digital collections information](https://digitale-sammlungen.ulb.uni-bonn.de/ulbbn/wiki/about)
- [Frankfurt digital collections](https://sammlungen.ub.uni-frankfurt.de/)

On each verified installation, the responding native
`/i3f/v21/collection/top` document declares the collection hierarchy. The following
roots were selected from its actual links, not from invented collection IDs:

```text
https://digital.blb-karlsruhe.de/i3f/v21/collection/178827
https://digital.ub.uni-paderborn.de/i3f/v21/collection/8437472
https://digitale-sammlungen.ulb.uni-bonn.de/i3f/v21/collection/10250864
https://sammlungen.ub.uni-frankfurt.de/i3f/v21/collection/all
```

These Collection documents use `@type: sc:Collection` and `members[].@id`.
They explicitly distinguish child Collections from Manifests. Follow `next` as
declared, e.g. `.../collection/178827_o20`; do not replace it with an assumed
`?page=2`. All four declared next pages were fetched and contain different
members. Paderborn's first two pages contained 20 and 4 member links, respectively;
this is a link count for that collection, not proof that 24 downloadable books
have been independently validated.

The existing generic Collection walker handles these native roots and `next`
links. Four supplementary first-page fallback recipes were independently live
checked with two valid Manifests each. Those eight extra checks are **not added**
to the downstream total. The fallback itself is explicitly documented as
first-page-only; full pagination belongs to the generic Collection walker.

## Failures and output boundaries

- M3 found 30 Manifest URLs, six per source. M4 fetched all 30 freshly, with no
  cache hits. Frankfurt `8929677` declares a P2 Manifest but has no `sequences` or
  usable Canvas; its PDF rendering is not a replacement for page-image inventory.
  It remains in `invalid_manifests.jsonl`. **29 Manifests** passed M4.
- M5–7 exported **29 documents, 6,539 image associations and 29 OCR profiles**.
  No institution reference text is declared in this sample, so no new
  `with_reference` examples were claimed. A generic ground-truth candidate record
  is not proof of a human-corrected institutional transcript.
- Five final M8 example bundles contain five actual images and fifteen linked
  JSON files. The first Frankfurt choice was a blank page; it was archived and
  replaced with a text-bearing Hebrew-script page from Manifest `2026040`, sequence 9.
  Six different images were downloaded during this run; the final index contains
  five. Initial evidence remains available outside the final presentation folder.
- KU's image is 3672×4527; Bonn's is 1000×1379. Karlsruhe, Frankfurt and Paderborn
  return native 1000-pixel preview derivatives with an additional **50-pixel
  attribution border**. The dimensions differ from the declared body dimensions.
  Retain actual dimensions; do not treat them as original OCR coordinate space.
- Digital Commonwealth, Villanova and one Qatar candidate returned 403.
  Georgetown returned 200 HTML with an access challenge, not catalogue JSON.
  UCD and Duesseldorf probes raised URLError. None was counted as a new success;
  no access challenge, authentication, TLS or geographic restriction was bypassed.
- Existing 47 knowledge entries and 19 curated endpoint entries remain unchanged.
  Five reviewed configurations were added, for **52 knowledge entries**. All
  runtime modules and downstream schemas are unchanged; no runtime AI API added.
- M3–8: **187 tests passed, plus seven subtests**. All five final images decode;
  all fifteen sample JSON files pass schema and ownership checks.

See the saved Chinese report, `sample_downloads.csv`, `provider_results.csv`,
`pagination_validation.json`, preservation checks and `运行命令.txt` in the evidence
directory. Never infer institution-wide totals from these six-object caps.
