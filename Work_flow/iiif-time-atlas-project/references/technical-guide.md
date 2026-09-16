# Technical guide

## Beginner mental model

Treat the project as a library logistics system:

```text
Find institutions and their update catalogues
→ discover object-list URLs
→ retrieve current object descriptions
→ check rights
→ extract and normalize core fields
→ emit one common record format
→ hand records to extraction and Time Atlas
```

This is closer to standards-based API harvesting and ETL than to conventional HTML web scraping.

- Extract: discover and retrieve IIIF records.
- Transform: filter rights and normalize fields.
- Load or deliver: emit records in the common schema.

Avoid Selenium or site-specific HTML scraping unless the supervisor confirms that a source has no usable standard interface and the extra connector is worth maintaining.

## Core terms

- IIIF: International Image Interoperability Framework, a standard used by libraries, museums, and archives to publish images and related information.
- Manifest: a JSON resource description for one digital object. It may contain identity, label, provider, metadata, rights, page order, and image links.
- API: a machine-readable interface accessed through HTTP requests.
- Change Discovery API: the IIIF specification for publishing lists of resource changes.
- Activity Stream: a paginated ordered feed of resource activities.
- Registry: a directory that points to institutions and their activity streams.
- Common schema: the team's agreed output fields and types.
- JSONL: line-delimited JSON, with one independent record per line.
- Rights statement: a URI or statement describing permitted use of a resource.

## Do not confuse these URLs

1. `https://iiif.io/api/discovery/1.0/`
   - Human-readable technical specification.
   - Explains required JSON structures and processing behavior.
   - It is not the dataset and should not be harvested as JSON.
2. `https://registry.iiif.io/`
   - Human-readable registry site.
3. `https://registry.iiif.io/index.json`
   - Machine-readable registry entry point.
   - Leads to registry pages and registered activity-stream URLs.
4. Provider activity-stream URL
   - Lists resources that were created, updated, deleted, moved, added, or removed.
5. Manifest URL
   - Returns the current full description of a particular IIIF resource.

An `Update` activity normally says that a resource changed and gives its manifest URL and time. It does not necessarily provide a field-by-field difference. To identify exact field changes, compare a previously stored manifest with the newly retrieved version.

The Registry is voluntarily maintained and may not contain every institution that uses IIIF.

## Change Discovery levels

- Level 0: unique resource references; useful for baseline discovery.
- Level 1: adds timestamps and ordering, so a client can stop when it reaches already processed changes.
- Level 2: adds explicit activity types such as create, delete, and move, enabling better synchronization.

For repeat runs, store the last processed activity or timestamp and process only later changes when the provider supports it.

## Modular architecture

### Module 1: Provider census

Record provider name, institution URL, discovery or stream URL, collection focus, estimated size, rights distribution, status, and last checked time.

### Module 2: Unified discovery

Read ordered collections and pages, follow pagination, collect manifest URLs, preserve activity type and time, and avoid provider-specific logic where the shared standard is enough.

### Module 3: Manifest retrieval and validation

Fetch JSON, check response and basic structure, record provenance, classify failures, and avoid duplicate requests.

### Module 4: Rights handling

Preserve the raw statement, map known statements to a confirmed category, apply the supervisor-approved allowlist, and record exclusion reasons. Never guess the allowlist.

### Module 5: Metadata normalization

At minimum produce:

- `identifier`: stable object or manifest identifier.
- `date`: raw date and normalized date when defensible.
- `place`: raw place and normalized form when defensible.
- `rights`: raw statement, normalized category, and allow status.
- `source`: institution, manifest URL, and discovery origin.

Do not silently discard a record when a field is missing. Preserve raw values and use explicit missing or unknown states.

### Module 6: Common-schema validation

Map provider fields to the common schema, validate required and optional fields, preserve provenance, version the schema, and create a sample Hafidz can read.

### Module 7: Reliable operation

After the complete baseline works, add pagination, batching, deduplication, retries, rate limiting, checkpoints, logs, statistics, configurable paths, and reproducible commands.

## First complete baseline

Use one standard discovery source and a small fixed sample:

```text
Read registry or provider stream
→ discover about 10–100 manifest URLs
→ fetch and validate manifests
→ read and filter rights
→ extract the five core fields
→ map to the provisional common schema
→ export JSONL or the confirmed handoff format
→ let Hafidz read the sample
```

Complete this before expanding source coverage or perfecting any one normalizer.

## Evaluation dimensions

A semester-level result can measure:

- Coverage: providers, streams, manifests, and collections discovered.
- Interoperability: how many providers work without custom code.
- Rights handling: distribution, allowed rate, unknown rate, and exclusion reasons.
- Metadata quality: completeness and normalization success for date, place, source, and identifier.
- Reliability: request success, retry recovery, restart behavior, and duplicate rate.
- Incremental behavior: whether later runs process only new or changed resources.
- Performance: throughput, storage, and runtime at meaningful scale.
- Traceability: whether every output returns to its original manifest and institution.
- Downstream compatibility: whether Hafidz and Time Atlas can consume the output.

## Local and server execution

Develop locally on a small fixed sample. Keep source URLs, paths, batch sizes, credentials, and output destinations in configuration rather than hard-coding them.

After local validation, move the same code to the approved DHLAB or Time Atlas environment:

1. Recreate dependencies and credentials.
2. Run the same fixed sample and compare outputs.
3. Connect approved storage or interfaces.
4. Increase batch size gradually.
5. Verify rate limits, checkpoint recovery, logs, and storage.
6. Record code and configuration versions.

Confirm server access, container requirements, data locations, quotas, and whether the final integration is a file import, API call, or long-running service.

