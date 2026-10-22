# Reviewed catalogue attributes and Linked Art detail records

Validated on 20 October 2026 with Ghent, St Andrews and three Yale museums.

## Read the public interface before increasing crawl depth

A record page may be an empty server template, a JavaScript application, or a
blocked homepage even though a documented public data surface remains usable.
Inspect the institution's own frontend scripts and official API documentation.
Record the observed search endpoint, collection selector, pagination fields,
record ID, and explicit Manifest namespace; then validate the native response.
Do not count a reachable search page or a plausible URL as a working source.

## HTML result attributes

`paginated_html_identifiers_to_manifest_templates` now accepts the optional
`record_url_attributes` list. The default remains `["href"]` on anchor tags.
An explicit reviewed recipe can use `["href", "data-manifest"]` to enumerate
Manifest links declared on result containers. Identifier regexes, optional
ancestor-class restrictions, deduplication and native Manifest checks still
apply. Next-page detection uses anchor links, not arbitrary data attributes.

Ghent's Biblissima collection results declare native Ghent Manifests through
`data-manifest`, so individual aggregator detail pages need not be visited.
The public pagination parameter is `from` (offsets 0, 20, ...), not `page`.
The recipe is scoped to Biblissima-indexed Ghent manuscripts, not all Ghent data.

## Indexed JSON metadata and followup records

Scalar JSON paths used by filters, required fields and declared totals now
support numeric list indices, consistently with identifier extraction.
Examples are `listMetadata.IRN.0`, `listMetadata.MultimediaPublish.0` and
`partOf.0.totalItems`. A missing or out-of-range index does not match.

St Andrews' current public search frontend declares a Funnelback JSON search
with `start_rank` and `num_ranks`. Public result metadata supplies the EMu IRN;
reviewed native routes return `/<IRN>/manifest`. Require published image
metadata before requesting a Manifest. The live investigation obtained four
Manifests from two result pages, then received HTTP 429 on a later page. This
is a proven discovery route with incomplete, rate-limited enumeration, not a
complete catalogue result. Keep the failure and use respectful pacing.

Yale LUX returns paginated Linked Art object references. The existing generic
identifier-followup skill can:

1. Query the institution's `memberOf` collection with `hasDigitalImage = 1`.
2. Extract the UUID from `orderedItems[].id`.
3. Fetch the object detail JSON.
4. Inspect `subject_of[].digitally_carried_by[].access_point[].id`.
5. Accept only the reviewed institution-specific Manifest namespace.
6. Fetch and validate every candidate as IIIF before passing it downstream.

The same code works for `ycba/obj`, `ypm/nat` and `yuag/obj`; only configuration
changes. Search estimates describe matching catalogue objects, not a measured
number of successfully retrieved Manifests. No runtime AI API is involved.

## Linked metadata is not a transcription

Yale British Art Manifests include `text/rdf+n3` Dataset links. These are linked
metadata, not OCR text merely because their MIME type starts with `text/`.
Module 6 excludes RDF serializations and requires transcription evidence for a
generic seeAlso Dataset, while raw Manifest links remain available. hOCR,
ALTO and explicit transcriptions retain their existing handling. This source
group delivers zero verified page-level OCR pairs.
