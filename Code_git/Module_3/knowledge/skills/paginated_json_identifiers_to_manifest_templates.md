# Skill: paginated JSON identifiers to Manifest templates

## When to apply

Use this skill when an institution exposes a public JSON catalogue API but the
API returns institution-specific records instead of IIIF Collections or
Manifests.

## Required observations

- a list endpoint that supports bounded pagination;
- the JSON path to the record array;
- a stable identifier field in each record;
- an evidence-based Manifest URL template;
- any filter required before a Manifest can exist.

## Processing steps

1. Fetch API pages with the configured parameter names and page size.
2. Resolve the configured record-array path.
3. Apply required-nonempty checks and equality filters.
4. Extract and deduplicate identifiers.
5. URL-encode each identifier and expand the configured templates.
6. Fetch candidates sequentially with the configured delay.
7. Accept only JSON declaring `Manifest` in an IIIF Presentation context.
8. Store counts, template successes, failures and truncation in the provider
   report.

## Generalization boundary

This skill does not discover undocumented API URLs or infer arbitrary URL
templates by itself. Those facts are established through the investigation
playbook and stored as provider configuration. The executable algorithm is
provider-independent.
