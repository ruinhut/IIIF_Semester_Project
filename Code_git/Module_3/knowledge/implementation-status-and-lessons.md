# Implementation status and lessons

## 2026-11-06 — scope checked against the personal assignment

- Re-read pages 59-60 of `Work_flow/工作流v1/工作流指导/工作目标与工作流程.pdf`,
  the personal sheet "One door to a scattered heritage". The four deliverables
  are provider census with scale/rights, unified cross-provider harvesting,
  normalization of identifier/date/place/rights/source, and a schema-conformant
  data slice for extraction and the Time Atlas. Aggregators are prioritized.
- M1-7 address that core; M8 and page-linked institutional references support
  downstream delivery. The task is not to develop an OCR engine or to replace
  the harvest with an OCR training-set project. "The front" means upstream
  data processing, not a requirement to build a web front end.
- The M7 profile is still explicitly provisional. Team-schema acceptance,
  downstream consumption and Time Atlas input compatibility have not been
  established merely by passing local schemas or downloading sample images.
  Unknown/missing descriptive fields must remain retained for research, while
  date/place coverage and source-scale evidence need further quality work.
- Recommended priority, not a new supervisor instruction: close the shared
  schema/data-slice handoff, document aggregator coverage and harvest limits,
  then improve reusable discovery/reliability. Optional LLM investigation and
  a small visual interface serve these deliverables; they do not replace them.
  Keep the confirmed research-retention policy and public-reuse restrictions.

## 2026-11-06 — research-policy regression fixed; all 100 sources freshly evaluated

- Corrected M6's legacy `decision != allow -> missing rights` quality gate.
  An explicit unknown/restricted rights category is present research metadata.
  `quality.research_usable` now follows retention and academic-analysis flags;
  public/commercial restrictions are preserved. Missing dates/places remain
  annotations rather than research rejection. Added German date-label support.
- Regression checks: M6 40 tests and M7 29 tests passed. The former test that
  expected an otherwise complete reuse-excluded record to be partial was fixed.
- Fresh evaluation froze the user's exact 100 historically validated source
  entries and all 139 supplied endpoints. M1–7 ran with up to three Manifests
  per source, fresh M4 retrieval and no runtime LLM. M8 was explicitly not run.
- Source progress, each denominator 100: M1 100; M2 reachable 88; M3 found URLs
  98; M4 accepted image Manifests 97; M5/M6/M7 research output 97.
  These source-level rates must not be replaced by conditional 275/275 rates.
- M2 checked all 139 candidates; 118 returned HTTP 2xx. The other 21 were:
  HTTP 403 (8), 401 (1), 429 (1), 404 (4), 400 (2), 405 (1), 502 (1),
  an uncompleted 308 redirect (1), and client/network errors without an HTTP
  response (2). Do not attribute every unsuccessful check to the institution:
  two Internet Archive requests still contained an unexpanded `:id` placeholder,
  and a Toronto candidate contained Markdown URL residue. These are input/
  request-handling defects to address, not evidence that IIIF is unavailable.
  M1's 100/100 means successful selection/export, not validated endpoint quality.
  Initial parseable JSON was returned by 30 endpoints from 29 sources; the
  remaining reachable endpoints returned HTML/XML, which can support M3.
- M3 yielded 280 source-Manifest observations / 274 unique URLs. M4 accepted
  275 observations / 269 unique URLs; all 275 were retained and normalized for
  research and exported. M7 exported 44,915 image associations (44,252 distinct
  download URLs), 275 OCR profiles and 7,232 reference descriptors. No image
  download success was measured; declared URLs are not downloaded files.
- 237 public-reuse-excluded records, including 132 unknown-rights records, remain
  in the research output. They were not relabelled public-reuse eligible.
- Leipzig: initial Collection requests failed with a local/client network error.
  Wales: homepage 403 plus catalogue timeout. Northwestern: M3 found three
  Manifests, but this sample contained no image bodies and was not accepted by
  M4 for OCR. These observations do not prove the institutions lack IIIF/images.
- Full outputs, configs, per-source CSV and evaluation summary:
  `../../Pipeline_Runner/data/midterm_100_20261106_123034/`.
  Reproduction: `Pipeline_Runner/tools/run_midterm_100_sources.py` and
  `Pipeline_Runner/tools/chart_midterm_100_sources.py`. Figures use this run,
  replacing the former selected-seven-source presentation figures.
- The same rules were written into the actual project's global SKILL.md and
  linked `references/research-retention-and-evaluation.md`, not just this log.
