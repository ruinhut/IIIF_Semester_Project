# Range catalogues and ALTO reference extraction

Learned and verified 2026-10-21, fourth five-provider investigation.

## Client-declared catalogue requests

When an HTML search page renders no records, inspect its own public client
JavaScript and data attributes before increasing recursive crawl depth. Do not
execute arbitrary downloaded code. Manchester's XTF client explicitly calls
`/search/JSONAdvanced` with start/end result ranges and reads `items[].item.id`.
The service returned 20 records even when `end=6`; verify response size and
compare the next range to prevent repeating the first page.

The generic query template supports `{page_number}`, `{page_size}` and now
`{page_end}` = page_number + page_size. Literal query braces remain intact;
provider expressions/code are never evaluated. Reviewed Manchester configuration
uses offsets 0, 20, 40 and range ends 20, 40, 60. A regression test checks the
first two constructed requests.

## Reference URLs are not reference text

Keep separately: declared reference links, fetched nonempty references, image
ownership, coordinate compatibility and transcription accuracy. Berlin declared
97 Canvas-level ALTO links in three sampled Manifests; one image/text pair was
downloaded, not all 97. Source-provided OCR can be wrong and is not automatically
manually corrected gold truth.

ALTO Description includes filenames, OCR models and processing settings. It
must not be flattened into page text. M8 now parses XML namespaces, reads only
layout String/CONTENT in document order, preserves TextLine separation and uses
XML entity decoding. Metadata-only ALTO yields no page text and is routed to
reference_failed. The original XML is retained. Media types ending in +xml,
including application/alto+xml, are supported.

Verify raw data before claiming fields exist: Berlin's selected ALTO v4 has
47 word elements with bounding boxes, but **zero WC confidence attributes**.
Its Page is 2221×3540 in pixel units, matching the decoded source image. The
Manifest declares an older v2 profile link; actual namespace and original source
declaration are both kept, without falsely claiming XSD validation. Its extracted
351-character page text still contains OCR mistakes.

Do not rewrite downstream modules for each institution. This batch reuses native
Collections, the existing generic HAL-link reader and the generic XML/OAI reader.
The only runtime changes were generic range-template support and ALTO text
quality handling; no runtime AI API was added.
