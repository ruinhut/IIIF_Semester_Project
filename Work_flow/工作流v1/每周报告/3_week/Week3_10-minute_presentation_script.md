# Week 3 — 10-minute supervision presentation

## Files to display

1. `Module3_current_problem_and_improvement.png`
2. `Fragmentarium_example_page.jpg`
3. `Module7_linked_output_example.md`
4. `example_common_record.json`
5. `example_common_media.json`
6. `example_ocr_document_profile.json`

The ground-truth candidate file is deliberately excluded from this
demonstration because it is currently a page-selection list rather than a
completed image–text ground-truth dataset.

## Presentation script

### 0:00–0:40 — Introduction

Good morning. This week I focused on three points. First, I corrected the way
Module 5 handles resources with missing or restricted rights. Second, I began
adapting the Module 7 output to answer Arsha's questions about the OCR dataset.
Third, I identified Module 3 as the main bottleneck limiting the number and
diversity of institutions that reach the rest of the pipeline.

### 0:40–2:00 — Module 5 rights handling

Previously, Module 5 excluded a resource from the downstream dataset when the
institution did not provide a clear reusable-rights statement. This was too
restrictive for our research purpose. The revised behaviour retains the URL
and metadata of every successfully processed resource for academic analysis.

The pipeline still preserves the distinction between research use and public
reuse. Unknown or restricted resources are marked as unsuitable for public
redistribution or commercial use, while open and public-domain resources can
be identified separately. This means that missing rights information no
longer causes useful research metadata to disappear.

The current bounded dataset contains 324 tested Manifests and about 54.6
thousand linked media records from ten resolved providers. These are validation
counts, not the complete potential collection. If Module 3 resolves more of the
reachable institutions, the eventual image volume could be on the order of
several hundred thousand.

### 2:00–3:20 — Module 7 output for Arsha

Arsha needs to select OCR engines and design a ground-truth set. For this, she
needs to know the languages, scripts, periods, printed-versus-handwritten mix
and scan quality of the harvested documents.

I therefore began adapting Module 7 to produce an OCR-oriented document
profile. The current sample spans approximately 601 to 2017. The main reported
languages include English, Latin, Persian, Hebrew, Greek and Arabic. It
contains both printed and handwritten material, although many records remain
unknown because the institutions do not report enough metadata. Scan quality
also remains unknown because the current stage does not analyse image pixels.

An important remaining issue is that institution-provided OCR or transcription
links are not yet connected to their corresponding Canvas and image in the
final output. This must be preserved from Module 4 onwards before we can
produce real image–text pairs.

### 3:20–5:20 — Demonstrating the Module 7 relationship

[Display `Module7_linked_output_example.md`.]

This example shows one Fragmentarium document. Module 7 separates the output
into linked tables instead of placing everything inside one very large JSON
record.

The `common_record` is the canonical document record. It stores the title,
language, date, type, rights and source. It also says that this document has
three media records.

The `common_media` file contains one row per Canvas or image. Here it stores
the Canvas identifier, page sequence, direct image identifier and IIIF Image
API service. It links back to the document through the same `record_id`.

The `ocr_document_profile` describes the same document for OCR selection. In
this example, the metadata reports German, a date covering the thirteenth and
fourteenth centuries, parchment and Gothic script. The production method is
still marked unknown because the program has not visually inspected the image
and the metadata does not explicitly classify it as handwritten.

[Display `Fragmentarium_example_page.jpg`.]

![Downloaded Fragmentarium page used in the live image-access test](Fragmentarium_example_page.jpg)

I used the Image API address from `common_media` to download this image. The
request returned HTTP 200 and a valid JPEG of 1000 by 440 pixels. This confirms
that the image link exported by Module 7 is operational. What is still missing
is a text-resource field linking this Canvas to hOCR, ALTO, plain text or an
institutional transcription when such data exists.

### 5:20–7:20 — Module 3 bottleneck and proposed improvement

[Display `Module3_current_problem_and_improvement.png`.]

![Module 3 current limitation and proposed improvement](Module3_current_problem_and_improvement.png)

The left side shows the current limitation. Module 3 can detect direct
Manifests, traverse IIIF Collections and Change Discovery streams, inspect
explicit IIIF links in JSON and HTML, and perform a bounded same-site crawl.
However, these methods resolved only ten of ninety-four candidate providers in
the bounded full-pipeline run. Many institutions use their own APIs,
identifier systems or Manifest URL patterns. Implementing a separate method
for every institution would be slow and difficult to generalise.

The right side shows the proposed AI-assisted workflow. For a new provider,
Module 3 first applies its existing skills and provider knowledge. If they
succeed, the pipeline outputs the Manifests directly. If they fail, the AI
investigates the institution's documentation, APIs and website structure. The
pipeline then validates the resulting Manifest URLs. Once the method is
confirmed, its process is stored as a reusable skill or as provider knowledge
for future runs. This is similar to a student remembering a verified solution,
so the same investigation does not need to be repeated each time.

### 7:20–8:30 — Next steps

My next priority is Module 3. I will choose one currently unresolved but
reachable institution, resolve it completely, document the reasoning process
and convert the successful method into reusable knowledge, a generic skill and
provider configuration. I will then test that skill on a different institution
without changing its Python implementation.

In parallel, I will extend Modules 4 to 7 so that Canvas-level OCR and
transcription resources are preserved alongside the corresponding images.
This will give Arsha usable image–text pairs rather than only document profiles
and candidate pages.

## Likely questions and standard answers

### 1. Is the estimate of several hundred thousand images a measured result?

No. The measured bounded result is 324 Manifests and about 54.6 thousand media
records from ten providers. The larger figure is an order-of-magnitude
projection based on the additional reachable providers. It must not be
reported as a completed harvest.

### 2. Why retain resources whose rights are unknown?

The supervisor and institutions allow their URLs and metadata to be retained
for academic analysis. Module 5 therefore keeps them while explicitly setting
public redistribution, commercial use and public reuse to false. Unknown
rights are never interpreted as public domain.

### 3. Is institution-provided OCR automatically ground truth?

No. It is useful as institutional reference text or a silver-standard label,
but it may contain OCR errors. It becomes strict ground truth only after its
provenance, Canvas alignment and transcription accuracy have been verified,
usually through human correction.

### 4. Why does the displayed manuscript have `production_method: unknown`?

The current classifier is conservative. It uses explicit metadata evidence and
does not inspect pixels. The document reports parchment and Gothic script but
does not explicitly state the production method, so the program leaves the
field unknown rather than guessing from the appearance.

### 5. How will AI output be prevented from adding false Manifest URLs?

AI will be used to investigate documentation and propose a recipe. Every
candidate URL must still pass deterministic HTTP, JSON and IIIF Presentation
type/context validation. Only verified results and their evidence are written
to the knowledge base.

### 6. Why use three output files instead of embedding every image in the main record?

One Manifest may contain hundreds of Canvases. A separate media table avoids
duplicating the document metadata for every page. The stable `record_id`
provides a clear one-to-many relationship and remains easy to process in JSONL,
CSV or a database.

### 7. How will Module 3 generalisation be evaluated?

I will separate development institutions from held-out test institutions. The
main measures are provider discovery success, valid Manifest yield and whether
the held-out provider can be resolved through an existing generic skill plus
configuration, without provider-specific Python code.

### 8. What is the next requirement for Arsha's OCR work?

We need page-level image–text pairs. Modules 4 to 7 must preserve Canvas-level
`seeAlso`, `otherContent`, ALTO, hOCR and Presentation 3 supplementing
annotations, then record their exact relationship to each image.
