# One Door to a Scattered Heritage

## Midterm presentation draft

更新：2026-11-06。正文为可挑选放入PPT的英文短句和口头说明。按最新调整采用八页结构：Module 4单独一页，Module 5–6合为一页；不安排每页时间。

**使用口径：** 统计采用11月6日100个来源的M1–7实跑，每个来源最多3份Manifest，M8未运行。指定PDF仍保留七机构旧样本统计，因此保留其页面结构，数字以最新Markdown、统计图和实跑记录为准。下文的 *sources* 指清单来源条目，包含项目和聚合门户，不等于去重后的100家独立机构。

---

## Slide 1 | Modular IIIF Harvesting Pipeline

### 可放入PPT的英文短句

- **Aim:** Collect scattered heritage resources and deliver linked images, metadata and institutional reference texts for downstream OCR work.
- Eight modules connect source selection, Manifest discovery, validation, metadata extraction, export and download.
- One command runs the selected modules and saves outputs and logs at each stage.

### 流水线图中的英文文本

```text
Registry | Official guides | Community lists | Maintained entries
                              |
                              v
M1 Provider Census and Selection
 -> M2 Endpoint Accessibility Checks
 -> M3 IIIF Manifest Discovery
 -> M4 Manifest Retrieval and Validation
 -> M5 Rights Classification
 -> M6 Metadata and Reference Extraction
 -> M7 Common-Schema Export
 -> M8 Image and Reference-Text Download
                              |
                              v
            Images + Linked Metadata + Available Reference Texts
```

分组名称：

| Modules | Group label |
|---|---|
| M1–2 | Provider Selection and Endpoint Checks |
| M3 | Manifest Discovery |
| M4 | Retrieval and Validation |
| M5–6 | Rights Classification and Metadata Extraction |
| M7–8 | Data Export and Resource Download |

### 口头说明

My work focuses on collecting and preparing resources for downstream OCR. The pipeline starts with a provider census and ends with downloadable images, linked metadata and institutional reference texts where available. Each module has a separate responsibility and saves its results, so a failed stage can be inspected and rerun. Module 3 determines which sources can contribute resources; Modules 7 and 8 package the results for the next researcher.

**配图：** 使用更新后的八模块总览。若补充整体结果，使用[图00](中期汇报/Fig/00_Pipeline_Success_and_Retention.png)。

**图00解释：** Across the same 100-source cohort, Module 3 found Manifest URLs for 98 sources, and Modules 4–7 produced image-document outputs for 97. Module 8 was excluded from this evaluation.

---

## Slide 2 | Modules 1–2: Provider Census and Endpoint Checks

### 可放入PPT的英文短句

- **Module 1:** Combine source lists, preserve candidate endpoints and provenance, and select sources for a run.
- **Module 2:** Check every supplied endpoint and record accessibility, HTTP status, response time, content type and JSON parsing results.
- All **100 sources** were selected, preserving **139 candidate endpoints**.
- **118/139 endpoints returned HTTP 2xx**, and **88/100 sources had at least one reachable supplied endpoint**.
- HTML and XML responses can also support discovery.

### 三张能力图的内容

1. **Source consolidation:** Four source types feed a shared census; retain source names, evidence and candidate links.
2. **Selection and multiple endpoints:** Select one source or all sources, while preserving multiple routes for each source. 可结合[图01](中期汇报/Fig/01_Module1_Census_and_Selection.png)。
3. **Endpoint checks:** Show status, content type and response time, alongside [图02](中期汇报/Fig/02_Module2_Endpoint_Checks.png)。

### 口头说明

Module 1 preserves the available routes instead of keeping only the first link for each source. Module 2 then checks all 139 supplied endpoints. Of these, 118 returned successful HTTP responses. The responses included 30 JSON, 8 XML and 80 HTML endpoints. JSON was directly available from 29 sources. An HTML or XML response may still lead to Manifests through further discovery, so accessibility and resource discovery are measured separately.

### 未完全通过的原因，可用于图注或答疑