- Demo instructions were checked against the actual launcher: `pipeline.py`
  and `pipeline.cmd` are in the repository root (`Semester_Project`), while the
  environment and modules are under `Code_git`. Corrected the presentation's
  erroneous Code_git working-directory instruction. A fresh M1-8 fixed-EPFL
  plan passed dry-run with force-refresh and no LLM; this check did not execute
  live harvesting or M8 downloads. Step-by-step Markdown and PowerShell text
  commands are stored with the midterm presentation materials.
- Subsequently ran a separate paired historical presentation demo with
  `Pipeline_Runner/tools/run_presentation_demo.py`: two independent fresh M1-8
  runs, one BSB 1694 print with retrieved page-linked hOCR, and Fragmentarium
  F-u3vo (source date 1275-1325) without declared page-linked text. Each case
  downloaded one image, with zero image/reference failures or cache hits.
  Six base JSON files passed schema/ID checks; both raster images decoded and
  were visually reviewed. The BSB hOCR page dimensions/word boxes match its
  image. See `../../Pipeline_Runner/verification/2026-11-06_paired_heritage_demo.json`.
  This is independent of the 100-source M1-7 evaluation. The demo wrapper calls
  the existing launcher twice and does not alter production download-example
  semantics (one successful image over an entire input). No LLM was invoked.


## 2026-11-05 — local midterm snapshot, unified CLI and optional LLM discovery

- Before modification, saved local commit `ff46048`, message `期中汇报使用版本`.
  UI implementation is deferred at the user's request. No new provider census
  entries or replacements of reviewed discovery knowledge are part of this work.
- Root `pipeline.py` / `pipeline.cmd` support one-command setup and ordered
  module selection (`--modules`, `--module-count`, or from/to), isolated run
  directories, configuration snapshots, and resumption at module boundaries.
  Existing module CLIs and the configured runner remain available.
- New M3 LLM integration is explicitly opt-in. Credentials come from a hidden
  prompt, environment or local token file; config snapshots contain no token.
  Responses and compatible Chat Completions protocols are supported, with an
  explicit user-selected model. Hosted web search is a separate Responses option.
- Existing methods run first. Unresolved providers may use saved learned
  recipes or a bounded model investigation. The model can inspect public URLs
  and propose data-only recipes, but cannot execute code or supply HTTP auth.
  Native Presentation context, Manifest type and declared Canvas checks gate
  learning; M4 remains responsible for full structural validation.
- Verified new recipes and their evidence are atomically written to a separate
  `config/learned_discovery_knowledge.json`. Reuse performs fresh HTTP checks and
  does not need a model key. The reviewed `discovery_knowledge.json` is preserved;
  downstream M3–M4 contracts and M4–M8 provider-independent behavior stay intact.
- Per-provider model calls and public retrievals are bounded; failures remain
  unresolved and appear in `llm_investigation.jsonl` under the log directory.
  This is recipe learning, not model fine-tuning or proof of arbitrary-provider
  generalization. Generated recipes currently use public GET retrieval only.
- CLI live acceptance: EPFL item 44 passed M1–M3, then resumed M4–M8, with one
  fresh valid Manifest, 415 image records, and one decoded image plus three
  schema/link-checked JSON records. Evidence:
  `../../Pipeline_Runner/data/cli_validation_20261105/`.
- A simulated local Responses service supplied an EPFL API/ID/template recipe;
  real public HTTP verified `/api/items?id=44` → `/iiif/3/44/manifest`. A second
  execution reused the saved recipe without a model key. This tests protocol and
  execution plumbing, **not** a paid model's independent investigation ability.
  Evidence is in that run's `llm_public_recipe_replay/verification.json`.
- No real user model credential was available; no paid LLM evaluation was run.
  Do not report the simulated token-usage counters as real consumption or claim
  the historical source coverage increased from this work.


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

## 2026-10-22 — KU Leuven restored and four public libraries added

- Restored the old KU Leuven entry through the public Lovaniensia catalogue and
  its explicit detail-page Manifest links. All six sample locations identify KU
  Libraries Special Collections. Its restricted Omeka API was not bypassed.
  Preserved the existing ID, Limo endpoint and source fields, adding one endpoint.
- Registered Karlsruhe, Bonn, Frankfurt and Paderborn libraries. Their verified
  native VisualLibrary Collections reuse existing members/next traversal. All
  four next pages and KU's second result page contain different records.
