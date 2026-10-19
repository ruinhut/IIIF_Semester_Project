# Implementation status and lessons

## 2026-10-19 — fresh full-chain acceptance and reference routing

- Reproducible runner: `../../Pipeline_Runner/tools/run_full_acceptance.py`.
  Evidence: `../../Pipeline_Runner/data/full_acceptance_2026-10-19/`.
- Three fixed real Manifest inputs (BSB, FromThePage, EPFL) each completed
  Modules 1–8, with fresh M4 fetches and actual M8 downloads. This tests module
  handoffs, not homepage discovery, exhaustive harvesting or added providers.
- M7: three records, 479 image associations, three profiles, 157 reference
  rows; all 485 record/media/profile rows schema-valid. All 157 reference IDs
  survive M6→M7; 154 page-linked rows match resource IDs and Canvas ownership.
- M8: three real JPEGs and nine linked JSONs; BSB has one hOCR reference,
  FromThePage has four variants for one page, EPFL has no declared reference.
  The two paired samples are in `with_reference`; EPFL is in
  `without_reference`. Zero image or reference download failures; dimensions
  match source declarations. A failed reference is not an absent reference.
- Unit tests: M1–8 plus Runner, 194 passed and 12 subtests passed. This includes
  reference-failure routing and the download-all path under controlled inputs.
- Known gap remains: M6 does not yet fetch external P2 otherContent
  AnnotationLists or external P3 AnnotationPages. Do not infer universal
  reference detection from these two tested reference-delivery styles.


## 2026-10-19 — third five-source investigation

- Verified sources: DRI (Hingston nested Collections), Princeton University Art
  Museum (official object API with maker filtering and offset pagination), UCLA
  (Blacklight work ARKs), SCTA (text Collections), and Smithsonian (official
  featured Manifests). All have explicit scope limits in their provider recipes.
- Evidence: `../evaluation/2026-10-19_third_five_provider_completion/` contains
  30 independently fetched M4-valid Manifests, 3,693 image associations with
  3,685 distinct image URLs, five actual images and 15 linked JSON files.
- M3–8 tests: 160 passed plus seven subtests. Five image bundles passed schema,
  relationship, file-integrity and actual pixel-decoding checks. Two examples
  are smaller than their Canvas declarations; original-resolution OCR alignment
  is not claimed.
- Cumulative successful source entries increased from 44 to 49 of the existing
  94 entries; 45 remain unresolved. Existing learned recipes were retained.
- A new generic compatibility option accepts only the exact known legacy
  Shared Canvas context when explicitly enabled. M4 retains source bytes and
  flags `source_format: legacy_shared_canvas`; parser version 2 is a structural
  compatibility selector, not a claim of modern Presentation 2 conformance.
- Plain catalogue HTML seeAlso pages were incorrectly becoming reference text.
  M6 now requires a transcription/full-text signal for HTML seeAlso resources,
  while keeping inline supplementing text and explicit OCR resources. This
  sample delivers no verified OCR reference pairs. SCTA external AnnotationLists
  remain a separate uncompleted text-enrichment investigation.
- Folger browser challenges, Illinois 403, Getty's unsuccessful documentation
  migration, Parliamentary bulk-enumeration failure and a stale Cultural Japan
  example are retained as failed/partial investigations, not counted successes.

See [the third investigation](institutions/2026-10-19_third_provider_completion.md).

## 2026-10-19 — resumed five-source investigation

- New verified source entries: Princeton University Libraries, University of
  North Texas Libraries, Harvard University Digital Collections, Stanford
  University, and the Biblissima aggregator. Each has six independently
  fetched, structurally validated Manifests and one real downloaded image with
  its three linked JSON files. Coverage is explicitly scoped in each recipe.
- Evidence: `../evaluation/2026-10-19_resumed_five_provider_completion/summary.json`,
  `provider_results.csv`, `sample_downloads.csv`, stage logs and pixel/schema QA.
- Module 3–8 tests: 157 passed, plus seven subtests. Module 7 exported 30
  document records and 2,103 image associations; five images were actually
  downloaded. Three sample images have fewer pixels than their Canvas declares.
- Cumulative evidence: 39 to 44 of the existing 94 source entries; 50 unresolved.
  This is not an independent-institution count or an exhaustive fresh audit.
- Learned skills: single-object detail responses, extracting delivery IDs from
  declared links, pre-filtering mixed metadata URLs, and bounded HTML refresh
  migrations. Public catalogue APIs or declared indexes can serve as discovery
  routes even when the main HTML search is blocked or challenged.
- Villanova remained HTTP 403 and was not promoted. Empty Collections, HTML
  challenge pages, stale metadata links and actual usable resources are distinct
  outcomes. Preserve failures rather than treating them as absence of IIIF.
- A descriptive `text/xml` seeAlso link is not OCR. Module 6 now requires an OCR
  or transcription signal for generic XML, while retaining explicit ALTO/hOCR
  and page transcriptions. This sample contains zero verified OCR references.
- Previous executable knowledge was preserved: 16 to 20 recipe entries, 15 to
  16 curated endpoint entries, with all old entries unchanged.
- Production configuration was promoted after the entire sampled handoff and
  image verification, not after finding plausible URLs. Temporary route-probe
  bodies were removed with a cleanup manifest; source Manifests, final outputs
  and essential evidence remain.

See [the dated investigation](institutions/2026-10-19_resumed_provider_completion.md)
and [the reusable skill notes](skills/declared_detail_and_migration_links.md).
