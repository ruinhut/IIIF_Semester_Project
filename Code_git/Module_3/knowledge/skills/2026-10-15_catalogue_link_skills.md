# Reusable catalogue-link discovery skills

## paginated_json_manifest_links

Use when a public JSON catalogue declares actual Manifest URLs. Configuration
supplies `api_url`, `records_path`, `manifest_url_path`, query parameters,
pagination names and budgets. A dot path supports `*` to expand nested arrays,
and numeric indexes. Each extracted candidate is fetched; it is accepted only
with a Presentation context and Manifest type. Deduplicate URLs and record
requests, failures, pages, records, and truncation in the skill audit.

Live evidence: Wellcome (`results`, `items.*.locations.*.url`) and Northwestern
(`data`, `iiif_manifest`), five verified Manifests each. No provider-name branch
is used in the implementation.

Both JSON skills support zero-based offset APIs via `start_page=0` and
`page_step=page_size`, while retaining the original one-based page defaults.
Brown's `start`/`rows` search API verified this with two real result pages and
five accepted Manifest URLs. Its identifier-template recipe reuses the original
EPFL/Chicago skill with different configuration.

## paginated_html_identifiers_to_manifest_templates

Use when a targeted catalogue listing exposes stable item-record links but no
structured public enumerator is yet available. Configuration supplies the
listing URL, a named-group `record_url_pattern`, `identifier_template` and
Manifest templates. The HTML parser collects anchor URLs, extracts identifiers
and deduplicates them. It then reuses the existing identifier-to-template
validator. Pagination parameters are configuration; they must be verified for
the actual catalogue before increasing the page budget.

Live evidence: e-codices `/en/list/all` record links become library-shelfmark
identifiers and then validated Manifest URLs. The collection root returned
HTTP 500; this targeted catalogue route worked. Only its first listing has
been tested, and this skill has not yet been transferred to an independent
second platform.

## Collection first-page navigation

Collection traversal follows `first` and `next`, using the same visited set as
nested Collections. This supports CONTENTdm wrapper Collections that declare
their first member page separately. Washington's alaskawcanada Collection
verified this behavior. Both page and Manifest budgets remain explicit.

## Failure boundaries

- A declared Manifest is not necessarily image-bearing: sound and video are
  legitimate IIIF resources. Module 4 classifies these separately.
- HTTP 200 challenge pages and Image API `info.json` are not Manifests.
- A recipe that finds five samples is not a complete collection inventory.
- Do not disable TLS checks or bypass access restrictions to improve counts.
- A wrong template must fail validation; never persist a guessed URL as verified.

Implementation: `iiif_resource_discovery/skills.py`, `discovery.py`.
Regression tests: `tests/test_catalogue_routes.py`.
