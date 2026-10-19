# Five provider discovery routes — 15 October 2026

These investigations complete the catalogue-to-Manifest step for the five
providers previously known only through individual working examples. An
executable route is not a claim that every item in an institution has been
harvested. Live outcomes, request failures, raw responses and exact sample
counts are kept in `evaluation/2026-10-15_five_provider_completion/`.

## Göttingen University Collections / GDZ

- Official guide: https://iiif.io/guides/guides/gdz.sub.uni-goettingen.de/
- Enumerate: `https://gdz.sub.uni-goettingen.de/suche?page=1`, then page 2, etc.
- Record links: `/id/{identifier}`; identifiers include PPNs and volume suffixes.
- Manifest: `https://manifests.sub.uni-goettingen.de/iiif/presentation/{identifier}/manifest`.
- The search page exposed 15 distinct record links per page and a last-page
  link to page 5683 in the inspected response. This is a navigation observation,
  not a verified count of downloadable objects.
- The top IIIF Collection's child routes were not usable for enumeration in
  the earlier inspection. Targeted search-result pagination supplies IDs without
  visiting every record page or inventing sequential identifiers.

## Leiden University

- Official guide: https://iiif.io/guides/guides/universiteitleiden.nl/
- Enumerate the public Islandora search endpoint:
  `https://digitalcollections.universiteitleiden.nl/islandora/search`.
- Configure `type=dismax` and a content-model filter for
  `info:fedora/islandora:bookCModel`. The site exposes the exact filter spelling
  in its search URLs; preserve its backslash escaping.
- Record links are `/view/item/{identifier}`. The unfiltered search also contains
  constituent/compound objects that may not have an item-level Manifest.
- Manifest template:
  `https://digitalcollections.universiteitleiden.nl/iiif_manifest/item:{identifier}/manifest`.
- Follow actual HTTP redirects: working records currently redirect to standard
  Presentation 3 resources under the new Alma catalogue. Do not derive the Alma
  representation identifier from the old numeric item ID.
- The book query exposed 20 records per page and a last page of 1255 (zero
  based). This recipe covers the book content model; it is not an inventory of
  every Leiden object type. Site migration remains an external dependency.

## National Library of Wales

- Official guide: https://iiif.io/guides/guides/discover.library.wales/
- Institution-specific training:
  https://training.iiif.io/nlw-workshop/nlw-manifests.html
- The public catalogue search returns structured JSON at
  `https://discover.library.wales/primaws/rest/pub/pnxs`.
- Use `vid=44WHELF_NLW:44WHELF_NLW_NUI`, `scope=MyInstitution`, `tab=tab1`,
  `q=any,contains,viewer.library.wales`, `lang=en`, and offset/limit pagination.
  The API uses `q`; the human search UI uses `query`. Confusing the two returned
  HTTP 400 during investigation.
- Extract `delivery.availabilityLinksUrl[]`; match
  `https://viewer.library.wales/{identifier}`.
- Candidate IIIF route:
  `https://iiif.llyfrgell.cymru/manifests/2.0/{identifier}/manifest.json`.
- Inspect JSON type: an endpoint ending in `manifest.json` may be a **Collection**.
  Keep it as a Collection root and let native Module 3 traversal discover its
  child Manifests. Never send a Collection to Module 4 as if it were a Manifest.
- The verified query reported 74 catalogue records; they include Collections
  containing many issues. This is the query's scope, not all NLW holdings.
- Other broad queries return physical holdings, archival descriptions and
  restricted e-resources too. A large `total` is not an IIIF object count.
- Public OAI Identify/ListSets work, but tested ListRecords publishing profiles
  did not expose a usable record feed. That lead remains documentary evidence.
- Ex Libris documents pagination limits for guest searches; respect them and
  record incomplete scope rather than claiming unrestricted catalogue export.

## Utrecht University Library

- Official guide: https://iiif.io/guides/guides/objects.library.uu.nl/
- Complete listing: `https://objects.library.uu.nl/reader/object-list?lan=en`.
- The full response was 9,810,977 bytes and ended with the HTML closing tag.
  It contained 29,357 distinct `20.500.14918-*` object identifiers; 25,564
  listing elements were labelled `object-openaccess`.
- This response exceeds the former 8 MiB probe budget. A truncated response
  must not be presented as a complete object census.
- Parse record links only inside `object-openaccess` containers; exclude
  `object-oncampus` entries. Keep fetch failures even for records labelled public.
- Manifest route:
  `https://objects.library.uu.nl/manifest/iiif/v3/{identifier}`.
- The public metadata label does not prove an image download will succeed.
  Validate the Manifest and image HTTP response separately.

## Universitaet Jena / ThULB / MyCoRe

- Official guide: https://iiif.io/guides/guides/collections.thulb.uni-jena.de/
- MyCoRe reference: https://www.mycore.de/documentation/interfaces/interface_rest/
- Enumerate public objects with
  `https://collections.thulb.uni-jena.de/api/v2/objects?offset=0&limit=20`.
- Extract each actual `id`; do not guess numeric IDs, since there are gaps.
- Request `/api/v2/objects/{id}/derivates`; extract each returned `href`.
- Manifest route:
  `https://collections.thulb.uni-jena.de/api/iiif/presentation/v2/{derivative_id}/manifest`.
- Objects can have no derivatives, multiple derivatives, or a failing derivative.
  Deduplicate derivative IDs and continue after an individual detail failure.
- Real requests showed HTTP 500 and transient timeouts, including an HTTP 500
  on the object index during a later run. A subsequent request to the identical
  index succeeded. Preserve this failure and use bounded retries; do not call
  the provider permanently unavailable or conceal the failed attempt.

## Generic implementation and reuse

All provider-variable facts are in `config/discovery_knowledge.json`. The shared
skills implement source pagination, wildcard JSON paths, configured URL-ID
patterns, optional detail-API expansion, targeted HTML record parsing, access
container filtering, URL-template validation and typed Collection handoff.

Catalogue pages are processed lazily. Increasing the catalogue page budget does
not require downloading the entire index before producing the first Manifest.
The run stops when the configured Manifest budget is reached. HTML pagination
uses observed next-page links; a short filtered page is not mistaken for the
end. Repeated record pages are detected within the current run to avoid loops.
This fingerprint is not an old-Manifest allowlist and never rejects new content.

Modules 4–8 consume the existing normalized Manifest contract. They require no
provider-name conditions for these new discovery methods.

## Reproduce

From the project root, use `Code_git/.venv/Scripts/python.exe`:

```powershell
& .\Code_git\.venv\Scripts\python.exe .\Code_git\Module_3\tools\prepare_five_provider_completion.py --sample-limit 20 --batch final_validation
& .\Code_git\.venv\Scripts\python.exe .\Code_git\Module_3\tools\run_discovery_with_evidence.py --config .\Code_git\Module_3\evaluation\2026-10-15_five_provider_completion\module3_final_validation.json
```

The preparer preserves the original provider identities and other recipes. The
evidence runner calls the real Module 3 pipeline; it adds HTTP traces and
provider checkpoints, without changing the downstream output schema.

For a larger output sample, increase `--sample-limit`. The source-level bounds,
coverage notes and public API restrictions remain visible in provider recipes.
