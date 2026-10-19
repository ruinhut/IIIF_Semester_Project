# Reusable detail-record and migration-link handling

## Detail API records

`identifier_followup.records_path` may resolve to a single record object or an
array. `identifier_path` selects a declared value. An optional
`identifier_pattern` extracts the identifier from that value with a named
`identifier` group (or capture group 1). Values that do not match are skipped.
This permits Blacklight detail documents to supply a Figgy UUID without
confusing it with the catalogue's own record ID.

## Mixed catalogue links

For `paginated_json_manifest_links`, an optional `manifest_url_pattern`
filters declared links before HTTP retrieval. This avoids requesting ordinary
PDFs, viewer pages and thumbnails as Manifest candidates. A pattern match is
not validation: the response must still declare IIIF Presentation and Manifest.

## HTML migration notices

The optional `html_migration` object enables bounded handling of legacy
delivery URLs returning an HTML refresh rather than an HTTP redirect:

```json
{
  "max_hops": 2,
  "url_pattern": "^https://(?:nrs|iiif)\\.lib\\.harvard\\.edu/"
}
```

Only a declared `meta` refresh target may be followed. Targets are resolved
against the actual response URL, checked against the configured pattern, and
stopped on a repeated URL or hop limit. No arbitrary page link is inferred.
HTTP redirects remain the fetcher's responsibility. Module 3 emits the final
validated Manifest URL, so downstream modules do not need institution branches.

Live evidence and limitations are in
`../institutions/2026-10-19_resumed_provider_completion.md`. This is an
investigation-derived deterministic skill, not an integrated autonomous LLM API.
