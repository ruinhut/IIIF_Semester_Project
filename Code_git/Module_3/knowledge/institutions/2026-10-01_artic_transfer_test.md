# Held-out transfer test: Art Institute of Chicago

## Purpose

The Art Institute of Chicago was not used to derive the EPFL Plume recipe. It
tests whether the same executable idea works with a different API structure and
different pagination and identifier fields.

## Evidence

The official API documentation provides:

- list endpoint: `https://api.artic.edu/api/v1/artworks`;
- pagination parameters: `page` and `limit`;
- record array: `data`;
- identifier field: `id`;
- eligibility field: `is_public_domain`;
- Manifest template:
  `https://api.artic.edu/api/v1/artworks/{id}/manifest.json`.

Documentation: <https://api.artic.edu/docs/>

The documentation states that IIIF Manifests are offered for public-domain
artworks and asks automated clients to make no more than one request per
second. The provider recipe therefore filters `is_public_domain == true` and
uses a one-second request delay.

Artwork `21445` was used as the independent verification case. Its generated
URL returned HTTP 200, JSON-LD, IIIF Presentation 2 context and type
`sc:Manifest`.

## Transfer conclusion

No new Python strategy was required. Only the API URL, record path, identifier
path, pagination name, public-domain filter, Manifest template and delay were
changed. This is evidence that the skill separates a reusable procedure from
provider-specific facts. It does not prove applicability to APIs with cursor
pagination, POST-only search, authentication, or identifiers that require
multi-step joins; those require further skills.
