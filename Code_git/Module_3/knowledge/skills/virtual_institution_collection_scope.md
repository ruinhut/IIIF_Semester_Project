# Preserve virtual-institution scope when following IIIF Collections

Verified on four independent Dilibri partner libraries on 22 October 2026.

1. Compare two institutions' root responses, member IDs, totals and holder
   metadata. Shared hosting does not make them the same collection; different
   root URLs alone also do not prove different ownership.
2. Inspect every root/child `@id`, `first` and `next`. A platform can return scoped
   first-page members while emitting global links that silently remove the
   institution filter. Do not treat `all` from the global portal as one library.
3. Verify the institution-specific version of the next/child Collection route
   using the documented public branch. Fetch two distinct pages and inspect the
   holder. A reviewed configuration may preserve that route prefix.
4. In a knowledge skill, use `collection_url_rewrites` with `from_prefix` and
   `to_prefix`, both same-origin and ending `/collection/`. Module3 applies this
   to Collection requests only, before visited-URL checks. Manifest/image links
   remain unchanged; original and rewritten Collection URLs are audited.
5. Keep this opt-in. Reject cross-origin, overly broad and malformed rules.
   Default behavior for all previous providers must remain unchanged. Audit
   events are distinct from actual executions of a discovery skill.
6. Test actual traversal beyond one page with a larger bounded budget. Count
   **unique Manifest URLs**, because one Manifest may have several discovery
   evidence records. A cap can be reached in a child collection before the root
   next page; retain independent pagination evidence and describe it precisely.
7. Validate holder metadata and check overlapping Manifest sets before counting
   different institutions. Preserve a distinct provider ID for each real holder;
   do not invent an extra institution for the shared portal or each project.
8. Re-fetch selected Manifests through M4 and download a real content image via
   M8. Browser-challenge HTML with HTTP 200, broken members and preview-resolution
   images require separate, explicit reporting.

[Investigation and exact evidence](../institutions/2026-10-22_seven_provider_completion.md).
