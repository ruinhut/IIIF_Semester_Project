# Seven more sources: the 93-source milestone — 22 October 2026

Evidence: `evaluation/2026-10-22_second_seven_provider_completion/`.
Cumulative bounded-run evidence increased **86→93 / 120 source entries** after
registering seven additional libraries. All previous 113 census records remain
unchanged. The original 94-entry census still has **27 unresolved entries**.
These are source entries, not deduplicated institutions, completed catalogues or
120 sources freshly re-fetched today.

| Source | Saved native route | Fresh M4-valid Manifests | M7 image associations |
|---|---|---:|---:|
| Koblenz City Library | Dilibri stbkodfg Collection | 6 | 1,611 |
| Leipzig University Library | Greek manuscripts static Collection | 6 | 1,790 |
| Oldenburg State Library | Manuscripts Collection 785124 | 6 | 980 |
| Potsdam University Library / Digitales Brandenburg | Native all-title Collection | 6 | 674 |
| Trier Seminary Library | Dilibri pstr Collection | 5 | 477 |
| University of Graz Library | Digi SCRIPT scoped Collection | 6 | 2,544 |
| Worms City Library | Dilibri stbwo Collection | 6 | 488 |

## Official sources and reproducible discovery

1. **Koblenz, Worms, Trier Seminary.** The [official Dilibri partner list](https://www.dilibri.de/)
   links these distinct institutions' catalogue branches:
   [Koblenz DFG](https://www.dilibri.de/stbkodfg/nav/history),
   [Worms](https://www.dilibri.de/stbwo/nav/history), and
   [Trier Seminary](https://www.dilibri.de/pstr/nav/history).
   Their actual responding native Collections are:

   ```text
   https://www.dilibri.de/stbkodfg/i3f/v21/collection/all
   https://www.dilibri.de/stbwo/i3f/v21/collection/all
   https://www.dilibri.de/pstr/i3f/v21/collection/all
   ```

   Follow explicit `members` and preserve each branch on child/next Collection
   requests using the reviewed mapping added in the preceding run. The platform
   is not an additional eighth source. These are not the previously registered
   Trier city/university libraries or Rheinland-Pfalz State Library Centre.
   Manifest `Online-Ausgabe` values name the respective institution and city.
2. **Oldenburg.** Its [official digital-collections portal](https://digital.lb-oldenburg.de/)
   identifies the State Library and Visual Library platform. The actual native
   top Collection declares manuscript Collection:
   `https://digital.lb-oldenburg.de/i3f/v21/collection/785124`.
   Its `members` declare native Manifests; its `next` URL ends in `_o20`.
3. **Leipzig.** The previously published UBLab documentation URL now redirects
   to the library homepage, but the native root remains live:
   `https://iiif.ub.uni-leipzig.de/static/collections/toplevel.json`.
   It explicitly declares the Greek-manuscript Collection:
   `https://iiif.ub.uni-leipzig.de/static/collections/GriechischeHandschriften/collection.json`.
   Read `manifests[].@id`; first samples identify Leipzig university-library Greek
   manuscripts. A dead or redirected documentation page does not establish that
   the native IIIF service is gone. This selected static Collection declares no
   `next`; the root also contains external holders, so do not attribute every
   root member to the university's own physical holdings.
4. **Graz.** The responding `https://unipub.uni-graz.at/obvugrscript/i3f/v21/collection/top`
   identifies **Digi SCRIPT** and declares its all-title Collection. The same
   opt-in scope mapping works across this different installation:

   ```text
   https://unipub.uni-graz.at/i3f/v21/collection/
   → https://unipub.uni-graz.at/obvugrscript/i3f/v21/collection/
   ```

   The first page contains ten members and `next` ends in `_o10`, not `_o20`.
   Always follow the declared link with the reviewed scope, not an assumed page
   increment. Actual sample labels identify Graz University Library Ms 0001–0006.
   Some HTML requests are restricted while these public native JSON routes work;
   no access challenge or authentication restriction was bypassed.
5. **Potsdam.** Its [official portal](https://digital.ub.uni-potsdam.de/)
   identifies **Digitales Brandenburg**, publishing the university library's
   holdings and cooperating institutions' resources. The native top Collection
   declares `https://digital.ub.uni-potsdam.de/i3f/v21/collection/all`.
   Preserve original-holder versus digital-edition publisher metadata. Each of
   the six sampled Manifests names Potsdam University Library in `Online-Ausgabe`;
   this confirms the digital publisher, not ownership of every physical original.

## Independent checks and exact scope

- M2: all seven selected roots return real native Collection JSON.
- M3: 42 unique URL discoveries, six per source under the sample limit.
- M4: 42 fresh retrieval attempts, zero cache hits; 41 valid Manifests. Trier
  Seminary `1937135` returned 404, retained in unavailable evidence and excluded.
- M5–7: **41 records, 8,564 image associations and 41 OCR profiles**. Eleven
  public-domain and one open-license documents enter the current reuse-eligible
  category; 29 unknown-rights documents remain research-only under existing policy.
- M8: seven final actual images and 21 linked JSON files. All images decode and
  all JSON files pass schema/ID ownership checks. Leipzig's example is 3840×5760;
  the others are mostly 1000-pixel native previews, not archival-resolution claims.
- Oldenburg's native preview has a 50-pixel attribution border: actual
  **1000×1254**, declared image body **1000×1204**. Preserve the discrepancy and do
  not align OCR coordinates without accounting for it. Other six examples match
  declared image-body dimensions. The original blank Oldenburg choice was
  archived and replaced with Canvas sequence 25 of the same Manifest. Eight
  distinct images were downloaded in total; the final index has seven bundles.
- No institutional page-reference texts are declared in this sample. All bundles
  are `without_reference`. The 72 generic ground-truth candidates are not 72
  institution-provided correct transcriptions. Previous reference pairs remain.
- All **41 valid sample Manifests** were checked using institution labels or
  `Online-Ausgabe` metadata. Their URL sets do not overlap between these sources.
- Seven first-page fallback recipes were separately executed with two results
  each. Five next-page pairs were fetched and differ. Seminary and the selected
  Leipzig static Collection have no declared next link at this level.
- Extra scope runs: Koblenz, Worms and Graz each discovered 24 unique URLs;
  Seminary discovered 12 URLs. All Collection requests retain the correct branch.
  These extra URL discoveries are not additional freshly M4-validated objects
  and are not added to the 41-object or 8,564-image-association totals.
- M3–8 automated tests: **193 passed, plus seven subtests**. Runtime modules and
  downstream schemas unchanged this batch. The scope rule introduced for Dilibri
  was reused at Graz through configuration only; no runtime AI API was added.
- Knowledge **59→66 entries**; all old 59 entries and 19 curated endpoint entries
  are unchanged. Old source records/endpoints were not overwritten.

## Other leads retained without promoting them as successes

- **Rijksmuseum:** the [official tutorial](https://data.rijksmuseum.nl/tutorials/iiif/)
  and live Change Discovery root/page work, but their events use `Manifest` type
  for metadata serializations as well. A type label in an event is not proof of
  an IIIF Presentation Manifest. The documented Linked Art
  object → VisualItem → DigitalObject → Micrio image/Manifest chain is a future
  candidate recipe; it was not executed end to end in this batch and is not counted.
- **Freiburg and Dresden:** public OAI-PMH METS catalogue responses were saved.
  They are not counted because the Manifest-to-image chain was not verified here.
- Candidate routes for Mannheim, Salzburg, Stuttgart, Duesseldorf, Bremen,
  Dortmund and Duisburg-Essen raised URLError. A Kassel candidate returned 404.
  These failures do not establish absence of IIIF, and no restriction was bypassed.

## Reproduction without chat history

The batch's `运行命令.txt` lists the isolated M2→M8 commands and output folders.
`institution_ownership_rules.json` records which source field and institution
tokens must match. The new reusable audit utility accepts any prepared directory:

```powershell
& $PipelinePython Code_git/Module_3/tools/verify_native_collection_recipes.py --evaluation-root $EvaluationRoot --ownership-profile "$EvaluationRoot/institution_ownership_rules.json"
```

It saves fallback, pagination, scope and provenance checks. It validates reviewed
recipes; it does not independently investigate an unfamiliar institution or turn
our conversation into an autonomous learning system. That architectural gap
remains explicit in the Chinese midterm-ready report.
