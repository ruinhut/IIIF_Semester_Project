# Module 3 Institution Investigation Playbook

The 2026-10-16 Blavatnik investigation is recorded in
`institutions/2026-10-16_blavatnik.md`. It adds reviewed read-only POST search,
JSON-body pagination, catalogue-only headers, and a declared-total check that
detects premature short pages. Verify actual page-size limits and reconcile
unfiltered catalogue coverage against collection facets: a successful query
does not establish complete enumeration. Preserve old and failed routes as
evidence without continuing to execute them as working recipes.

This playbook stores the reusable reasoning process for an institution whose
Module 2 endpoints are reachable but whose Manifests are not found by the
current generic traversal.

## Goal

The result of an investigation is not merely a provider URL. It is:

1. a reproducible evidence trail;
2. a reusable discovery skill;
3. a small provider configuration that supplies only variable facts;
4. a held-out transfer test showing where the skill does and does not apply.

## Investigation sequence

### 1. Read the conditions

- Inspect every Module 2 route, final URL, content type, status, redirect and
  JSON result for the provider.
- Record what is known and what remains unknown.
- Do not assume that an institution homepage is the data endpoint.

### 2. Classify the platform and exposed surfaces

- Inspect HTML metadata, script paths, network calls and stable URL patterns.
- Probe conventional public descriptions such as `/api`, `info.json`,
  `manifest`, `collection`, `activity`, `oai`, or documented search APIs.
- Classify the useful surface: IIIF Collection, Change Discovery, public JSON
  API, search API, identifier list, embedded JSON, or HTML-only catalogue.

### 3. Find authoritative instructions

- Prefer the institution's technical documentation and API documentation.
- Consult `config/official_guide_knowledge.json` for the provider's exact
  official IIIF guide actions, screenshots, links, and candidate skills.
- Use official software documentation when the platform is identifiable.
- Use IIIF community and source-code documentation to resolve gaps.
- Record every source URL and the date checked.

Official guide knowledge remains documentary evidence. A screenshot or a
manual instruction proves that a route exists for a human item page; it does
not prove a catalogue enumerator, current endpoint, or stable URL contract.
Only a verified complete chain may be copied into executable provider
knowledge.

### 4. Derive an executable recipe

Separate stable method from provider variables:

- **skill**: pagination, record-array extraction, filtering, identifier
  extraction, URL-template expansion, and Manifest validation;
- **provider configuration**: API URL, JSON paths, pagination parameter names,
  filters, URL templates, limits and respectful request delay.

### 5. Verify the entire chain

For at least one item, retain evidence for:

`Module 2 route -> public API -> item identifier -> candidate URL -> HTTP 200 -> JSON-LD -> IIIF Manifest`

The endpoint is resolved only when the candidate can be fetched and declares
an IIIF Presentation `Manifest`. A plausible URL is not enough.

### 6. Test transfer

- Apply the same skill implementation to a provider not used to create it.
- Change configuration only.
- If it works, retain the new provider recipe and document the boundary.
- If it fails, record the failed assumption and create or extend a reusable
  skill rather than adding scattered provider-name branches.

## Current reusable skills

The subsequent five-provider work is recorded in
`institutions/2026-10-15_five_provider_completion.md`. It adds lazy pagination,
wildcard JSON identifier paths, URL-ID patterns, optional detail-API expansion,
HTML access-container filtering, observed next-page detection, repeated-page
guards, and typed Collection roots returned by catalogue recipes. A separate
generic Image API repair in Module 8 handles stale body URLs and unsupported
delivery formats; discovery recipes do not rewrite image-server hostnames.

The 2026-10-15 investigation added `paginated_json_manifest_links` (declared
Manifest URLs in nested catalogue arrays) and
`paginated_html_identifiers_to_manifest_templates` (targeted catalogue record
links). Collection traversal now follows both `first` and `next` with cycle
detection. See `skills/2026-10-15_catalogue_link_skills.md` and
`institutions/2026-10-15_provider_routes.md` for live evidence and boundaries.

Consult native Collection roots and documented catalogue APIs before raising
HTML crawl depth. Preserve HTTP 403, certificate errors, browser challenges,
empty Collections, and non-image Manifests as distinct outcomes. Do not turn a
sample success into a claim that the entire institution has been harvested.

`paginated_json_identifiers_to_manifest_templates` performs bounded JSON API
pagination, extracts records and identifiers through configured paths, applies
optional filters, expands one or more Manifest URL templates, fetches every
candidate, and accepts only declared IIIF Presentation Manifests.

The implementation is in `iiif_resource_discovery/skills.py`. Machine-readable
provider recipes are in `config/discovery_knowledge.json`. Each run stores a
`knowledge_application` audit block in the provider report.

The next three-provider investigation is documented in
`institutions/2026-10-15_three_provider_completion.md`: BSB's official guide
already publishes a paginated native Collection; Rumsey's LUNA JSON search
declares `results[].iiifManifest`; Vatican's manuscript catalogue declares
category JSON routes containing real shelfmarks. All three reuse existing
algorithms through configuration. Preserve all declared categories while
distinguishing retained routes from routes actually exercised. Frick was
investigated but is not counted as resolved: its comparison Manifest route
expects a saved workspace ID, not an ordinary catalogue record ID.
# 2026-10-19: Collection and viewer-route transfer

See [five verified source routes](institutions/2026-10-19_five_provider_completion.md)
for Visual Library pagination, FromThePage project Collections, SACHA annual
newspaper Collections and Bodmer's constellation-scoped viewer templates.
Distinguish directory coverage, valid Manifest samples and actual image delivery.

## 2026-10-19 resumed investigation

See [five additional reviewed routes](institutions/2026-10-19_resumed_provider_completion.md)
and [detail records and explicit migration links](skills/declared_detail_and_migration_links.md).
Inspect JSON detail records when list records omit delivery IDs. Treat an HTTP
200 HTML migration notice or challenge page as HTML, not as an empty Manifest.
Follow only reviewed, explicitly declared migration targets with finite hops.
Do not mistake descriptive metadata XML for institution-provided OCR labels.

## 2026-10-19 third source group

See [five more source routes](institutions/2026-10-19_third_provider_completion.md)
and [explicit legacy-format compatibility](skills/legacy_shared_canvas.md).
Check the actual source context before calling a resource unavailable. Historical
Shared Canvas can use compatible sequence/image structures; opt in explicitly
and retain the original format and a validation warning. Distinguish an API's
required filters and offset parameters from guessed page/limit parameters.
Ordinary catalogue HTML seeAlso links are not OCR references without evidence of
full text or transcription; inline supplementing text remains supported.
