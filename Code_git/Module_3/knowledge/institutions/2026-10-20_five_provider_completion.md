# Five additional reviewed sources — 20 October 2026

Local evidence: `../../evaluation/2026-10-20_five_provider_completion/`.
The experiment selected five previously unresolved census IDs. Module 2
rechecked their supplied homepage routes; reviewed candidate knowledge then
ran through the real Module 3, fresh Module 4 retrieval, Modules 5–7 and one
actual image download per source. Only verified recipes were promoted.

| Source | Reviewed discovery method | M4-valid Manifests | M7 image records |
|---|---|---:|---:|
| Ghent University | Biblissima's filtered Ghent results → declared native `data-manifest` URLs | 6 | 1,206 |
| University of St Andrews | Public frontend → Funnelback search → published image IRNs → native Manifest | 4 | 7 |
| Yale Center for British Art | LUX institution filter → Linked Art details → explicit `ycba/obj` Manifest | 6 | 15 |
| Yale Peabody Museum | Same generic procedure, `ypm/nat` namespace | 6 | 6 |
| Yale University Art Gallery | Same generic procedure, `yuag/obj` namespace | 6 | 11 |

Total: 28 independently fetched and structurally validated Manifests, 1,245
image associations with distinct image URLs in this sample, five real images
and 15 schema-valid linked JSONs. All five images decode and match the declared
source dimensions. These are samples, not institution-wide harvest totals.

## Authoritative entry points and observed recipes

- [IIIF Ghent guide](https://guides.iiif.io/guides/lib.ugent.be/) and
  [Biblissima's indexed collections](https://iiif.biblissima.fr/collections/).
  Filter `collection=Ghent University Library`; follow `from` offsets. The
  result HTML declares native URLs under `adore.ugent.be/IIIF/manifests/`.
- [IIIF St Andrews guide](https://guides.iiif.io/guides/st-andrews.ac.uk/) and
  the institution's [current public search](https://collections.st-andrews.ac.uk/search/?query=photograph&form=grid&mode=query).
  Its declared application script `ag--search/main-WXV7NP3J.js` exposed the
  public Funnelback search collection `standrews~sp-web-sc-photo`, `start_rank`
  pagination, result paths and IRNs. The validated native route is
  `https://collections.st-andrews.ac.uk/625074/manifest` (among other IDs).
- [Yale's LUX Python API documentation](https://github.com/project-lux/luxy)
  and the live configuration endpoint
  `https://lux.collections.yale.edu/api/advanced-search-config` establish the
  search terms. `memberOf` is a supported relation; guessed `heldBy` was not.
  Search with `AND(hasDigitalImage=1, memberOf.name=<museum name>)`, then follow
  object UUIDs to the explicit Manifest links in their Linked Art records.
  Examples independently verified:
  `https://manifests.collections.yale.edu/ycba/obj/48501`,
  `https://manifests.collections.yale.edu/ypm/nat/576819`,
  `https://manifests.collections.yale.edu/yuag/obj/209803`.

Yale's three museums are distinct existing source entries, but reuse one LUX
algorithm. The other Yale British Art census alias was not automatically
counted as another success. No claim is made about Yale Library delivery or
the complete Yale institutional network.

## Reusable changes and limits

- Added opt-in HTML attribute enumeration and scalar array-index paths in
  Module 3; tests cover deduplication, pagination and institutional namespaces.
- St Andrews initially selected no IDs because scalar filter paths did not
  read array indices. Corrected this generic behavior and retained the failed
  first attempt. Two successful pages yielded four eligible Manifests before
  another page returned HTTP 429. Coverage remains partial and rate-limited.
- Three sources' supplied homepage routes were reachable HTML; two were
  restricted. Their usable structured discovery routes are separate public
  surfaces. No authentication or certificate checks were disabled.
- The provisional common schema remains incomplete in these records;
  Module 6 reports partial records when bibliographic fields are missing.
- Module 6 previously interpreted six British Art RDF Dataset links as text.
  Added semantic exclusions and reran downstream export. There are zero OCR
  reference descriptors after correction; all five sample bundles are in
  `without_reference`. Candidate ground-truth sampling rows are not verified
  page transcriptions.
- M3–8 tests: 166 passed and seven subtests passed. M4 fetched all 28
  Manifests independently with zero cache hits. Image download traces retain
  the first five live downloads; the metadata refresh reused those images.

The final cumulative census evidence is 54 of 94 source entries, 40 unresolved.
This is not a count of independent institutions worldwide, and historical
successes were not all re-fetched today. Blocked or partial alternative probes
are listed in `unresolved_investigations.json`, rather than counted successes.

See [generic skills](../skills/catalogue_attributes_and_linked_art.md).
