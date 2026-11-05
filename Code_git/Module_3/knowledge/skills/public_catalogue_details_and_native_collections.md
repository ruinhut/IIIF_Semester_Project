# Public catalogue details and native Collection pagination

Verified on 22 October 2026 with KU Leuven/Lovaniensia and four additional
VisualLibrary installations. This is a reusable investigation procedure, not a
promise that every installation exposes the same public endpoints.

1. Preserve the original institutional URL and inspect the official IIIF guide,
   then the actual collection platform. Keep failed and historical routes.
2. When a catalogue API is restricted but normal public result pages are
   accessible, inspect those pages' item links and one item detail. Never bypass
   an API restriction or assume public metadata means public images.
3. Distinguish the **catalogue record ID** from the **Manifest identifier**.
   Lovaniensia's `6217` links to `IE17067641`; no numerical conversion exists.
   Use the detail-page anchor and a reviewed allowlisted pattern. The existing
   generic HTML-detail follow-up supports this without new provider code.
4. Check holder metadata when harvesting a collaborative catalogue. A project's
   host name is not proof of every item's institution of origin.
5. Prefer a verified native Collection over a deeper general HTML crawl. Read
   `members` as well as `manifests`/`items`, inspect child types, preserve source
   links and follow **declared `next` URLs**. Some installations use an `_o20`
   path suffix; an invented `?page=2` can silently repeat page one.
6. Fetch two distinct pages to verify pagination. The number of member links
   is not the number of successfully downloaded objects. Separate first-page
   fallback recipes, whole-collection traversal and bounded-run output counts.
7. A declared Manifest can be incomplete. M4 must still check usable Canvases
   and image bodies; retain a PDF rendering without counting it as page images.
8. Download and decode a native image. A platform may append an attribution
   border to a preview, increasing its height by 50 pixels. Record actual versus
   declared dimensions. A dimension mismatch is not always downscaling.
9. Keep normalized M3 output unchanged so later modules do not need new
   institutional logic. Store recipes, provenance, request snapshots, failures
   and final image/JSON ownership checks separately.

Evidence and exact institutional scope:
[five-source investigation](../institutions/2026-10-22_five_provider_completion.md).
