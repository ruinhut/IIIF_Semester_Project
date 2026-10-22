# Implementation status and lessons

## 2026-10-21 — second batch: five more completed source entries

- Added BSB East Asia, Cardiff, Leeds, vHMML and Yale Library from the existing
  census. Evidence: ../evaluation/2026-10-21_second_five_provider_completion/.
- M4 freshly validated 26 Manifests (zero cache hits); M7 exported 7,918 image
  records/unique URLs. M8 downloaded five real images plus 15 linked JSONs.
  Schema/ownership and full image decoding passed; sample dimensions match.
- BSB East Asia contributes 5,256 declared hOCR descriptors. Only selected OCR
  content was fetched: descriptors are not 5,256 confirmed training labels.
  Final sample Canvas 10 has Chinese text, 157 word spans and page/image bbox
  1731×2996. It is provider OCR, not manually certified gold truth.
- Corrected M8's empty-hOCR false positive: title-only filenames are ignored;
  existing failed-reference routing now catches pages without body text.
  M7 percent-encodes spaces/Unicode while retaining raw source image IDs.
- M3 adds opt-in HTML detail follow-up (anchors/visible URL text, no scripts).
  Cardiff uses documented MMS-ID-to-representation resolution; Yale Library
  reuses Linked Art detail traversal. Leeds is a curated workshop subset;
  vHMML uses the public DREAMSEA Laos subset. None proves full-catalogue coverage.
- Cumulative evidence 59→64/94 source entries; 30 outside the completed set.
  Entries include collection subsets and aliases, not 64 independent world
  institutions. Historical successes were not all refreshed in this run.
- Tests: 179 passed plus seven subtests. Production knowledge entries 33→37,
  curated entries 18→19; all old configurations are preserved exactly.
  No automatic GitHub push or runtime LLM API was added.

## 2026-10-21 — five additional sources with real image bundles

- Completed source entries: DigiVatLib, Getty, Cultural Japan, Harvard Art
  Museum and National Gallery of Art Library. Final evidence is in
  ../evaluation/2026-10-21_five_provider_completion/.
- M4 independently fetched 26 unique Manifests (zero cache hits); M7 exported
  2,991 image associations/URLs. Per-source sums are larger because Cultural
  Japan also discovers one Harvard Manifest. M8 downloaded five real images
  and 15 linked JSONs; schema/link checks and pixel decoding passed.
- NGA's image is 2818×4096 versus Canvas 3302×4800; preserve this difference
  before page-coordinate alignment. Getty/Harvard samples are small declared
  derivatives, not certified archival originals.
- Cumulative completed-source evidence increases 54→59/94; 35 entries remain
  outside that set. Europeana is partial: six native Manifests were fetched
  in the initial batch but media were restricted, stale or non-image. It was
  replaced by NGA, not counted as a completed sixth source. Previous source
  successes were not all refreshed today; the census includes aggregators.
- M3 adds opt-in mapping_values records and numeric query parameter templates,
  marks failed catalogue traversal partial, and corrects the diagnostic for
  reachable HTML skipped by an intentionally disabled crawler.
- M6 excludes unknown-format/JSON seeAlso Text links without transcription
  evidence; Getty catalogue metadata is not OCR reference text. Final sample
  has zero OCR references and five without_reference bundles. Existing OCR
  fixtures still pass. M3–8 tests: 173 passed plus seven subtests.
- Five recipes are promoted locally, 28→33 knowledge entries; old entries and
  all 18 curated endpoint configurations are preserved. No runtime AI API was
  added and no automatic GitHub push was performed.

## 2026-10-20 — five additional sources validated

- New source entries: Ghent University, St Andrews, Yale Center for British
  Art, Yale Peabody Museum and Yale University Art Gallery. The three Yale
  museums share LUX discovery code and have distinct native Manifest namespaces.
- Evidence: ../evaluation/2026-10-20_five_provider_completion/. Module 4 freshly
  fetched and validated 28 Manifests; M7 exported 1,245 image associations;
  M8 delivered five real images plus 15 linked JSONs. Pixel decoding, dimensions
  and schema/relationship checks passed. These are bounded samples.
