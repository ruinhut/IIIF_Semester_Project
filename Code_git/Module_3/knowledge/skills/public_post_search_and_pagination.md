# Reusable skill: public read-only POST catalogue search

Use this only for a reviewed public catalogue/search request. POST is not
automatically a write, but the recipe must explicitly declare `read_only: true`.
The implementation accepts GET and POST, not mutation verbs. Never copy login
tokens or private browser credentials into provider knowledge.

The generic recipe keeps the variable facts outside Python:

```json
{
  "skill_id": "public-search",
  "type": "paginated_json_identifiers_to_manifest_templates",
  "api_url": "https://example.org/search?size=60",
  "request": {
    "method": "POST",
    "read_only": true,
    "headers": {"X-Public-Catalogue": "collection-name"},
    "json_body": {"query": "", "filters": []}
  },
  "records_path": "hits.data",
  "identifier_path": "record.id",
  "manifest_url_templates": ["https://example.org/iiif/{identifier}/manifest"],
  "pagination": {
    "location": "json_body",
    "page_parameter": "from",
    "page_size_parameter": "",
    "page_size": 60,
    "page_step": 60,
    "start_page": 0,
    "max_pages": 1000,
    "total_path": "hits.total"
  }
}
```

The body is copied for every page. Search headers and body are not forwarded
to candidate Manifest requests. Offsets are distinct from numbered pages;
verify both the parameter and the increment using actual responses.

Before declaring complete enumeration, check:

1. The server's effective page size agrees with the requested size.
2. Distinct records and a terminal page agree with the declared total.
3. A repeated page or premature short page is recorded as incomplete.
4. Facets/collections do not omit unassigned records or double-count overlap.
5. Candidate URLs return actual Presentation Manifests, rather than image
   information, a viewer HTML page, a login page or an empty catalogue wrapper.

Resume identity includes URL, HTTP method, JSON body and catalogue headers.
Replaying a saved response is recorded as a snapshot reuse, not a new network
request. Corrupt JSON is fetched again. No old hash is used to reject a new
resource. Source structural defects must remain visible to Module 4.

Evidence: `../institutions/2026-10-16_blavatnik.md`. This extension has local
HTTP tests and one real provider verification. Its additional cross-provider
transfer remains to be measured; the recipe structure alone is not proof that
every institution can use it.
