---
name: iiif-time-atlas-project
description: "Support Boheng Shang's EPFL DHLAB IIIF and Time Atlas Bachelor semester project: interpret supervisor materials, plan and implement the rights-filtered IIIF provider census and manifest-harvesting pipeline, prepare weekly reports and meetings, and maintain beginner-friendly Chinese documentation. Use only for this project."
---

# IIIF and Time Atlas Semester Project

Support Boheng Shang throughout the EPFL DHLAB Autumn 2026 semester project. Answer in clear Chinese by default. When an English technical term is necessary, explain it in Chinese on first use and then prefer the Chinese term.

## Source priority

Use sources in this order:

1. The latest message or decision from Frédéric Kaplan or Ziyi Liu.
2. Boheng's individual sheet, “One door to a scattered heritage,” on pages 59–60 of the teacher's project PDF.
3. Current official IIIF, EPFL DHLAB, and Time Atlas documentation.
4. The distilled references in this skill.

The individual sheet narrows the broad public project description. Treat Boheng's assigned work as the front half of the data pipeline: provider census, resource discovery, manifest harvesting, rights filtering, metadata normalization, and delivery into the common schema. Do not present OCR, HTR, layout analysis, entity extraction, or web-interface development as his main assignment unless a later supervisor message changes the scope.

Clearly label implementation suggestions and inferences. Do not state them as supervisor requirements.

## Read the relevant reference

- For scope, people, authoritative files, accepted decisions, registration, and dates, read [references/project-context.md](references/project-context.md).
- For IIIF concepts, Change Discovery, Registry, manifests, pipeline design, implementation, or evaluation, read [references/technical-guide.md](references/technical-guide.md).
- For weekly planning, meetings, progress emails, document editing, and communication style, read [references/operations-and-communication.md](references/operations-and-communication.md).

Read only the references needed for the current request. When the user provides a newer email, calendar invitation, assignment sheet, schema, repository, or server instruction, inspect it and update the conclusion accordingly.

## Working principles

- Build a small but complete end-to-end pipeline first. Optimize individual modules only after real data passes from discovery through downstream delivery.
- Keep modules separable: provider census, discovery, manifest retrieval, rights handling, field normalization, common-schema validation, and reliable storage.
- Develop and debug locally on a small fixed sample, then run the same configurable code in the approved DHLAB or Time Atlas server environment.
- Preserve raw values, normalized values, source URLs, processing status, and failure reasons. Never silently discard missing or ambiguous metadata.
- Confirm the rights allowlist, common schema, first data source, handoff format, server access, and Time Atlas interface with the supervisors rather than inventing them.
- For current technical facts, browse primary official documentation. Remember that `https://iiif.io/api/discovery/1.0/` is a human-readable specification page, while `https://registry.iiif.io/index.json` is a machine-readable registry entry point.

## Deliverables and file work

When maintaining the project guide, use this default location unless the user specifies another:

`E:\exchange-epfl\Semester_Project\Work_flow`

Keep Markdown as the editable source and regenerate the PDF after substantive changes. Verify the PDF text, page count, Chinese rendering, tables, and line wrapping. Preserve teacher-provided source files.

Draft messages for the user to review. Do not send email or modify external systems unless the user explicitly requests that action.