Twenty-one endpoint checks did not return HTTP 2xx: nine access-denied or authentication responses, one rate-limit response, four not-found responses, three invalid-request or unsupported-method responses, one gateway error, one incomplete redirect and two client/network errors.

Some failures came from our current input cleaning and request handling: two Internet Archive URLs still contained an unexpanded `:id` placeholder, and one Toronto URL contained malformed Markdown link text. These need correction rather than being interpreted as unavailable institutional resources.

**本页结论：** Preserve multiple routes and distinguish endpoint accessibility from resource discovery.

---

## Slide 3 | Module 3: Manifest Discovery

### 可放入PPT的英文短句

- A reachable institutional homepage does not necessarily provide an immediately traversable Manifest catalogue.
- Discovery combines native IIIF traversal with catalogue APIs, HTML extraction and configurable URL templates.
- **98/100 sources yielded Manifest URLs in the current run.**
- **280 source–Manifest observations represented 274 distinct Manifest URLs.**
- Historical investigations had already validated Manifest access for all 100 selected sources.

### 已实现的发现能力

- Direct Manifest detection.
- IIIF Collection traversal and pagination.
- Change Discovery Activity Stream traversal.
- Explicit IIIF links in HTML, embedded data and JSON APIs.
- Catalogue recipes using JSON APIs, XML, RSS or OAI-PMH.
- Reusable pagination, identifier extraction, detail lookup and Manifest URL templates.

### 用EPFL说明发现方法

```text
EPFL Plume
 -> Omeka S catalogue API
 -> Extract item identifiers (o:id)
 -> Construct and validate IIIF Manifest URLs
 -> Read Canvases and declared image resources
```

Plume item pages already expose IIIF links. The catalogue API provides a more efficient route to enumerate items and locate their Manifests.

### 口头说明

The main difficulty is discovering resources from different institutional entry points. I addressed this by separating reusable discovery operations from provider configuration. For example, EPFL Plume uses an Omeka S catalogue API to expose item identifiers, which can be used to locate standard IIIF Manifests. The same execution skills can be reused with different API paths, pagination settings and Manifest templates. In the current live run, 98 of the 100 historically validated sources yielded Manifest URLs.

### 本轮未完全通过的原因

| Source | Current observation |
|---|---|
| Leipzig University Library | The Collection request failed with a client/network error. |
| National Library of Wales | The homepage returned HTTP 403, and the catalogue API request timed out. |
| Northwestern University | Module 3 found three Manifests, but all three sampled items had no image bodies and were not accepted by Module 4 for OCR extraction. |

The first two cases explain the 98/100 discovery result. Northwestern explains why only 97 sources produced downstream image outputs. It needs image-aware sampling rather than stopping after any three Manifests.

**本页结论：** Reusable skills and provider configuration improve coverage; reliable sampling and complete catalogue enumeration still require further work.

**配图：** [图03：发现结果](中期汇报/Fig/03_Module3_Manifest_Discovery.png)；可选[图12：样本图像产出前20名](中期汇报/Fig/12_Image_Yield_by_Source.png)。

**图12解释：** Image yield varies substantially between the sampled sources because a Manifest can represent a single image or a multi-page document. These counts describe the up-to-three-Manifest samples, not entire institutional collections.

---

## Slide 4 | Module 4: Manifest Retrieval and Validation

### 可放入PPT的英文短句

- **Module 4:** Retrieve Manifests, validate their basic IIIF structure and inventory image resources.
- **275/280 source–Manifest observations were accepted for the image pipeline (98.2%).**
- Accepted records represent **269 distinct Manifest URLs** from **97/100 sources**.
- Retain the raw Manifest and validation evidence for inspection and downstream extraction.

### 本页结果表

| Stage | Current result |
|---|---|
| M4: image-pipeline acceptance | 275/280 source–Manifest observations accepted, or 98.2% |
| Distinct accepted Manifest URLs | 269 |
| Sources with accepted image Manifests | 97/100 |
| Image associations inventoried | 44,915 |

### 口头说明

