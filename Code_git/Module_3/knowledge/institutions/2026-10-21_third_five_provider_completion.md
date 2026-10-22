# Third five-source completion — 21 October 2026

Evidence: `evaluation/2026-10-21_third_five_provider_completion/`.
Two sources were unresolved in the existing census; three institutions were
added to Module 1. Cumulative evidence is **69/97 source entries**, including
66/94 original entries and 3/3 additions. It is not 69/94, an independent
institution count, a full-catalogue harvest, or a fresh retest of all old sources.

| Source | Route | M4-valid Manifests | Exported image associations |
|---|---|---:|---:|
| British Library | Official highlights page → viewer fragment's declared native Manifest | 6 | 2,365 |
| Indigenous Digital Archive / DigiTreaties | Public treaty catalogue → treaty ID → native Manifest | 6 | 130 |
| Heidelberg University Library, new | OAI-PMH XML → explicit dc:hasFormat | 6 | 762 |
| National Diet Library of Japan, new | OpenSearch RSS → declared NDL PID → documented Manifest template | 6 | 288 |
| Victoria and Albert Museum, new | Public objects API → declared link; separately tested systemNumber recipe | 1 | 90 |

## Routes and limitations

- **British Library**: [official digitised highlights](https://www.bl.uk/collection/digitised-manuscripts-archives)
  lists nine viewer links. Extract native `bl.digirati.io` URLs from their
  `#?manifest=` fragments. Support `/iiif/ark:/81055/{id}` and
  `/manifests/ark:/81055/{id}`; verify responses rather than assuming a route.
  Six were retained in this bounded run. The downloaded 818×1024 image is the
  Manifest's declared derivative, not a claim of archival master resolution.
- **Indigenous Digital Archive**: the former hostname is parked. The
  [Museum of Indian Arts and Culture announcement](https://media.newmexicoculture.org/press_releases.php/1195/?action=detail&releaseID=1195)
  identifies DigiTreaties as an IDA project with National Archives content.
  Enumerate `https://digitreaties.org/treaties/treaties/`, extract
  `/treaties/treaty/{id}/`, request its `/manifest/`. This restores the treaty
  subset, not the entire former boarding-school archive. Some Manifests still
  declare restricted old `dlcs-ida.org` assets. The first sample failed HTTP 403;
  its failure is retained in `initial_failed_downloads.jsonl`. Treaty 81147473
  has declared public NARA images and supplied the successful 3798×5859 sample.
- **Heidelberg**: [official open interfaces](https://www.ub.uni-heidelberg.de/helios/kataloge/datenschnittstellen.html)
  documents DWork OAI and IIIF. Use
  `https://digi.ub.uni-heidelberg.de/cgi-bin/digioai.cgi?verb=ListRecords&metadataPrefix=oai_dc&from=2026-10-20`.
  Read explicit `dc:hasFormat` Manifest links. This is an update-date subset.
  OAI continuation uses its opaque resumption token. HTML challenge pages were
  not bypassed. The real sample decodes at 1623×2356.
- **NDL**: [official API specifications](https://ndlsearch.ndl.go.jp/help/api/specifications)
  give OpenSearch XML and numeric `idx`/`cnt` pagination. This run queries
  `dpid=ndl-dl`, title `源氏物語`, publication `until=1900`. Extract only
  `https://dl.ndl.go.jp/pid/{id}` from `rdfs:seeAlso/@rdf:resource`, then use
  `https://dl.ndl.go.jp/api/iiif/{id}/manifest.json`. One candidate (2608445)
  returned 404; it was rejected and pagination continued to obtain six valid
  Manifests. The reported 724 matches are metadata hits, not a validated total.
  OpenSearch is limited to the first 500 matches; use query partitions or the
  documented OAI endpoint for larger harvests. The selected image's `full/full`
  URL returned non-image content; existing M8 service validation and size
  fallback downloaded 3340×2203, below the Canvas's 6680×4406 declaration.
- **V&A**: [official IIIF guide](https://developers.vam.ac.uk/guide/v2/images/iiif.html)
  documents `systemNumber` and
  `https://iiif.vam.ac.uk/collections/{systemNumber}/manifest.json`.
  The public manuscript query supplies image-bearing object records. Generic
  discovery found one explicit Manifest and therefore skipped the fallback
  recipe, as designed. A separate live execution of that recipe validated six
  Manifests (`vam_recipe_validation.json`); these are not added to the 25-object
  downstream count. The API's `_iiif_presentation_url` can be null even when the
  documented template works. Not every image-bearing record yields a Manifest.

## Completed checks

- Module 1 registered the three additions using its own parser; all original
  IDs and endpoints remain. The two restored sources have additional endpoints.
  The old census snapshot remains available, and manual source configuration
  includes all five changes for subsequent normal census runs.
- Module 2 checked nine endpoints; all five sources have a reachable route.
- Module 3 saved catalogue/Manifest request traces. Its resumed final run reused
  snapshots from this investigation; Module 4 independently fetched all 25
  Manifests freshly, with zero cache hits, and accepted all 25.
- Modules 5–7 produced 25 documents, 3,635 image associations and 25 OCR profiles.
  Research-only rights categories remain marked; they are not public-reuse grants.
- Module 8 saved five real JPEGs and 15 linked, schema-valid JSON files. All five
  images decode. NDL's sample is downscaled; 3,635 links are not 3,635 verified
  downloads. No page-linked institutional reference text was declared in these
  samples. They belong in `without_reference`; candidate hints are not ground truth.
- Module 3–8: 182 tests passed, plus seven subtests. New XML executor coverage
  adds three tests. Production knowledge increased 37→42 recipes; all 37 old
  recipes and 19 curated endpoint entries remain unchanged. There is no runtime
  AI API integration in this change.

See [the generic XML skill](../skills/xml_catalogue_discovery.md) and the dated
evaluation's Chinese report, metrics CSV, native Manifests and sample path list.