- Existing census coverage increases from 49 to 54 of 94 source entries; 40
  remain unresolved. Older successes were not all re-fetched today. Prior
  executable recipes remain unchanged; five new knowledge entries are appended.
- Generic M3 improvements: opt-in record_url_attributes (data-manifest etc.)
  and scalar numeric-index paths for filters and declared totals. M6 now
  excludes RDF Dataset metadata from reference text. Tests: M3–8, 166 passed
  plus seven subtests; this is not a claim that the full test count shrank.
- St Andrews yielded four Manifests from two API pages, then HTTP 429. Its
  route is usable but enumeration is incomplete. A false low-level truncated
  flag must not be read as a complete harvest when fetch failures are present.
- This source sample has zero verified OCR references. British Art's six RDF
  seeAlso links remain in source Manifests, outside the reference-text output.
- Local changes from this investigation have not automatically been pushed to
  the earlier GitHub export; publication is a separate action.


## 2026-10-19 — existing reference output audit: pairs versus ground truth

- Audited primary Code_git outputs, excluding the temporary GitHub export:
  201 saved with_reference bundles, deduplicated to 199 Manifest/Canvas image
  pairs and 199 different image byte contents. Sources: Blavatnik 196, BSB two
  pages from two Manifests (provider-name aliases merged), FromThePage one page
  with four text variants. Repeated run copies are not additional examples.
- All 201 images decoded; linked IDs and saved nonempty reference files passed.
  For all 196 Blavatnik records, cached API originalTranscript matches exported
  text after HTML cleanup; single catalogue image identifier matches output.
- Critical quality distinction: manual inspection of Blavatnik item 13606
  shows the supplied originalTranscript is abridged (ellipsis and omitted page
  content). Pair association and nonempty institutional text do not certify
  complete verbatim transcription. Do not report 199 pairs as 199 gold OCR pages.
- Report: ../../Pipeline_Runner/output/参考文本现存输出核查_2026-10-19.md.
  Detailed read-only audit: workspace tmp/reference_output_audit_2026-10-19.json.


## 2026-10-19 — GitHub code publication

- Authorized public destination: `https://github.com/ruinhut/IIIF_Semester_Project`,
  branch `main`, verified remote commit `b2e0ad10cacdaffdb2d1a3a1de26b9331a6a2c62`.
- Includes all 174 Python source/test/helper files from Modules 1–8 and Runner,
  configurations, schemas, discovery knowledge, CMD documentation and a compact
  verification summary. Runtime datasets, virtual environments, raw caches,
  personal documents and weekly-report emails were excluded.
- Publication used an independent clone at workspace-relative
  `tmp/github_publish_2026-10-19`; the original workspace Git history and
  remotes were not replaced. Future uploads must deliberately sync source
  changes into this clone or a fresh clone; do not push the whole workspace
  history, which includes unrelated project documents.
- The upload copy has its own environment and passed 194 tests plus 12 subtests
  and three fresh full-chain live cases before pushing. System GitHub login
  was completed by the user; remote HEAD and raw README content were verified.


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

## 2026-10-21 — third five-source update, including three census additions

- Restored two old source entries: British Library (public digitised highlights)
  and Indigenous Digital Archive (its DigiTreaties project, not the whole former
  archive). Added Heidelberg University Library, Japan's National Diet Library,
  and the Victoria and Albert Museum through Module 1's parser and manual source.
- Cumulative evidence is now **69/97 source entries**: 66/94 original entries,
  plus three additions. The old census still has 28 unresolved entries. Earlier
  successes were not all requested again; source entries are not necessarily
  independent institutions. All old IDs and endpoints were preserved.
- Evidence: `../evaluation/2026-10-21_third_five_provider_completion/summary.json`,
  Chinese report, `provider_results.csv`, `sample_downloads.csv`, request traces,
  native Manifests, stage logs and schema/pixel verification reports.