Module 3 provides candidate Manifest URLs. Module 4 retrieves their JSON, checks the basic IIIF structure and inventories the declared image resources. In this run, 275 of 280 source–Manifest observations were accepted, covering 97 of the 100 sources. The original JSON and validation results remain available, so downstream records can be traced back to their source.

### 未完全通过的原因

Five of the 280 observations were not accepted by Module 4: three Northwestern Manifests had no image bodies, one Austrian National Library request returned HTTP 400, and one Trier Seminary Library request returned HTTP 404. Austria and Trier still contributed other valid records.

The Northwestern samples were not accepted for image extraction; the absence of image bodies alone does not establish that their IIIF Manifests are invalid.

**配图：** [图04：Manifest获取与校验](中期汇报/Fig/04_Module4_Manifest_Validation.png)。98.2%是文献观测级接受率；97/100是来源级图像输出覆盖率，两个分母分别说明。

**本页结论：** Module 4 turns discovered URLs into retrieved, checked Manifests and an inventory of their image resources.

---

## Slide 5 | Modules 5–6: Rights Classification and Metadata Extraction

### 可放入PPT的英文短句

- **Module 5:** Preserve rights evidence and distinguish research retention from public-reuse eligibility.
- **Module 6:** Normalize metadata and link images with declared institutional reference texts.
- All **275 accepted records were retained and normalized for research**, including **132 unknown-rights records**.
- The output preserves **44,915 image associations** and **7,232 institutional reference descriptors**.
- Missing dates or places remain explicit and do not block research output.

### 本页结果表

| Stage | Current result |
|---|---|
| M5: research retention | 275/275 accepted records retained |
| M6: research-usable normalization | 275/275 retained records normalized |
| Records not classified as eligible for public reuse | 237, including 132 with unknown rights |
| Image associations preserved | 44,915 |
| Institutional reference descriptors | 7,232 |

### 口头说明

Module 5 preserves the original rights evidence. Under the agreed project policy, unknown and public-reuse-excluded records remain in the research pipeline, while public-use restrictions stay attached. Of the 275 retained records, 237 were not classified as eligible for public reuse, including 132 with unknown rights. Module 6 then normalizes the metadata and preserves links to images and institutional texts. All 275 retained records passed through both stages. Missing descriptive fields are recorded rather than used to discard otherwise usable research records.

### 字段缺项如何解释

The metadata chart measures extracted field availability, not research usability. Titles and rights classifications are present in all 275 records; date strings were extracted for 133, normalized dates for 122, places for 87 and languages for 91. A rights classification of `unknown` is still a recorded assessment, not evidence of unrestricted reuse.

**配图：** [图05：研究保留](中期汇报/Fig/05_Module5_Rights_and_Retention.png)、[图06：规范化](中期汇报/Fig/06_Module6_Normalization_and_Completeness.png)。[图11](中期汇报/Fig/11_Module5_Rights_Categories.png)和[图14](中期汇报/Fig/14_Metadata_Field_Availability.png)可用作版权和字段的补充图。

**本页结论：** Validated resources retain their provenance, rights restrictions and normalized metadata throughout the research pipeline.

---

## Slide 6 | Modules 7–8: Linked Outputs and Downloads

### 可放入PPT的英文短句

- **Module 7:** Validate the common output schema and preserve document–image–reference associations.
- **Module 8:** Download one example or all exported images, with their linked JSON records and retrievable reference texts.
- The current run exported **275 document records, 44,915 image associations and 275 OCR profiles**.
- **5,783 image records have declared page-level text references.**
- Module 8 was not run in the 100-source evaluation; earlier image-and-text download examples are shown separately.

### 输出关联结构

```text
common_records.jsonl: document records
 |
 |-> common_media.jsonl: images linked by record_id
 |      +-> resource_id and Canvas identify the page/image
 |
 |-> ocr_document_profiles.jsonl: OCR-related document characteristics
 |      +-> linked by record_id
 |
 +-> institution_reference_texts.jsonl: institutional text references
        +-> record_id identifies the document
        +-> resource_id / Canvas links the text to an image when known
```

