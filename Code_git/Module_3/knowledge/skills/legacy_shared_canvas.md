# Explicit Shared Canvas compatibility

Some public institutional Manifest files use the historical context
`http://www.shared-canvas.org/ns/context.json`. They must not be described as
modern IIIF Presentation 2 or 3 merely because their structure is readable.

For a reviewed JSON/HTML identifier skill, set:

```json
{"allow_legacy_shared_canvas": true}
```

The default remains false. Acceptance requires the exact known Shared Canvas
context, a Manifest type, and a sequences array. Unknown contexts remain rejected
even when this compatibility option is enabled. Empty or malformed media
structures still undergo Module 4 validation.

Module 4 retains the original JSON and context and emits:

- `source_format: legacy_shared_canvas`;
- a `legacy_shared_canvas_context` warning;
- the existing `presentation_version: 2` parser selector, denoting compatible
  sequence traversal rather than source conformance certification.

No source-specific name branch is used. The Manifest URL handoff and downstream
record contracts remain compatible. This family was verified with the
Smithsonian official featured Manifest page; six samples subsequently passed
structural/media extraction and an actual image bundle was downloaded.

See `../institutions/2026-10-19_third_provider_completion.md` for evidence and scope.
