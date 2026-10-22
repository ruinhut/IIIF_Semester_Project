# Catalogue details, visible IIIF URLs and Alma MMS IDs

Derived from the second 21 October 2026 five-source investigation.

1. Read the official IIIF guide and the institution's public search UI first.
   A guide often starts at the record page and does not specify bulk enumeration.
2. Distinguish catalogue record IDs, representation IDs, image IDs and native
   Manifest IDs. Reusing an image identifier as a record identifier is invalid.
3. Prefer explicitly declared Manifest links. If a catalogue only supplies
   parent record IDs, use one reviewed public detail route and extract the
   declared child links. JSON wildcard paths handle Linked Art; HTML details
   can contain an ordinary anchor or a visible plain-text URL.
4. The generic `identifier_followup` configuration defaults to JSON. Opt into
   `format: html`, set a strict `identifier_pattern` and, if needed,
   `include_visible_url_text: true`. It parses visible HTML and configured
   URL attributes without executing scripts. Match the native hostname and
   route, then independently validate the resulting Manifest JSON/type/context.
5. Alma publicly documents MMS-ID delivery: native IIIF routes may accept the
   catalogue MMS ID and resolve the appropriate representation. Verify that
   before adding an unnecessary representation-enumeration API call.
6. Search paging parameters are not interchangeable. BSB East Asia's `start`
   is a zero-based page number; Primo's `offset` is a result offset; LUX uses
   one-based `page` with `pageLength`. Follow actual next links to establish it.
7. Keep scope explicit: a keyword search, partner catalogue or workshop
   Collection proves a subset. It does not establish complete full-institution
   enumeration or an exact total. Preserve native-provider provenance.
8. Validate image bytes after Manifest validation. Construct Image API
   requests from declared services, encode spaces/Unicode once, and preserve
   the raw source identifier. A native body can be stale while its declared
   service works. Restricted responses must not trigger access-control bypass.
9. A reference descriptor is not validated training text. Exclude HTML titles,
   scripts and styles from extracted OCR; reject empty body text. Store
   genuinely nonempty OCR with its matching Canvas/resource ID and image.
   Provider OCR is a weak/reference label unless correction accuracy is known.

Verified transfers: BSB reuses HTML result attributes; Cardiff reuses JSON
identifier templates; Yale Library reuses JSON detail traversal; vHMML adds
HTML detail traversal; Leeds uses native Collection traversal. The procedure
can guide a new investigation, but does not guarantee success for unseen sites.
