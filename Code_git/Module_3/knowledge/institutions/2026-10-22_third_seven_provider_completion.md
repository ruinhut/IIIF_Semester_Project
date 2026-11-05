# Seven distinct holders: the 100-source milestone — 22 October 2026

Evidence: `evaluation/2026-10-22_third_seven_provider_completion/`.
Cumulative bounded-run evidence increased **93→100 / 127 source entries**.
Seven new institutions were registered; all previous 120 census records are
unchanged. The original census still has **27 unresolved entries**. Historical
entries include duplicate institutions/projects and aggregators; 100 is not a
deduplicated institution count, a fresh reharvest of all sources, or a claim of
complete catalogues.

| New institution | Fresh M4-valid Manifests | M7 image associations |
|---|---:|---:|
| Berlin Central and Regional Library | 6 | 9 |
| Humboldt University of Berlin Library | 6 | 2,000 |
| Kiel City Archives | 6 | 7 |
| Kiel University Library | 6 | 938 |
| SLUB Dresden | 6 | 648 |
| University of Kassel Library | 6 | 22 |
| Upper Austrian State Library | 6 | 3,499 |

## Official discovery surfaces and saved recipes

1. **Kassel.** The [official ORKA portal](https://orka.bibliothek.uni-kassel.de/viewer/)
   explicitly declares its public RSS feed. Read `item/link`, extract the record
   identifier from `/viewer/image/{identifier}/…`, and validate the native route:

   ```text
   https://orka.bibliothek.uni-kassel.de/viewer/api/v1/records/rss?query=&sortField=DATECREATED&sortDescending=true
   https://orka.bibliothek.uni-kassel.de/viewer/api/v1/records/{identifier}/manifest/
   ```

   The real response for `DE-611-HS-4058424` is a Presentation 2 Manifest. The
   selected final postcard uses identifier `1769857290721`. The site's native
   `/viewer/api/v2/collections/DC/` also works and is saved as an investigation
   lead; the promoted RSS recipe does not yet traverse its whole hierarchy.
2. **Humboldt.** The [official digi-hub portal](https://www.digi-hub.de/viewer/)
   declares the same public feed structure. Use ascending `DATECREATED` for a
   historical feed subset and native `/api/v1/records/{identifier}/manifest/`.
   First source records include the memoirs of Marshal Ney, historical medical
   papers and bookplates. The final sample is the explicitly listed George
   Meyer bookplate `1479968607541`. A separate newest-feed academic volume
   `1780988531629` also validated. Some other newest records advertise denied
   access: do not treat metadata visibility as image permission or bypass it.
3. **Berlin Central and Regional Library / ZLB.** Its [public digital portal](https://digital.zlb.de/viewer/)
   exposes the same RSS route. The newest feed mainly lists modern publications,
   including restricted files; use the documented public feed's ascending sort
   for this historical sample. Native Manifest `15453578` and the Friedlaender
   collection records validate. `019591853_2010` timed out twice independently,
   was retained as a failure, and was not counted. A guessed `YEARPUBLISH` filter
   returned an explicit undefined-field 400 and is not in the promoted recipe.
4. **Kiel University Library and Kiel City Archives.** The [official Schriftgut.SH
   portal](https://schriftgut.sh/viewer/) links the [university library](https://schriftgut.sh/viewer/partner/ub-kiel/)
   and [city archives](https://schriftgut.sh/viewer/partner/stadtarchiv-kiel/).
   The old university portal redirects here. The common catalogue is filtered
   using **MD_DV_OWNER**, with exact values `Universitätsbibliothek Kiel` and
   `Stadtarchiv Kiel`. Extract IDs from `item/link` and request the native
   `/viewer/api/v1/records/{identifier}/manifest/` route. All 12 fresh Manifests
   were checked against their explicit owner metadata. They have no overlapping
   Manifest URLs; the shared portal is not counted as an eighth institution.
   The archive sample is a historical plan (`Ka__235`); the university example
   is a printed text (`PPN1965402933`, Canvas 21). Lübeck records also exist in
   this portal, but their declared external image URL failed in this environment:
   Lübeck was not added as a successful institution.
5. **SLUB Dresden.** The [official digital library](https://digital.slub-dresden.de/)
   provides the public catalogue:

   ```text
   https://digital.slub-dresden.de/oai/?verb=ListRecords&metadataPrefix=oai_dc
   oai:de:slub-dresden:db:id-32109025X
   → https://iiif.slub-dresden.de/iiif/2/32109025X/manifest.json
   ```

   The identifier template was checked against actual native responses, not
   accepted from the header alone. The existing generic XML recipe supports
   opaque OAI resumption tokens. Independent catalogue requests returned two
   different 25-record pages. Do not assume the configured 50-record size is the
   server's actual page size. The selected music manuscript is `312005946`.
6. **Upper Austrian State Library / Linz.** The [official digital portal](https://digi.landesbibliothek.at/viewer/)
   identifies the library. The platform's [own Collection API documentation](https://intranda.github.io/goobi-viewer-core/io/goobi/viewer/api/rest/v2/collections/CollectionsResource.html)
   specifies `/collections/{field}`. The actual native Collection:

   ```text
   https://digi.landesbibliothek.at/viewer/api/v2/collections/DC/
   → https://digi.landesbibliothek.at/viewer/api/v2/collections/DC/karten/
   ```

   The selected response is a Presentation 3 Collection with **466 members** and
   no declared `next`. Follow its explicit `items[].id` to native
   `/api/v2/records/{identifier}/manifest/` responses. Do not infer IIIF version
   from the platform's REST `/api/v1` or `/api/v2` prefix. The category contains
   whole works with cartographic content, not only one-page maps. The independent
   public RSS feed and `AC06324325` Manifest were also inspected but are not the
   promoted primary route for this source.

## Exact coverage and checks

- M2: seven reachable roots; six XML, one Collection JSON. Reachable XML is a
  legitimate enumeration surface, not an invalid institution.
- M3: 42 URLs, six per institution. M4: **42 freshly retrieved, valid Manifests**,
  zero cache hits. M5–7: **42 records, 7,123 image associations, 42 OCR profiles**.
- The five RSS recipes cover **at most 50 public feed records each**. No numeric
  pagination or complete-catalogue claim was established. A conservative
  `has_next` size heuristic in XML audit output is not a server-declared link;
  `pagination_validation.json` explicitly distinguishes this from actual OAI
  token continuation. Full enumeration needs further Collection/OAI/search work.
- Seven recipes independently validated two additional candidate responses each.
  Those checks are not added to the 42 downstream objects. All 42 Manifest URLs
  are distinct across providers; the two Kiel holders are separately verified.
- M5 research output retains all documents under the existing policy. Public
  reuse categories: 14 allow, 28 exclude; detailed categories: 8 public domain,
  6 open license, 4 institutional terms, 6 conflicting, 18 unknown. Do not equate
  retained unknown/exclude resources with permission for publication.
- M8 final output: **7 actual images, 21 linked JSON files**, all decoded,
  schema/ID verified, and matching native image-body dimensions. Earlier previews
  and unsuitable cover/blank examples remain in `initial_examples/`.
- Most Goobi Manifests declare preview URLs despite full dimensions. The separate
  evaluation helper reads the explicitly declared `info.json` and requests a
  supported full-size representation. Original image/source IDs are retained;
  `download_url` is the requested representation. **Production M7/M8 defaults
  were not changed** and may still use the original previews unless this explicit
  auxiliary step is run. SLUB's declared service itself is a 1000×1509 medium
  image, not an archival-resolution master.
- M3–8 automatic suites: **193 tests and seven subtests passed**. Knowledge
  **66→73**, original 66 entries and all 19 curated endpoints unchanged. The
  runtime discovery schemas/code and downstream contracts were unchanged.

## Real institutional OCR pair

The six Linz Manifests expose **3,504 reference descriptors**: 3,498 page/image
associations and six Manifest-level ALTO endpoints with no fabricated page ID.
Only one final reference was actually downloaded here, not all 3,504. Its chain:

```text
https://digi.landesbibliothek.at/viewer/api/v2/records/AC05304281/manifest/
→ /pages/21/canvas/
→ /files/alto/00000021.xml
→ declared Image service /api/v1/records/AC05304281/files/images/00000021.tif
→ /full/full/0/default.jpg
```

The image and ALTO Page both measure **2882×4629**; **159 word boxes** are within
the image. Text begins “Erstes Kapitel. Ankunft in Wilna…”. This is provider OCR,
not demonstrated manually corrected gold truth. The real XML, extracted text,
image and linked JSON are under `all/with_reference/`; the other six bundles are
under `all/without_reference/`. Prior reference examples were not modified.

## Transferable lesson

See [the reusable catalogue procedure](../skills/public_rss_oai_and_image_representations.md).
`verify_catalogue_feed_recipes.py` accepts an evaluation directory and rechecks
recipes, actual continuation, source overlap and holder metadata without needing
chat history. This stores executable methods; it is **not a runtime AI system
that investigates unknown institutions autonomously**. The previously identified
maintainability/generalisation gap remains a separate task.
