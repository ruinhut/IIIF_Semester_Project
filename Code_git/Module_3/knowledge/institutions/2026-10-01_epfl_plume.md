# Investigation: EPFL Plume

## Initial conditions

- Provider: Ecole Polytechnique Fédérale de Lausanne (EPFL)
- Provider ID: `provider-f2683615336e129a`
- Module 2 input: `https://plume.epfl.ch/`
- Observed result: HTTP 200 HTML after redirects to
  `https://plume.epfl.ch/s/fr/page/accueil`
- Previous Module 3 result: three bounded HTML pages visited, no Manifest found.

The failure occurred because the homepage did not directly expose the
machine-readable catalogue entry used for enumeration.

## Investigation

1. `https://plume.epfl.ch/api` identifies the installation as Omeka S and lists
   the public REST resources, including `items` and `item_sets`.
2. Omeka S documents its REST API at `/api` under the installation root:
   <https://omeka.org/s/docs/developer/api/rest_api/>.
3. `https://plume.epfl.ch/api/items?per_page=10&page=1` returns a JSON-LD array.
   Each item exposes the stable internal identifier in `o:id` and media links
   in `o:media`.
4. The official Omeka IIIF Presentation module documents the Manifest pattern
   `/iiif-presentation/3/item/:item-id/manifest`:
   <https://omeka.org/s/docs/developer/module_docs/IiifPresentation/>.
5. Item `44` was used as the first verification case. The URL
   `https://plume.epfl.ch/iiif-presentation/3/item/44/manifest` returned HTTP
   200, JSON-LD, IIIF Presentation 3 context, and type `Manifest`.
6. The alternative installed IIIF Server route
   `https://plume.epfl.ch/iiif/3/44/manifest` also returned a Presentation 3
   Manifest. Its documented generic pattern is `/iiif/:id/manifest` with an
   optional version segment:
   <https://omeka.org/s/modules/IiifServer/>.

The IIIF Server route is placed first in the executable recipe. In the bounded
downstream check it produced image bodies that Module 4 could inventory, while
some very large manifests from the IIIF Presentation module exposed image
services without bodies recognized by the current Module 4 extractor. The
official IIIF Presentation route remains a fallback and the distinction is
recorded rather than hidden.

## Extracted method

The reusable method is not “use item 44”. It is:

1. identify an Omeka S API root;
2. enumerate `/api/items` with bounded pagination;
3. read `o:id` from records with non-empty `o:media`;
4. expand a documented IIIF Manifest template;
5. fetch and validate every candidate as an IIIF Manifest;
6. retain the API page, skill ID and investigation ID as provenance.

This method is represented by the generic skill
`paginated_json_identifiers_to_manifest_templates` and the EPFL variables in
`config/discovery_knowledge.json`.