- Module 4 freshly fetched 25 Manifests, all valid, zero cache hits. Module 7
  exported 25 documents and 3,635 image associations. Module 8 saved five real
  JPEGs with 15 linked JSON files; all decode and pass schema/ownership checks.
  NDL's sample is downscaled to 3340×2203 versus a 6680×4406 Canvas declaration.
  These counts are bounded samples, not entire catalogues or 3,635 downloads.
- Added namespace-aware XML catalogue discovery with numeric RSS pagination,
  attribute extraction, opaque OAI continuation tokens and deleted-record/error
  handling. Existing JSON/HTML skills and the downstream contract are unchanged.
- Module 3–8 tests: 182 passed, plus seven subtests. Knowledge recipes increased
  37→42; all old 37 recipes and 19 curated endpoint entries remain unchanged.
- Preserve failures: one NDL candidate Manifest returned 404; an IDA sample
  pointed to a restricted legacy image (403). No restriction was bypassed; an
  explicitly public NARA image supplied the final IDA example. Do not infer all
  image links are downloadable from Manifest validity. No institutional reference
  text was declared in this sample; outputs are `without_reference`.
- NDL OpenSearch only exposes the first 500 query matches; use partitioned
  searches or documented, date-bounded OAI harvesting for catalogue-wide work.
- V&A generic discovery found one Manifest before its fallback recipe ran. The
  configured identifier recipe was separately live-tested with six valid results;
  those are not added to the 25-object downstream total. No runtime AI API was added.

See [the dated investigation](institutions/2026-10-21_third_five_provider_completion.md)
and [the reusable XML skill](skills/xml_catalogue_discovery.md).

## 2026-10-21 — fourth five-source update, all five institutions newly registered

- Added Berlin State Library, National Library of Norway, Pennsylvania State
  University Libraries, University Library of Bern and University of Manchester
  Library. All previous 97 census records remain unchanged; current census 102.
  Cumulative bounded-run evidence is **74/102 source entries**, with the same
  28 old unresolved entries. Earlier successes were not all re-fetched today.
- Evidence: `../evaluation/2026-10-21_fourth_five_provider_completion/`, including
  Chinese report, provider and sample-path CSVs, request traces, native Manifests,
  schemas, decoded-pixel checks, source snapshots and reference-pair QA.
- M4 fetched all 24 discovered Manifests freshly, all valid, zero cache hits.
  M7 exported 24 documents, 10,194 image associations and 97 ALTO reference
  descriptors. M8 initially downloaded five images and one reference, no failures.
  A later M8 run cached those five images and regenerated clean reference text.
- Berlin's reference pair is stored in with_reference: image 2221×3540, ALTO Page
  2221×3540 pixels, 47 words and 351 extracted characters. Other four examples
  are without_reference. Only one of the 97 reference URLs was downloaded here;
  institution OCR is not certified manually corrected ground truth. No word-level
  confidence is present in this sample, so none is fabricated.
- Fixed generic M8 ALTO extraction: processing settings and filenames no longer
  contaminate text. Namespace-aware String/CONTENT parsing preserves line order
  and entities; metadata-only ALTO takes reference_failed. Original XML remains.
- Added generic {page_end} query-template support for client-declared start/end
  pagination; verified distinct Manchester result ranges and 20-record pages.
  Existing XML skills handled Berlin OAI without institution-specific code.
- M3–8 tests: **187 passed plus seven subtests**. One new pagination test and four
  ALTO extraction/failure-routing tests were added. Old tests still pass.
- Knowledge recipes increased 42→47; all old 42 recipes and 19 curated endpoint
  entries remain unchanged. The three fallback recipes skipped after generic
  success were separately live-checked and their extra results not double-counted.
- All five sample images decode. Manchester delivers 1543×2000 despite a
  4243×5500 Canvas declaration; do not label the sample archival resolution.
  Counts are bounded project/query subsets, not complete institution totals.
- Trinity CAPTCHA, Cornell 403 and unreachable Edinburgh routes were not counted.
  Public metadata, public digitized content and valid downloadable images remain
  separate checks. Runtime AI API integration was not added.

See [the dated investigation](institutions/2026-10-21_fourth_five_provider_completion.md)
and [the reusable lessons](skills/range_catalogues_and_alto_reference_safety.md).
