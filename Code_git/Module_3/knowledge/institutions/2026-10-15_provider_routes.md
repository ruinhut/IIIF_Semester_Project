# Provider discovery investigations, 15 October 2026

This is a bounded, evidence-backed checkpoint, not a completed catalogue harvest.
The source queue was the 83 unresolved provider **entries** in the October 12
production output. Their homepages were rechecked and 63 matched official guide
pages were requested. Provider names and duplicate identities are not reliable
counts of independent institutions.

## Executable routes verified

Each entry below yielded five sample Manifest references in Module 3. Module 4
then fetched all 65 unique references: 62 passed image-resource structural
validation, two Northwestern Manifests contained non-image content, and one
Lancaster request timed out. The 62 image-bearing samples declare 8,985 Canvases
and 8,985 image bodies. Images were not downloaded in this investigation.

| Provider | Verified discovery route | Method and boundary |
|---|---|---|
| Cambridge | https://cudl.lib.cam.ac.uk/iiif/collection/all | Native Collection hierarchy. |
| Lancaster | https://digitalcollections.lancaster.ac.uk/iiif/collection/all | Same Collection pattern; one sample timed out in Module 4. |
| Huntington | https://hdl.huntington.org/iiif/2/manifest.json | CONTENTdm top Collection and child Collections. |
| Leicester | https://specialcollections.le.ac.uk/iiif/2/manifest.json | CONTENTdm Collection hierarchy. |
| Radboud | https://bijzonderecollecties.ubn.ru.nl/iiif/2/manifest.json | CONTENTdm Collection hierarchy. |
| Washington | https://cdm16786.contentdm.oclc.org/iiif/2/alaskawcanada/manifest.json | One-collection fallback because the top index repeatedly timed out. Follow `first` to the first member page. Does not cover the entire institution. |
| Durham | https://iiif.durham.ac.uk/manifests/trifle/collection/index | Native Collection hierarchy. |
| Northwestern | https://api.dc.library.northwestern.edu/api/v2/collections?as=iiif | Native Collection hierarchy; mixed media, so a Manifest need not contain an image. |
| National Library of Scotland | https://view.nls.uk/collections/top.json | Native Collection hierarchy. |
| Toronto | https://iiif.library.utoronto.ca/presentation/collections | Redirects to the current versioned root Collection. |
| Wellcome | https://api.wellcomecollection.org/catalogue/v2/works | Filter `items.locations.locationType=iiif-presentation`, include `items`, extract `results[].items[].locations[].url`. |
| e-codices | https://www.e-codices.ch/en/list/all | Extract library and shelfmark from `/en/list/one/{library}/{shelfmark}` links, expand `https://www.e-codices.ch/metadata/iiif/{library}-{shelfmark}/manifest.json`, validate response. First listing only; catalogue pagination is not established. Two old provider entries refer to this same source. |
| Brown | https://repository.library.brown.edu/api/search/ | Filter `q=object_type:image`, extract `response.docs[].pid`; expand `https://repository.library.brown.edu/iiif/presentation/{identifier}/manifest.json`. Offset pagination uses `start` and `rows`. Five Manifests passed Module 4. |

Northwestern was also separately tested through
`https://api.dc.library.northwestern.edu/api/v2/search?query=*&size=5&page=1`:
the same JSON-link skill used for Wellcome extracted `data[].iiif_manifest`
and validated five real Manifests, with configuration changes only. The result
is saved in `northwestern_skill_transfer.json`. This is a transfer test on a
known provider, not an unbiased held-out benchmark.

## What was learned

