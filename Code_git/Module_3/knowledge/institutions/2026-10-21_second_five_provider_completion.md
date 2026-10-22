# Second five-source completion — 21 October 2026

Evidence: `evaluation/2026-10-21_second_five_provider_completion/`.
All five are previously unresolved **entries in the existing 94-entry census**.
An entry can represent a collection, so this is not a claim of five newly
identified independent institutions. BSB East Asia is a BSB collection subset.

| Source | Reproducible route | Live validated Manifests | Image records |
|---|---|---:|---:|
| BSB East Asia | Search HTML `data-manifest` attributes | 6 | 5,256 |
| Cardiff | Public Primo digital records → MMS ID → Alma Manifest | 2 | 95 |
| Leeds | Public IMC workshop Collection → native Leeds Manifests | 6 | 1,867 |
| vHMML | DREAMSEA search → detail page's visible native Manifest URL | 6 | 118 |
| Yale Library | LUX search → Linked Art object → declared Library Manifest links | 6 | 582 |

## Exact recipes and coverage

1. **BSB East Asia**: `https://ostasien.digitale-sammlungen.de/search?q=China&searchType=free`.
   Result containers declare `data-manifest` URLs. The page displays 108 hits
   for this query; it is not the whole catalogue. `start` is a zero-based page
   number, not a result offset; `rows` controls the page size. A request with
   `start=11` returned no results and must not be mistaken for the second page.
   The verified first six URLs are native BSB Presentation 2 Manifests.
2. **Cardiff**: `https://librarysearch.cardiff.ac.uk/primaws/rest/pub/pnxs` with
   institution view `44WHELF_CAR:44WHELF_CAR_VU1`, local catalogue scope and
   query `any,contains,Ellor`. Nine catalogue hits include two digital records.
   Select records with `delivery.hasD=true`; read `pnx.control.sourcerecordid.0`.
   `https://librarysearch.cardiff.ac.uk/view/iiif/presentation/44WHELF_CAR/{MMS_ID}/manifest`
   works directly: Alma resolves an MMS ID to a representation. Do not invent
   representation IDs or require a separate representation lookup unnecessarily.
   The originally declared image body returned 404; existing M8 resolution
   through its explicitly declared IIIF Image service downloaded the image.
3. **Leeds**: public curated root
   `https://presentation-api.dlcs-trial.digirati.io/176/leeds-imc/university-of-leeds-medieval-manuscripts`.
   Its items declare native `https://iiif.library.leeds.ac.uk/presentation/cc/...`
   URLs. This is a workshop medieval-manuscript selection, not the full Leeds
   catalogue; catalogue search itself returned 403. The downloaded body is a
   declared 762×1024 derivative. Native image services describe larger masters;
   do not call this sample an archival original.
4. **vHMML**: public institutional partner catalogue
   `https://hmmlcloud.org/dreamsea/manuscripts.php?country=Laos&searchType=1`.
   Enumerate `detail.php?msid=...`, then read the **visible URL text**
   `https://www.vhmml.org/image/manifest/...` on each detail page. DREAMSEA's
   local ID and vHMML's Manifest ID are different; never substitute one for the
   other. The reviewed recipe bounds identifiers at 50 and validation at six.
   Restricted Reading Room search was not bypassed. Public Manifest bodies
   identify Image API service bases containing spaces; M7 constructs the image
   request and percent-encodes those spaces while preserving raw source IDs.
5. **Yale Library**: `https://lux.collections.yale.edu/api/search/item` with JSON
   grammar `{"AND":[{"hasDigitalImage":1},{"text":"manuscript"}]}`.
   Enumerate `orderedItems.*.id`, fetch the Linked Art object and read
   `subject_of.*.digitally_carried_by.*.access_point.*.id`. Accept only links
   under `https://collections.library.yale.edu/manifests/`. This reuses the
   generic JSON detail traversal, rather than deriving Library IDs from image
   IDs or using museum namespaces. One LUX object can declare several volumes.
   The 5,234 search estimate is not a validated Manifest count.

## Validation and reference-text correction

M4 freshly fetched 26 distinct Manifests, with zero cache hits; M7 exported
7,918 distinct image URLs with zero rejected records/media. Five real images
and 15 companion JSONs passed schema/ownership checks and full pixel decoding.
Dimensions match the selected source declarations. M6 has 26 partial metadata
records, zero failed records; a missing metadata field is not a lost Manifest.

The six BSB books declare 5,256 Canvas-level hOCR descriptors. This does not
prove every OCR endpoint contains useful recognized text. The initial cover
hOCR contained only an HTML title naming the file. M8 previously mistook that
title for OCR. It now excludes head/title/script/style content; empty decoded
text is rejected and routed through existing reference-failure handling.

The corrected final sample uses `bsb11178213`, Canvas 10, OCR endpoint
`https://api.digitale-sammlungen.de/ocr/bsb11178213/10`: 157 hOCR word spans,
373 extracted characters, page bbox and image both 1731×2996. Image content
was visually checked. This is provider-supplied machine OCR, not certified
manual ground truth. Other final samples are in `without_reference`.

179 tests and seven subtests passed. Four executable knowledge recipes and
one curated Collection root were appended locally; all previous 33 knowledge
entries and 18 curated endpoint entries remain equal to their snapshots.
Cumulative completed-source evidence: **64/94**, 30 outside that set. Earlier
successes were not all re-fetched today. No runtime AI API or GitHub push was
performed in this investigation.

## Primary references

- [IIIF finding-resources index](https://iiif.io/guides/finding_resources/)
- [Cardiff guide](https://iiif.io/guides/guides/librarysearch.cardiff.ac.uk/)
- [Alma delivery and MMS-ID resolution](https://developers.exlibrisgroup.com/alma/integrations/digital/almadigital/access/)
- [Leeds guide](https://iiif.io/guides/guides/library.leeds.ac.uk/)
- [DREAMSEA institutional catalogue](https://hmmlcloud.org/dreamsea/)
- [vHMML metadata schema and access fields](https://www.vhmml.org/dataPortal/schema)
- [Yale LUX backend API documentation](https://github.com/project-lux/lux-marklogic/blob/main/docs/lux-backend-api-usage.md)

Additional blocked, retired and incorrect routes remain in the probe logs and
`unresolved_investigations.json`. HTTP 200 challenge/status pages are not
successful JSON retrievals; metadata access does not imply image availability.
