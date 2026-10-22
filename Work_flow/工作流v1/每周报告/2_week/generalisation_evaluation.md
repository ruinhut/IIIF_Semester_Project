# Module 3 Generalisation Evaluation

Date: 25 September 2026

## Method

The 94-provider census was split at institutional-domain-group level:
75 development providers and 19 held-out test providers. The split
used only institutional domains and endpoint roles. Network and
Module 3 outcomes were not used. The same implementation and limits
were frozen before the held-out test.

## Results

| Metric | Development | Held-out test |
|---|---:|---:|
| Providers | 75 | 19 |
| Endpoints checked | 121 | 37 |
| Providers with a reachable endpoint | 53 | 16 |
| Providers with a JSON endpoint | 5 | 1 |
| Providers with Manifest(s) found | 9 | 2 |
| Provider success rate | 12.0% | 10.5% |
| Unique Manifest URLs | 306 | 19 |

Held-out successes:

- Digital Commonwealth: 1 Manifest URL(s)
- Fragmentarium - Digital Research Laboratory for Medieval Manuscript Fragments: 18 Manifest URL(s)

The held-out success rate was 2/19 (10.5%).
Among providers with a reachable endpoint it was 2/16 (12.5%).

Held-out unresolved diagnostics:

- No reachable endpoint in Module 2: 3
- Reachable page, but no IIIF candidate was exposed within the crawl limits: 4
- Candidate routes were tried, but none was confirmed as a Manifest: 10

## Interpretation

The generic implementation transferred to a direct Manifest route and
an HTML-declared Manifest route in previously held-out providers.
The low overall success rate shows that institutional APIs, search
interfaces and URL templates still require reusable adapters.

A negative result means no Manifest was found within the shared limits.
It does not prove that the institution has no IIIF resources.