- Census 102→106; cumulative validated sources **74→79/106**. Within the original
  94-entry census, 67 are resolved and **27 remain unresolved**. Cumulative
  history was not all re-fetched today; some source entries are aggregators.
- M3 found 30 URLs; fresh M4 accepted 29 and rejected one Frankfurt Manifest with
  no sequences/Canvases. M5–7 exported 29 records, **6,539 image associations** and
  29 OCR profiles. No institutional reference text was declared in this sample.
- M8 final output has five real images and fifteen linked JSON files; all decode
  and schema checks passed. Six distinct images were downloaded in total: the
  initial blank Frankfurt example was archived and replaced by a text-bearing
  Hebrew-script page. No additional image associations are claimed as downloaded.
- Three VisualLibrary previews add a 50-pixel attribution border; actual height
  exceeds the declaration. Preserve actual dimensions before OCR alignment.
  Corrected the evaluation summary to distinguish mismatch, smaller and larger.
- Knowledge 47→52; all old 47 entries and 19 curated entries preserved. Runtime
  modules and schemas unchanged, no runtime AI API added. M3–8 tests: **187 passed
  plus seven subtests**. Failed 403/challenge/URLError probes were not successes.

See [the investigation](institutions/2026-10-22_five_provider_completion.md),
[the reusable procedure](skills/public_catalogue_details_and_native_collections.md)
and `../evaluation/2026-10-22_five_provider_completion/` for reproducible evidence.

## 2026-10-22 — seven additional libraries, target 86 reached

- Added Vienna/Wienbibliothek, Detmold, Cologne's diocesan/cathedral library,
  Rheinland-Pfalz State Library Centre, Mainz City Library, Trier City Library
  and Trier University Library. All previous 106 census records are unchanged.
  Cumulative historical evidence: **86/113 source entries**, still 27 unresolved
  old entries. This is not a deduplicated institution count or a full harvest.
- All seven public native Collections passed M2; M3 found 42 unique URLs.
  M4 fetched all 42 freshly and accepted 41; one Trier City member returned 404.
  M5–7 exported **41 records, 2,303 image associations and 41 OCR profiles**.
- Final M8 output has seven actual images and 21 linked JSON files, all decoded
  and schema/ID verified. Actual dimensions match image-body declarations; these
  are mostly 1000-pixel previews, not archival-resolution claims. Two initial
  blank-page examples were archived and replaced; nine distinct images were
  downloaded in total. No institutional reference text was declared in this run.
- Added opt-in, same-origin Collection-prefix mappings to prevent a shared
  platform's child/next URLs from dropping virtual-library scope. Runtime has no
  new hard-coded institution IDs/hosts; old provider behavior is unchanged.
  Invalid rules are recorded, not executed; scope audit events do not inflate
  discovery-skill execution counts. Manifest and downstream contracts unchanged.
- Seven next-page pairs differ. Four independent Dilibri libraries each passed
  a 24-unique-URL M3 traversal with scoped Collection requests. Their 23 valid
  downstream Manifests were checked against attribution/Online-Ausgabe; no
  inter-library Manifest URL overlap. These extras are not added to 41 records.
- Six new regression tests. M3–8: **193 passed plus seven subtests**. Knowledge
  **52→59**, all old 52 and 19 curated entries preserved. No runtime LLM API.
- Finna/Illinois 403, NCSU 401, Hamburg browser challenge and other probe errors
  remain failures, not absence-of-IIIF claims. Native public JSON availability
  is distinct from blocked HTML catalogue pages; no challenge was bypassed.

See [the seven-library investigation](institutions/2026-10-22_seven_provider_completion.md),
[the reusable scope procedure](skills/virtual_institution_collection_scope.md)
and `../evaluation/2026-10-22_seven_provider_completion/` for reports and commands.

## 2026-10-22 — second seven-source batch, target 93 reached

- Added Oldenburg State Library, Leipzig University Library, Graz University
  Library, Potsdam/Digitales Brandenburg, Koblenz City Library, Worms City Library
  and Trier Seminary Library. All old 113 census records remain unchanged.
  Cumulative bounded-run evidence: **93/120 source entries**; the original census
  still has 27 unresolved entries. This is not a deduplicated institution total.
- M2: 7/7 native Collection roots reachable. M3: 42 unique URLs; M4 freshly
  attempted 42, accepted 41 and preserved one Seminary Manifest 404. Cache hits 0.
  M5–7: **41 records, 8,564 image associations, 41 OCR profiles**, no institutional
  page-reference texts. The 72 candidate ground-truth rows are not correct texts.
