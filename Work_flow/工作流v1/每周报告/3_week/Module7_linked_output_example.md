# Module 7 linked-output example

## Relationship

```text
common_records: canonical document record
record_id = manifest-5c57a6b89f846c5f
│
├── common_media: Canvas and image resources belonging to the document
│   record_id = manifest-5c57a6b89f846c5f
│
└── ocr_document_profiles: OCR-oriented description of the document
    record_id = manifest-5c57a6b89f846c5f
```

The shared `record_id` is the join key. The full example files are:

- `example_common_record.json`
- `example_common_media.json`
- `example_ocr_document_profile.json`
- `Fragmentarium_example_page.jpg`

No ground-truth candidate file is included in this demonstration.

## 1. `common_records`: canonical document record

Selected fields from `example_common_record.json`:

```json
{
  "record_id": "manifest-5c57a6b89f846c5f",
  "object": {
    "title": "Tübingen, Konviktsbibliothek Wilhelmsstift, KH 5184",
    "languages": [{"code": "de", "raw": "German"}],
    "dates": [{"start_year": 1275, "end_year": 1325}],
    "types": [
      {"source_label": "Material", "value": "Parchment"},
      {"source_label": "Document Type", "value": "Fragment"},
      {"source_label": "Script Type", "value": "Gothic Script (generic)"}
    ]
  },
  "media_count": 3,
  "rights": {
    "category": "open_license",
    "public_reuse_eligible": true
  }
}
```

This record says what the document is and reports that three media records are
linked to it. It does not embed all three image records.

## 2. `common_media`: one linked Canvas/image record

Selected fields from `example_common_media.json`:

```json
{
  "record_id": "manifest-5c57a6b89f846c5f",
  "resource_id": "resource-9e005357d509c62648f4",
  "sequence": 0,
  "canvas": {
    "id": "https://fragmentarium.ms/.../Wilhelmsstift_KH_5184_IIv_Ir.jp2.json",
    "label": "Wilhelmsstift_KH_5184_IIv_Ir"
  },
  "image": {
    "id": "https://fragmentarium.ms/loris/.../full/full/0/default.jpg",
    "service_urls": ["https://fragmentarium.ms/loris/.../IIv_Ir.jp2"]
  }
}
```

The displayed `Fragmentarium_example_page.jpg` was downloaded successfully
from this Image API service: HTTP 200, JPEG, 1000 × 440 pixels.

![Downloaded Fragmentarium page](Fragmentarium_example_page.jpg)

## 3. `ocr_document_profiles`: OCR-oriented document description

Selected fields from `example_ocr_document_profile.json`:

```json
{
  "record_id": "manifest-5c57a6b89f846c5f",
  "languages": [{"code": "de", "raw": "German"}],
  "date_profile": {
    "start_year": 1275,
    "end_year": 1400,
    "century_labels": ["13th century", "14th century"]
  },
  "scripts": [{"value": "Gothic script"}],
  "document_types": [
    {"source_label": "Material", "value": "Parchment"},
    {"source_label": "Document Type", "value": "Fragment"}
  ],
  "production_method": {
    "category": "unknown",
    "confidence": "unknown"
  },
  "media_count": 3
}
```

The image looks handwritten, but the profile remains `unknown` because the
current classifier requires explicit metadata evidence and has not inspected
the pixels. This is intentional conservative behaviour.

## Current missing relationship

The example links the document, its image and its OCR-oriented description.
It does not yet link the Canvas to institution-provided OCR or transcription
text. That requires preservation of `seeAlso`, `otherContent`, ALTO, hOCR and
Presentation 3 supplementing annotations through Modules 4–7.
