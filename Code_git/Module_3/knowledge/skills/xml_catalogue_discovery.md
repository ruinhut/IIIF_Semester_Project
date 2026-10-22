# Namespace-aware XML catalogue discovery

Implemented 2026-10-21 as `paginated_xml_identifiers_to_manifest_templates`.
This adds a reusable executor; institution paths and URL templates remain data
in `config/discovery_knowledge.json`. Modules 4–8 keep the same contracts.

1. Find an institution's documented machine interface before increasing HTML
   crawl depth. Catalogue APIs can be public even when HTML search is challenged.
   This is not permission to bypass protected routes.
2. Configure XML namespaces, record path, identifier element and optional
   attribute. Extract **declared identifiers or links**, rather than scanning
   arbitrary numbers or guessing sequential IDs.
3. Use reviewed regular expressions to select the intended collection's links.
   Expand only documented Manifest templates; validate the returned IIIF context
   and Manifest type. XML catalogue records are not themselves Manifests.
4. For RSS/SRU, keep start position, step and page size distinct. NDL uses
   `idx` (one-based record position) and `cnt`. The current OpenSearch interface
   cannot retrieve beyond the first 500 matches: partition queries or use the
   documented OAI harvesting API for larger jobs, respecting its date limits.
5. For OAI-PMH, treat `resumptionToken` as opaque. Continuation requests keep
   `verb` plus the token, omitting the original metadataPrefix/from/until/set.
   Stop on an empty token; reject repeated tokens and protocol errors. Skip
   deleted records. Never call a challenge page or malformed XML an empty success.
6. Keep actual request URLs, declared totals, failures, bounded-run truncation,
   native Manifests and downloaded images as separate evidence.

Verified families: Heidelberg DWork OAI-PMH `dc:hasFormat`; NDL Search RSS
`rdfs:seeAlso/@rdf:resource` PID links. Three new tests cover OAI continuation,
duplicate/deleted records, restricted HTML/protocol errors and strict validation.

Official documentation:

- [Heidelberg open interfaces](https://www.ub.uni-heidelberg.de/helios/kataloge/datenschnittstellen.html)
- [NDL API specifications](https://ndlsearch.ndl.go.jp/help/api/specifications)
- [NDL September 2026 specification](https://ndlsearch.ndl.go.jp/file/help/api/specifications/ndlsearch_api_20260925.pdf)