Module 8 places each downloaded image beside `common_record.json`, `common_media.json` and `ocr_document_profile.json`. Reference-bearing examples additionally include `institution_reference_texts.json`, the retrieved original text file and extracted plain text when supported.

```text
Module 8 output
 |-> with_reference: downloaded image and retrieved linked text
 |-> without_reference: image with no declared page-linked text
 +-> reference_failed: image whose declared reference could not be retrieved
```

### 口头说明

The output keeps documents, images and institutional texts connected through explicit identifiers. Arsha can therefore select a page and locate its corresponding text without reconstructing the relationship from filenames. In the current sample, nine sources provided text-reference declarations, covering 19 document records and 5,783 image records. These are recorded references and associations; this run did not download or verify every referenced text. Institutional OCR also needs quality assessment before it can be treated as trusted ground truth.

### 展示本次古籍下载样例

The new download demonstration uses a 1694 German print with institutional hOCR and a medieval manuscript fragment dated to 1275–1325 without a declared page-linked reference text. Both were freshly processed through Modules 1–8 on 6 November.

The BSB page image is 1688 × 2216 pixels and is linked to its retrieved hOCR by Canvas and resource identifiers. The Fragmentarium image is 6801 × 2999 pixels and is accompanied by the same three base JSON records.

Both examples demonstrate successful download and metadata linkage. The institutional OCR is not certified as manually corrected ground truth.

**配图：** [图07：统一导出](中期汇报/Fig/07_Module7_Common_Schema_Export.png)、[图13：参考文本覆盖](中期汇报/Fig/13_OCR_Reference_Availability.png)，以及本次两张古籍图片。图07/13属于100来源M1–7实测；两张实际下载图片属于单独的双样例演示。

**本页结论：** The pipeline delivers linked inputs for OCR testing and reference-based evaluation, while keeping text quality and provenance explicit.

---

## Slide 7 | End-to-End Demonstration

### 可放入PPT的英文短句

- One command runs two independent eight-module cases.
- A **1694 printed book** provides a page image with institutional hOCR.
- A **medieval manuscript fragment, dated 1275–1325**, provides an image without a declared page-linked reference text.
- Both examples include their document record, media record and OCR-profile JSON.
- Reference-bearing and reference-free outputs are stored separately.

### 视频中的启动命令

从包含pipeline.py的项目根目录执行。工具自动使用Code_git/.venv；默认创建新的时间戳目录：

~~~text
python Code_git/Pipeline_Runner/tools/run_presentation_demo.py
~~~

需要指定视频输出目录和打开图片的PowerShell代码时，使用[Demo命令.txt](Demo命令.txt)。逐步操作见[Demo演示步骤](Demo演示步骤.md)。

### 口头说明

This demonstration runs the complete pipeline for two historical documents. The first is a 1694 German printed book from the Bavarian State Library, with institutional hOCR linked to its page image. The second is a medieval manuscript fragment from Fragmentarium, dated to 1275–1325 in its source metadata, without a declared page-linked reference text. One command launches both cases, and each runs Modules 1–8 and downloads one image. I will show their separate output categories, the linked JSON files and the retrieved OCR text.

### 视频应展示的顺序

~~~text
Show the two inputs and start command
 -> Run M1-8 for the reference-bearing print
 -> Run M1-8 for the reference-free manuscript
 -> Show the two completed cases
 -> Open the 1694 image, hOCR, plain text and linked JSON
 -> Open the medieval image and its three JSON files
~~~

### 本次实测结果

2026-11-06两组全流程均已实际执行成功：两张新下载图片、六份通过schema及关联检查的基础JSON；带文本案例另取得一份机构hOCR、抽取纯文本及参考文本JSON。两组图片失败数、文本下载失败数均为0，两张图片已解码并目视检查。

BSB当前下载的是Canvas 1，1688×2216；Fragmentarium图像为6801×2999。此处不用旧EPFL样图。第6页可同时展示这两个新样例，历史林茨配对作为备用材料。

