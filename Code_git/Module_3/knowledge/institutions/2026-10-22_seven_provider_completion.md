# Seven additional libraries — 22 October 2026

Evidence: `evaluation/2026-10-22_seven_provider_completion/`.
The target of **86 successful source entries** was reached from 79. Seven new
libraries were registered, increasing the census from 106 to 113. All old 106
records are unchanged. The original 94-entry census still has 27 unresolved
entries; cumulative entries include duplicates and aggregators, so **86 is not
a deduplicated institution count**. Historical successes were not all fetched
again today.

| Library | Native discovery scope | Fresh M4-valid Manifests | M7 image associations |
|---|---|---:|---:|
| Cologne Archdiocesan and Cathedral Library | Historical holdings Collection 381367 | 6 | 344 |
| Lippische Landesbibliothek Detmold | All-title catalogue, first sample | 6 | 504 |
| Mainz City Library | Dilibri virtual institution stbmz | 6 | 273 |
| Rheinland-Pfalz State Library Centre | Dilibri virtual institution rlb | 6 | 774 |
| Trier City Library | Dilibri virtual institution stbtr | 5 | 76 |
| Trier University Library | Dilibri virtual institution ubtr | 6 | 248 |
| Wienbibliothek im Rathaus | Culture and literature Collection 2612535 | 6 | 84 |

## Primary evidence and discovery

- [Cologne's official digital library](https://digital.dombibliothek-koeln.de/)
  identifies its Visual Library platform and historical holdings. Its actual
  `/i3f/v21/collection/top` response declares Collection `381367`, containing
  explicit Manifest members. The manuscripts Collection `334547` also exists,
  but the first inspected child was empty; this run uses historical holdings.
- [Detmold's digital collections](https://digitale-sammlungen.llb-detmold.de/)
  identify the Lippische Landesbibliothek. The responding native top Collection
  declares `/i3f/v21/collection/all`. This sample includes modern as well as
  historical material; do not describe every item as an ancient manuscript.
- [Vienna's digital library](https://www.digital.wienbibliothek.at/)
  declares thematic Collections. Culture/literature `2612535` contains books,
  illustrated works and music, with nested Collections as well as Manifests.
  The separately checked address-book Collection `2612506` was not the selected
  downstream sample and must not be added to its counts.
- [Dilibri's official partner list](https://www.dilibri.de/) explicitly lists
  the State Library Centre, Trier University Library, Trier City Library and
  Mainz City Library as **different holders**. Their public branch pages are
  `/rlb`, `/ubtr`, `/stbtr`, `/stbmz`. Dilibri itself is not counted as an eighth
  new institution. The institution-specific native roots are:

```text
https://www.dilibri.de/rlb/i3f/v21/collection/all
https://www.dilibri.de/ubtr/i3f/v21/collection/all
https://www.dilibri.de/stbtr/i3f/v21/collection/all
https://www.dilibri.de/stbmz/i3f/v21/collection/all
```

All seven selected roots responded with real `sc:Collection` JSON and explicit
`members` links. Several HTML portals and partner history pages instead returned
200 with a **browser verification page** and no catalogue links. Their status
alone is not proof of discovery. The available public IIIF interfaces were used;
no CAPTCHA or verification script was executed or bypassed.

## A generic bug found and fixed: virtual-institution scope

The four Dilibri roots return different scoped members and totals, but declare
global identifiers and pagination links such as:

```text
requested root: https://www.dilibri.de/ubtr/i3f/v21/collection/all
declared next:  https://www.dilibri.de/i3f/v21/collection/all_o20
scoped next:    https://www.dilibri.de/ubtr/i3f/v21/collection/all_o20
```

Following the declared global Collection URL would lose the university-library
scope. A scoped response is not proof that its child/pagination links retain it.
This also applies to nested Collection links, not just `next`.

Added an opt-in `collection_url_rewrites` rule in reviewed knowledge skills:

```json
{
  "collection_url_rewrites": [{
    "from_prefix": "https://www.dilibri.de/i3f/v21/collection/",
    "to_prefix": "https://www.dilibri.de/ubtr/i3f/v21/collection/"
  }]
}
```

The generic Collection walker applies this **only to Collection requests**.
Prefixes must share the same scheme/host and end in `/collection/`; broad,
cross-origin and malformed rules are rejected as recorded issues. Manifest and
image URLs remain exactly as declared. The audit records both `declared_url` and
`requested_url`; these scope events are excluded from actual knowledge-skill
execution counts. No institution hostname or ID is hard-coded in runtime logic.
Sources without a reviewed rule retain their previous traversal behavior.

Independent verification:

- All seven next-page pairs were requested and have different member sets.
- The generic M3 walker was separately run to **24 unique discovered URLs** for
  each Dilibri library. All Collection requests keep the correct institution
  path. Mainz reached the cap inside a nested collection before its root `next`;
  the root next page was independently fetched in the pagination checks.
- All **23 M4-valid Dilibri sample Manifests** were checked against their actual
  `attribution` and `Online-Ausgabe` metadata. The names distinguish Trier city
  from Trier university; their validated Manifest URL sets do not overlap.
- Each of the seven supplementary first-page fallback recipes was separately
  executed with two results. Its extra checks and the four 24-URL runs are **not
  added** to the main downstream count. The fallback remains first-page-only;
  generic Collection traversal handles full pagination subject to run budgets.

## End-to-end measurements and limitations

- M2: 7/7 selected native JSON endpoints reachable.
- M3: 42 unique URLs, bounded at six per provider.
- M4: 42 fresh network retrieval attempts, zero cache hits. 41 structurally
  valid. Trier City `2799234` returned 404 and remains in unavailable evidence.
- M5–7: 41 documents, **2,303 image associations**, 41 OCR profiles, zero declared
  institutional page-reference texts. Six public-domain documents are eligible
  for reuse under the existing policy; 35 unknown documents remain research-only.
  No unknown rights value was rewritten as copyright-free.
- M8: seven final images plus 21 linked JSON files. All decode and schema/ID
  checks pass; all actual dimensions match the declared image-body dimensions.
  They are mostly 1000-pixel previews, not asserted archival-resolution images.
- Initial Detmold and State Library Centre examples were blank pages. They were
  archived and replaced by content pages (`9323782`, sequence 20; `296109`,
  sequence 9). Nine different images were downloaded during the investigation,
  while the final index and presentation directory contain seven example bundles.
- No reference text is declared in this sample, so all examples are
  `without_reference`. The 59 generic ground-truth candidate entries are not 59
  correct transcriptions. Old `with_reference` examples and behavior remain.
- M3–8 tests: **193 passed plus seven subtests**. Six new tests cover scoped
  pagination, unchanged Manifest URLs, unchanged default behavior, cross-origin
  and overbroad rejection, and malformed-rule handling.
- Knowledge increased **52→59 entries**. All old 52 entries and 19 curated
  endpoint entries are unchanged. No runtime language-model API was integrated.

Old-census retries: Finna and Illinois catalogue requests returned 403; NCSU
returned 401. Folger and several other probes raised URLError. Hamburg exposed
a browser challenge. Guessed Halle Collection routes returned 404. None is a new
success or evidence that the institution lacks IIIF. Do not bypass restrictions.

The Chinese report, `provider_results.csv`, `sample_downloads.csv`, request
snapshots, scope/ownership QA, tests, preservation checks and `运行命令.txt` are
saved in the dated evidence directory. Only the bounded sample was validated;
no entire institution catalogue was declared complete.