1. Read the [official guide](https://iiif.io/guides/finding_resources/) first.
   It often describes item-page interaction, not a bulk enumerator. Inspect the
   institution's current documentation and platform documentation next.
2. Test native Collection roots before spending the request budget crawling
   unrelated HTML. CONTENTdm's documented hierarchy applies to several sites;
   shared software can yield reusable discovery knowledge.
3. A Collection can be a page wrapper containing `first` without any members.
   Follow both `first` and `next`, with cycle detection and explicit budgets.
4. A public catalogue API may explicitly declare Manifest links deeply nested
   inside arrays. Extract configured paths rather than inventing URL templates
   where the institution already supplies URLs.
5. When only an HTML catalogue is available, target record links using a
   documented identifier pattern. Do not crawl every navigation link. A template
   is a candidate generator; fetch and validate each candidate.
6. HTTP 200 is insufficient: challenge pages, HTML catalogue UIs, Image API
   descriptions and Presentation Manifests have different meanings.
7. Preserve partial successes. One working item proves an item route, not a
   complete enumeration method. Timeouts do not prove permanent unavailability.

## Partial leads and current failures

- Göttingen: a real PPN Manifest works, but the top Collection's child URLs
  return HTML; corrected Collection endpoints returned no members in this run.
- Leiden: an official item Manifest works; bulk enumeration remains unknown.
- Wales: `https://damsssl.llgc.org.uk/iiif/2.0/4389767/manifest.json` works;
  a catalogue-wide enumerator is not verified.
- Utrecht: an item Manifest was retrieved, but no bulk discovery recipe was
  validated here.
- Bodmer Lab: catalogue pages and direct Hedera Image API links were found;
  a Presentation Manifest enumeration route remains unverified.
- e-rara / e-manuscripta: current homepages return browser verification content.
  Official e-rara OAI-PMH documentation suggests a future XML-identifier skill;
  it is not executable verified knowledge yet.
- Digital Commonwealth, Gallica and Finna: tested routes returned HTTP 403.
  Do not interpret this as evidence that no IIIF exists.
- Several providers returned certificate-chain failures or timeouts. TLS
  verification was kept enabled. They require network/certificate diagnosis.
- Stanford returned a challenge page. Yale published crawler restrictions;
  no restriction bypass was attempted.
- Jena's MyCoRe `/api/v2/objects?limit=5` returns object IDs; requesting
  `/api/v2/objects/{id}/derivates` returns derivative IDs. The tested Manifest
  requests first timed out; retrying the same candidate returned a real
  Presentation Manifest. The two-stage enumerator is not integrated yet, so
  Jena is recorded as a partial item-level success rather than a resolved recipe.
- Austrian National Library SACHA documents project-specific Manifest routes,
  but explicitly restricts bulk downloading of ABO books. Preserve that boundary
  rather than assuming public metadata authorizes unrestricted image downloads.
- Brown catalogue/search APIs returned JSON while its human documentation
  page returned a browser challenge. The public API was usable without bypass.

## Source and evidence locations

- [CONTENTdm support summary](https://help.oclc.org/Metadata_Services/CONTENTdm_classic_version/Advanced_website_customization/API_Reference/IIIF_API_reference/IIIF_API_support_summary)
- [Wellcome Catalogue API](https://developers.wellcomecollection.org/api/catalogue)
- [Northwestern API source](https://github.com/nulib/dc-api-v2)
- [Toronto collection FAQ](https://collections.library.utoronto.ca/explore/faq/getting_started)
- [e-codices official IIIF guide](https://iiif.io/guides/guides/e-codices.ch/)
- [Cambridge collection platform](https://cambridge-collection.github.io/)
- [e-rara API documentation](https://era-prod11.ethz.ch/wiki/apiinfo)
- [Brown Library API documentation repository](https://github.com/Brown-University-Library/bdr_api_documentation)
- [SACHA API documentation and download restrictions](https://iiif.onb.ac.at/api/)

All live checks, exact dates, response files, failed guesses and provider IDs
are preserved in `evaluation/2026-10-15_provider_investigation/live/checks.jsonl`.
See `provider_route_audit.json` / `.csv` for every original queue entry, and
`summary.json` for computed totals. `baseline_*` files preserve old knowledge.
The two isolated Module 3/4 batches retain raw Manifests and logs; they do not
overwrite production outputs. Configured five-item samples must be expanded
in a separate full-coverage run before claiming catalogue totals.
