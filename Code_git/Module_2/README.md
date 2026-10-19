# Module 2: IIIF Entry-Point Accessibility and Response Validator

Module 2 consumes the provider selection produced by Module 1 and records what
happens when each candidate entry point is requested. It is a network and
response-quality gate: it follows redirects, applies bounded retries and
timeouts, records HTTP evidence, and determines whether a successful response
contains parseable JSON.

It does **not** traverse Activity Stream pagination, discover Manifest URLs, or
validate Manifest structure. Those operations belong to Modules 3 and 4.

## Schema 2.0: all-endpoint validation

Module 2 reads every item in a provider's `endpoints` array and writes one
checked JSONL record per provider-endpoint pair. Each row includes the original
provider, `endpoint_candidate`, and `endpoint_check`. The run log separately
reports provider count, candidate-endpoint count, unique requests, and how many
providers have at least one reachable or JSON endpoint. The `--limit` option
limits providers; all endpoints of each selected provider are still checked.

## Input

The default input is:

```text
../Module_1/data/output/selected_providers.jsonl
```

Every Module 1 field is retained unchanged. Module 2 appends an
`endpoint_check` object and a `module_2_schema_version` field.

## Check sequence

For every `discovery_endpoint`, the module:

1. sends a bounded HTTP GET with an identifiable academic user agent;
2. follows and records redirects;
3. records the final URL, HTTP status, content type, elapsed time, body size,
   attempt count, and error details;
4. reads no more than the configured response-size limit;
5. parses responses advertised as JSON, plus JSON bodies served with an
   incorrect media type;
6. assigns one explicit result category without silently dropping the record.

## Result categories

| Result | Meaning and route |
|---|---|
| `reachable_json` | Successful response with parseable JSON; ready for Module 3 |
| `reachable_non_json` | Successful HTML or other response; manual review |
| `invalid_json` | JSON-like response that cannot be parsed; manual review |
| `response_too_large` | Response exceeded the configured safe read limit; manual review |
| `restricted` | HTTP 401 or 403; manual review |
| `temporary_failure` | Timeout, rate limit, or retryable server error; retry later |
| `unreachable` | Permanent HTTP failure or network/address failure |

An HTTP 200 response is not treated as proof that the endpoint is a conformant
IIIF API. Structural validation remains downstream.

## Outputs

Module exchange data is written to `data/output/`:

- `checked_entry_points.jsonl` — every input record with its check;
- `discovery_ready.jsonl` — parseable JSON responses for Module 3;
- `manual_review.jsonl` — accessible but ambiguous, malformed, large, or
  restricted responses;
- `unavailable_entry_points.jsonl` — temporary and permanent access failures;
- `checked_entry_points.csv` — flattened table for human inspection.

Timestamped operational logs are stored separately in:

```text
data/log/Module2_YYYY-MM-DD_HH-MM-SS_log.txt
```

## Run

From the `Module_2` directory:

```powershell
python -m iiif_entry_validator run --config config.example.json
```

For a bounded smoke run on the first five selected entries:

```powershell
python -m iiif_entry_validator run --config config.example.json --limit 5
```

`--limit` is recorded in the run log so a partial run cannot be mistaken for a
complete validation.

## Test

```powershell
python -m unittest discover -s tests -v
```

The tests use a local deterministic HTTP server and therefore do not depend on
the availability or behavior of external institutions.

## Implementation structure

| Path | Responsibility |
|---|---|
| `iiif_entry_validator/models.py` | Module 1 compatibility and Module 2 result model |
| `iiif_entry_validator/checker.py` | HTTP requests, redirects, retries, parsing, and classification |
| `iiif_entry_validator/store.py` | JSONL, CSV, and TXT persistence |
| `iiif_entry_validator/pipeline.py` | Configuration, orchestration, partitioning, and logging |
| `iiif_entry_validator/cli.py` | Command-line interface |
| `tests/` | Deterministic unit and end-to-end tests |