**演示边界：** 两份输入都是已知Manifest，验证的是全流程交接与下载分类，不是未知机构首页发现。工具调用原启动器两次，M8每次仍只下载一张；本次下载演示独立于前面的100来源M1–7实验。机构OCR仍需质量评估后才能作为可信ground truth。

---

## Slide 8 | Next Steps: LLM Discovery and Visual Interface

左右两个圆角框分别展示“降低新来源接入成本”和“降低用户操作门槛”。以下英文可直接放入对应框内，标题、目标、四个要点和状态依次排列。

### 左栏：LLM-Assisted Discovery

**Goal: Reduce manual effort when adding unfamiliar sources.**

- Investigate unresolved sources using official guides and catalogue APIs.
- Propose discovery routes and validate the resulting Manifests.
- Save verified recipes and evidence for later reuse.
- Evaluate success rates and costs on previously unseen sources.

框内可选简化流程：

```text
Unresolved source
 -> LLM investigation
 -> HTTP / JSON / IIIF validation
 -> Save and reuse verified recipes
```

**Status: API interface implemented; live-model evaluation pending.**

说明：已有方法先运行，仍未解决的来源才进入可选LLM调查。用户提供自己的API凭据。模型提出候选方法，程序执行实际HTTP、JSON和IIIF检查；失败时保留原因。保存的是可执行方法配置与证据，不是重新训练模型，也不保证覆盖所有新机构。

### 右栏：Visual Interface

**Goal: Make the pipeline easier to run and inspect.**

- Select sources, modules, download mode and optional API settings.
- Start the pipeline without entering terminal commands.
- Monitor progress, errors and output statistics.
- Browse images, metadata and linked reference texts.

框内可选简化流程：

```text
Configure
 -> Run
 -> Monitor
 -> Browse results
```

**Status: UI planned; unified command-line launcher available.**

说明：无终端操作、图形进度监控和图文浏览都是计划中的UI功能，当前已实现的是统一命令行启动器。

### 口头说明

The next goal is to reduce the effort of adding an unfamiliar source. The optional LLM interface can propose a discovery recipe, but deterministic checks decide whether the result is usable. A successful recipe stores configuration and evidence for later reuse; it does not retrain the model. The current coverage results were obtained with saved methods and the LLM disabled. I still need to evaluate the live model's discovery success, cost and reuse performance on unseen sources. In parallel, a visual interface would make the pipeline easier to configure and inspect.

### 现阶段最具体的改进

- Correct malformed candidate URLs, distinguish templates from concrete endpoints, and improve redirect handling.
- Diagnose client/network errors and retry affected sources separately.
- Continue searching for image-bearing Manifests when the first results contain only other media.
- Test catalogue pagination and completeness beyond the current sampling limits.
- Prioritize page-linked institutional texts and assess their OCR quality for downstream evaluation.

**可用的结束句：** The pipeline now connects resource discovery to linked OCR inputs; the next step is to make new-source onboarding more reliable and easier to use.

---

## Optional figure captions and backup answers

本节是选句与答疑材料，不增加主汇报页数。

### Figures 9–15: short English captions

| Figure | Caption |
|---|---|
| [09: Test scope](中期汇报/Fig/09_100_Source_Cohort_and_Scope.png) | The census contains 127 entries. This evaluation retested the 100 historically validated entries; the other 27 were outside the requested cohort. Of the 100 tested sources, 98 yielded Manifest URLs. |
| [10: Response types](中期汇报/Fig/10_Module2_Response_Types.png) | The 139 endpoint checks returned 30 JSON, 8 XML and 80 HTML responses; 21 checks were unsuccessful. Different response types require different discovery strategies. |
| [11: Rights categories](中期汇报/Fig/11_Module5_Rights_Categories.png) | All 275 records remain in the research output, including 132 with unknown rights. Public-reuse restrictions are preserved separately. |
| [12: Image yield](中期汇报/Fig/12_Image_Yield_by_Source.png) | The top 20 sources are ranked by image associations in their sampled Manifests. The results describe sample yield, not total collection size or downloaded images. |
| [13: Reference texts](中期汇报/Fig/13_OCR_Reference_Availability.png) | Nine sources declared reference texts; 5,783 image records have page-linked references. Of 7,232 reference descriptors, 7,217 are linked to a page. These declarations are not verified transcription-accuracy labels. |
| [14: Metadata fields](中期汇报/Fig/14_Metadata_Field_Availability.png) | Field availability measures non-empty extracted metadata. Missing dates, places or languages do not block research output, and an unknown rights category still counts as an assessment. |
| [15: Per-source results, five panels](中期汇报/Fig/15_Source_Stage_Results_01_of_05.png) | The five tables report M2–7 output counts for all 100 sources. Green means at least one output, red means zero, and gray means the stage did not finish. Each column has its own stated unit. |

