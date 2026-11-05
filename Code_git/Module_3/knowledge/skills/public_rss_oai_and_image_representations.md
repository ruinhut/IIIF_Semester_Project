# Public RSS/OAI catalogues → native Manifests → readable image representations

Validated 22 October 2026 at Kassel, Humboldt, ZLB, two distinct Kiel holders,
SLUB Dresden and Upper Austrian State Library. Full evidence and scope:
`../institutions/2026-10-22_third_seven_provider_completion.md`.

1. Inspect official HTML/API documentation. Preserve declared RSS/OpenSearch,
   OAI, Collection, item and Image-service links rather than keeping only a
   homepage. A reachable XML catalogue can be useful without returning JSON.
2. For Goobi, the verified structured surfaces include:
   `/viewer/api/v1/records/rss`, and on supporting installations,
   `/viewer/api/v2/collections/{field}/`. The latter requires a configured field
   such as `DC`; guessing a v1 `/collections/` root and seeing 404 is not evidence
   of no IIIF. Different installations may disable the v2 surface.
3. Public RSS `item/link` values expose record IDs in `/image/`, `/metadata/` or
   `/toc/` routes. Use the existing XML identifier/template executor. Verify
   `/api/v1/records/{id}/manifest/` on actual records; reject non-Presentation or
   inaccessible responses. Do not assume all metadata-visible files are public.
4. A 50-record RSS feed is a **bounded subset**. No numeric pagination was
   established for these feeds. Do not invent page parameters or mistake the
   executor's conservative size heuristic for an explicit server `next`. Find a
   documented Collection, OAI or search pagination route for full harvesting.
5. When using a shared portal, configure a documented public owner filter and
   check native holder metadata. At Schriftgut.SH use exact `MD_DV_OWNER` values.
   Check cross-source Manifest overlap; do not count the portal again as a holder.
6. For OAI-PMH, read namespace-aware paths and map a documented/tested identifier
   to native Manifest routes. Follow the **opaque resumptionToken**, retaining
   only allowed request parameters (normally `verb`). Check a distinct second
   page. A short page may still have a continuation token; SLUB returned 25.
7. Keep basic Manifest validation and M4 handoff independent of discovery. A
   valid OAI record does not imply a valid Manifest: GWLB's old documented
   Manifest example works, but the same guessed directory template failed on
   newer newspaper IDs. Keep the failed mapping as a lead, not a promoted recipe.
8. A Manifest image body may request a 300–400-pixel preview while its dimensions
   describe the full image. For readable sample delivery, inspect its explicitly
   declared Image API `info.json`, respect size/area bounds, and request the
   supported representation. Preserve original image/source IDs and record the
   actual requested download URL. Do not rewrite hosts or bypass 401/403.
9. Select a real content page instead of a blank flyleaf or a cover with only a
   shelfmark. If institution OCR is linked, preserve the exact Canvas/resource
   association and compare downloaded raster dimensions with ALTO Page dimensions
   and word boxes. Provider OCR is not automatically manually corrected gold truth.
10. Retain evidence and precise counts: descriptors ≠ fetched texts, Manifest
    links ≠ validated objects, previews ≠ master scans, source entries ≠ distinct
    institutions, bounded samples ≠ full catalogues.

Reusable commands under `Module_3/tools/`:

- `verify_catalogue_feed_recipes.py --evaluation-root DIR`: independent recipe,
  actual OAI continuation, Manifest-overlap and shared-holder checks.
- `prepare_full_resolution_examples.py --evaluation-root DIR`: explicit **sample
  preparation** after M5–8 helper; reads native Image services, archives prior
  previews and emits `module8_full_resolution_examples.json` for standard M8.
- `verify_linked_download_bundles.py` and `verify_downloaded_pixels.py`: file,
  schema, identity and actual raster checks. No change to production M7/M8 default
  image selection is implied by the auxiliary sample step.

These methods and configurations can be run by another maintainer. Identifying
new platforms/recipes still requires investigation; no runtime LLM investigator
or universal discovery guarantee was implemented by this batch.