- M8: seven final real images and 21 schema/ID-verified JSON files, all images
  decoded. Leipzig 3840×5760; most others 1000-pixel previews. Oldenburg adds a
  50-pixel attribution border; actual 1000×1254 versus 1000×1204 declared.
  An initial blank page was archived/replaced; eight distinct images in total.
- Reused Collection/members/manifests traversal and the existing scope mapping
  at another platform (Graz). No runtime module/schema changes and no runtime
  AI API added. Graz next offset is 10, so follow native next, not a guessed 20.
- Seven fallback recipes independently checked, five different next-page pairs,
  and four scoped runs (24/24/24/12 unique URLs). Extra discovered URLs are not
  extra M4-valid objects. All 41 source labels/edition publishers checked; no
  inter-source Manifest URL overlap. Potsdam publisher is not original ownership.
- Knowledge **59→66**, old 59 and 19 curated entries preserved. M3–8 tests:
  **193 passed plus seven subtests**. Added a reusable directory/profile-driven
  native Collection audit command so checks do not require conversational context.
- New lesson: Rijksmuseum CD may label ordinary metadata representations as
  Manifest. Validate Presentation context/Canvases after resolving the documented
  Linked Art chain; do not count a Change Discovery type as success. This lead,
  working Freiburg/Dresden OAI catalogues and failed routes remain unpromoted.

See [the investigation](institutions/2026-10-22_second_seven_provider_completion.md)
and `../evaluation/2026-10-22_second_seven_provider_completion/` for the Chinese
midterm wording, measured counts, actual bundles, provenance and commands.

## 2026-10-22 — third seven-institution batch, 100 source entries

- Added Kassel University Library, Humboldt University Library, Berlin Central
  and Regional Library, Kiel University Library, Kiel City Archives, SLUB Dresden
  and Upper Austrian State Library. All old 120 census records are unchanged.
  Cumulative bounded-run evidence: **100/127 source entries**, still 27 unresolved
  original entries; not a deduplicated institution count or a full catalogue run.
- M2: seven reachable roots (six XML, one native Collection JSON). M3 found 42
  URLs; M4 freshly retrieved **42/42 valid**, zero cache hits. M5–7: **42 records,
  7,123 image associations and 42 OCR profiles**. M5 research retains all objects;
  14 public-reuse allow, 28 exclude, without turning unknown into public domain.
- Reused existing XML identifier/template and native Collection skills; no
  runtime module/schema changes. Five RSS recipes cover capped 50-record feeds,
  **not full enumerations**. Linz's selected Collection has 466 declared members;
  SLUB's OAI continuation was independently checked across two distinct pages.
- Independent rechecks: seven recipes × two validated responses; all 42 URLs
  distinct across sources. Both Kiel holders' native owner fields verified on
  all 12 Manifests. The shared portal is not counted as an extra institution.
- M8: seven final real images and 21 schema/ID-verified JSON files, all decoded
  and matching Manifest dimensions. Six native services permit larger images
  than the original preview URLs. An explicit **evaluation helper** reads their
  declared info.json and requests supported full-size representations; production
  M7/M8 defaults remain unchanged. SLUB's service itself is a 1000×1509 medium
  image. Blank/cover/low-resolution first examples remain in `initial_examples/`.
- Linz declares 3,504 reference descriptors: **3,498 image-linked and six
  Manifest-level**. Actual final download: one source ALTO and plain text paired
  with Canvas 21. Image and ALTO both **2882×4629**, 159 word boxes inside bounds.
  This is provider OCR, not certified manually corrected ground truth. Final
  outputs split one `with_reference` and six `without_reference` bundles.
- Tests M3–8: **193 passed plus seven subtests**. Knowledge **66→73**, all old
  66 and 19 curated entries unchanged. No runtime AI API/autonomous investigator.
- Failures retained: ZLB year-volume timeout, Lübeck external image URLError,
  GWLB new-ID template 404 despite working old example/OAI, Weimar feed timeout.
  They are not absence-of-IIIF findings or additional resolved sources.

See [the investigation](institutions/2026-10-22_third_seven_provider_completion.md),
[the reusable catalogue/image procedure](skills/public_rss_oai_and_image_representations.md)
and `../evaluation/2026-10-22_third_seven_provider_completion/` for Chinese results,
CSV counts, linked samples, reference alignment and reproducible commands.
