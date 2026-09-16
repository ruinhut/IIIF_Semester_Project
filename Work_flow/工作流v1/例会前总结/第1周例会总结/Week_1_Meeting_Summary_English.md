# Week 1 Meeting Summary

## 1. Project objective

My task is to develop the first half of the IIIF data pipeline: survey IIIF providers, discover and retrieve Manifests, filter resources according to their rights statements, normalize metadata such as identifier, date, place, rights, and source, and deliver the results to the downstream pipeline in the team's common schema.

## 2. Current progress

1. I have studied the basic concepts of IIIF, Manifests, the Change Discovery API, Activity Streams, and the IIIF Registry.
2. I have refined the original three-machine pipeline into modules with clearer responsibilities. Logging will cover every stage.
3. I have revised the four-week plan so that a small end-to-end sample is tested in the second week. This should reveal interface problems early.
4. The Codex provider sorter has not yet been implemented. Its inputs, outputs, test sample, and acceptance criteria have only been defined at the planning level.

## 3. Current pipeline design

```text
IIIF provider storage and selection
→ IIIF entry-point access and availability check
→ IIIF resource discovery
→ Manifest retrieval and structural validation
→ rights identification and filtering
→ resource reading and metadata normalization
→ common-schema validation and export
→ downstream processing
```

The modules have the following responsibilities:

- Provider sorter: stores provider information and selects the providers and IIIF entry points required for the current run.
- Address accessor: checks whether an entry point is accessible and records the status code, access time, and failure reason.
- Resource discoverer: follows the pages of an Activity Stream or Collection, extracts and deduplicates Manifest URLs, and preserves provenance and activity information. It aggregates Manifest references rather than merging Manifest contents.
- Manifest retriever and validator: retrieves JSON data and checks whether it can be parsed and has a basic IIIF structure.
- Rights filter: preserves the original rights statement, maps it to a normalized category, and applies rules confirmed by the supervisors.
- Content reader and metadata normalizer: extracts and normalizes identifier, date, place, rights, and source while preserving raw values and explicit missing states.
- Common-schema validator and exporter: checks field names, types, required fields, and provenance, then exports records in the format required downstream.
- Logging: records the source, processing time, status, and failure reason throughout the pipeline.

## 4. Four-week plan

- Week 1 (14–20 September): finalize module boundaries, study IIIF fundamentals, inspect a few real samples, and confirm the common schema, rights rules, and delivery format with the downstream team.
- Week 2 (21–27 September): implement the first version of entry-point access and resource discovery, then use a fixed sample to connect provider selection, access checking, resource discovery, and Manifest retrieval.
- Week 3 (28 September–4 October): implement Manifest validation, rights handling, core-field extraction, metadata normalization, and common-schema conversion; produce a small file for downstream testing.
- Week 4 (5–11 October): test the complete first-half pipeline with the downstream component; add failure reporting, deduplication, and basic retries; verify consistency and traceability.

## 5. Points to align during the meeting

1. Should the first version start from the IIIF Registry, Europeana Change Discovery, or another source?
2. Where is the official common-schema definition, and who maintains it?
3. Which rights categories are allowed, and how should unknown or ambiguous statements be handled?
4. How many Manifests should the fixed initial sample contain?
5. Does Hafidz need JSON, JSONL, or another delivery format, and when should the first handoff take place?
6. Are there existing code, provider surveys, or server resources from Ziyi that can be reused?
7. Will Time Atlas receive the data through a file import, an API, or a continuously running service?

## 6. Meeting duration and presentation approach

According to Professor Kaplan's email, the formal weekly IIIF supervision starts on 22 September 2026 and runs every Tuesday from 11:00 to 11:20, for a total of 20 minutes. The local materials do not mention a separate formal supervision meeting on 15 September. If tomorrow's meeting is a separately arranged group meeting, its latest invitation should be treated as authoritative.

A 20-minute supervision meeting does not require a long presentation. I suggest spending about three minutes on the project objective, the current pipeline, and the four-week plan, then using most of the meeting to align the interfaces, rights policy, first data source, and downstream requirements.