### Why did a previously validated source fail this time?

Historical success means that a working Manifest route was demonstrated previously. A new run can still encounter access restrictions, network errors or a different sample of resources. In this evaluation, two sources failed during discovery requests, and one yielded only non-image samples. These cases need targeted retesting and improved sampling.

### Why did Module 3 succeed for more sources than Module 2?

Module 2 checks the supplied endpoints. Module 3 can also use saved catalogue API routes, so it may discover Manifests even when a supplied homepage is unavailable.

### Are the 44,915 image records unique downloaded images?

No. They are source-specific image associations exported from the sampled Manifests. They contain 44,252 distinct download URLs. Module 8 was not run in this evaluation, so these counts do not measure downloaded files.

### Does 100-source coverage prove generalization?

It demonstrates accumulated coverage of known sources with validated methods. Generalization to unseen providers needs a separate evaluation without adding provider-specific configuration during the test.

### Does the pipeline provide ground truth?

It provides institutional reference texts linked to images where the relationship is declared. Their accuracy and correction status must be assessed before using them as trusted ground truth.

### What is already implemented, and what remains planned?

All eight modules and the unified launcher are implemented. The current 100-source evaluation covers Modules 1–7; the separate two-case demonstration freshly runs Modules 1–8 for a historical print and a medieval manuscript. The optional LLM interface is implemented, but live-model generalization remains unmeasured. The visual interface is planned.

---

## Evidence and source files

- [Original presentation outline](中期汇报大纲与准备清单.md): content and evaluation scope; the latest instruction splits Module 4 and Modules 5–6 into separate slides in this draft.
- [Earlier PDF outline](output/pdf/中期汇报大纲与准备清单.pdf): original grouping; its seven-source statistical examples are superseded by the current run.
- [Current PNG figures](中期汇报/Fig/): images used for the captions above.
- [2026-11-06 evaluation summary](../../../Code_git/Pipeline_Runner/verification/2026-11-06_100_sources.json): 100-source counts, unique URLs and current failures.
- [2026-11-06 paired heritage demo](../../../Code_git/Pipeline_Runner/verification/2026-11-06_paired_heritage_demo.json): two fresh M1–8 runs, two decoded images, six validated base JSON files and retrieved page-linked BSB hOCR; separate from the 100-source experiment.
- [Per-source stage counts](../../../Code_git/Pipeline_Runner/data/midterm_100_20261106_123034/provider_stage_counts.csv): all 100 current source outcomes.
- [Implementation notes](../../../Code_git/Module_3/knowledge/implementation-status-and-lessons.md): current endpoint-check failure categories and known limitations.
- [2026-11-05 launcher and LLM checks](../../../Code_git/Pipeline_Runner/verification/2026-11-05_cli_and_llm.json): separate CLI example and simulated-model protocol/recipe replay checks; no paid-model performance evaluation.
- [Linz image–ALTO alignment evidence](../../../Code_git/Module_3/evaluation/2026-10-22_third_seven_provider_completion/reference_alignment_verification.json): historical downloaded page/text example.
- [Unified CLI instructions](../../../Code_git/Pipeline_Runner/统一命令行启动说明.md).
- [Module 3 LLM interface and knowledge reuse](../../../Code_git/Module_3/LLM接口与知识复用说明.md).
