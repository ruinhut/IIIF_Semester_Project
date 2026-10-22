# Downloaded Blavatnik reference batch

This is a bounded pilot for testing OCR/HTR with institution-supplied page
transcriptions. It is not a representative sample of the entire archive and
is not asserted to be manually corrected gold ground truth.

## What is physically available

99 single-page candidates were processed through Modules 4–8. There are
**98 downloaded JPEGs and 98 corresponding original-language transcriptions**
(320,729,690 image bytes in total). One image, item 19634, is unavailable at
the source; the failed attempt remains recorded.

Each successful folder under
`reference_batch/module8/output/all/with_reference/` contains:

```text
image.jpg
common_record.json
common_media.json
ocr_document_profile.json
institution_reference_texts.json
institution_reference_001.txt
```

The record ID, resource ID, Canvas URL and image identifier agree across the
files. The text exactly matches the cleaned institution `originalTranscript`
field. English translations in `englishTranscript` were not substituted.
Original catalogue JSON and precise field paths remain linked in provenance.
The catalogue source URL returns JSON, not a standalone plain-text file;
the text has already been extracted into `institution_reference_001.txt`.

## Languages, dates and appearance

Institution-reported language combinations for these 98 downloaded pages:

| Reported value | Pages |
|---|---:|
| Russian | 94 |
| Russian;Yiddish | 1 |
| Yiddish | 1 |
| English;Russian | 1 |
| Unknown | 1 |

77 documents have a normalized metadata date, spanning **1917–2006**;
21 have no normalized date in the export. The range follows explicit date
fields. One source inconsistency is preserved: item 14328 has “2007” in its
title but “July 7, 2006” in its Written Date. No date was silently corrected.

Visual inspection of three selected pages confirms Cyrillic handwriting,
Yiddish handwriting with a printed letterhead, and a mixed English/Russian
handwritten message on a printed form. One inspected letter has substantial
paper damage. These are observations of three pages, not full-batch quality
or typography statistics. Fraktur coverage has not been established.

The exported production-method classifier is metadata-based: 6 pages are
labelled handwritten, 5 printed and 87 unknown. Those labels are not a pixel
survey and should not be interpreted as the true handwriting/print split.
The scan-quality fields likewise remain unassessed unless evidence exists.

## Reference-label scope

Alignment is established only for a single Manifest Canvas with one image
body, one catalogue page and a matching image identifier. These transcriptions
are page-associated; they have no word/line bounding boxes. Completeness,
editorial conventions, restoration of missing text and exact transcription
accuracy have not been independently scored. In particular, text supplied for
a damaged page can contain editorial readings that are not visible in the
surviving pixels.

The files named `ocr_ground_truth_candidates` are a separate representative
sampling suggestion, not the complete set of references. Use the actual
`institution_reference_texts` output and the downloaded text files for this
98-page pilot.

All 98 images were decoded successfully and match the source pixel dimensions.
All 294 principal JSON files passed schema validation, and all 98 source-text
and image-identity matches were checked. The underlying rights classifications
and research/public-reuse flags are preserved in the JSON.

Machine-readable checks: `reference_batch_ocr_characteristics.json`,
`reference_batch_link_verification.json`, `reference_batch_image_verification.json`.
