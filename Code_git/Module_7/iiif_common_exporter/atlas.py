"""Offline adapter from the common handoff to EPFL Time Atlas RDE envelopes.

The contract is based on time-atlas-python 0.3.0, commit 2c7d59e.
No upload/publish request is made. Missing dates remain in staging; missing
coordinates never become guessed map observations. Research and public reuse
permissions retain their original, separate meanings.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping
from urllib.parse import urlsplit
from uuid import UUID, NAMESPACE_URL, uuid5

from jsonschema import Draft202012Validator, FormatChecker

from .models import MEDIA_SCHEMA_VERSION, RECORD_SCHEMA_VERSION
from .store import file_descriptor, read_jsonl, write_json, write_jsonl


TARGET_COMMIT = "2c7d59e03298bd5eec31faec74c7530254e026fa"
DEFAULT_PROFILE = Path(__file__).resolve().parents[1] / "profiles/time-atlas-0.3.json"
TARGET_SCHEMA = Path(__file__).resolve().parents[1] / "schemas/time-atlas-rde-0.3.schema.json"


def _http_url(value: Any) -> bool:
    """Check identifiers without rewriting provider URL spelling."""
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return False
    try:
        parts = urlsplit(value)
        return parts.scheme in {"http", "https"} and bool(parts.hostname) and not parts.username and not parts.password
    except ValueError:
        return False


def _date_range(dates: list[dict]) -> tuple[tuple[int, int] | None, str | None]:
    """Select the narrowest compatible stated year interval, never invent a date.

    Disjoint intervals require clarification; overlapping statements stay intact
    in the source metadata and are not silently intersected into a new claim.
    """
    spans = []
    for date in dates:
        start, end = date.get("start_year"), date.get("end_year")
        if type(start) is int and type(end) is int and 1 <= start <= end <= 9999:
            spans.append((start, end))
    if not spans:
        return None, "missing_or_unsupported_date"
    if max(s[0] for s in spans) > min(s[1] for s in spans):
        return None, "conflicting_date_intervals"
    return min(spans, key=lambda s: (s[1] - s[0], s)), None


def _times(span: tuple[int, int]) -> dict[str, str]:
    """Expand year precision to an inclusive UTC interval for the target model."""
    return {"start_time": f"{span[0]:04d}-01-01T00:00:00Z", "end_time": f"{span[1]:04d}-12-31T23:59:59Z"}


def _profile(path: Path | None) -> dict:
    value = json.loads((path or DEFAULT_PROFILE).read_text(encoding="utf-8-sig"))
    if value.get("target") != "epfl-time-atlas-rde-0.3":
        raise ValueError("Unsupported Time Atlas target profile")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value.get("dataset_slug", "")):
        raise ValueError("dataset_slug must contain lowercase ASCII words separated by hyphens")
    name = value.get("dataset_name")
    if not isinstance(name, dict) or not name or not all(
        isinstance(k, str) and isinstance(v, list) and v and all(isinstance(s, str) and s.strip() for s in v)
        for k, v in name.items()
    ):
        raise ValueError("dataset_name must be a nonempty multilingual dictionary of string lists")
    if not re.fullmatch(r"\d+\.\d+\.\d+", value.get("dataset_version", "")):
        raise ValueError("dataset_version must use X.Y.Z")
    if not _http_url(value.get("namespace_url")):
        raise ValueError("namespace_url must be an HTTP(S) URL")
    areas = value.get("external_area_ids", [])
    if not isinstance(areas, list) or len(set(areas)) != len(areas):
        raise ValueError("external_area_ids must be a list without duplicates")
    for area_id in areas:
        UUID(area_id)
    return value


def _unique_index(rows: list[dict], key: str) -> dict[str, dict]:
    """Reject duplicate/missing join keys rather than silently overwriting rows."""
    result = {}
    for row in rows:
        value = row.get(key)
        if not isinstance(value, str) or not value or value in result:
            raise ValueError(f"Missing or duplicate {key}: {value!r}")
        result[value] = row
    return result


def _spatial_rows(profile: dict, profile_path: Path | None, records: dict) -> dict[str, list[dict]]:
    """Read optional evidence-backed WGS84 points; no geocoding is performed."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    filename = profile.get("spatial_annotations_jsonl")
    if not filename:
        return grouped
    path = Path(filename)
    if not path.is_absolute():
        path = (profile_path or DEFAULT_PROFILE).parent / path
    seen = set()
    for row in read_jsonl(path):
        if row.get("record_id") not in records:
            raise ValueError("Spatial annotation does not reference a common record")
        if not isinstance(row.get("annotation_id"), str) or not row["annotation_id"] or row["annotation_id"] in seen:
            raise ValueError("Spatial annotations need unique annotation_id values")
        seen.add(row["annotation_id"])
        coordinates = row.get("geometry", {}).get("coordinates")
        if row.get("geometry", {}).get("type") != "Point" or not isinstance(coordinates, list) or len(coordinates) != 2:
            raise ValueError("Spatial annotation needs a GeoJSON Point [longitude, latitude]")
        if not all(type(v) in {int, float} and math.isfinite(v) for v in coordinates):
            raise ValueError("Spatial coordinates must be finite numbers")
        if not (-180 <= coordinates[0] <= 180 and -90 <= coordinates[1] <= 90):
            raise ValueError("Spatial coordinates must be WGS84 longitude/latitude")
        if not _http_url(row.get("source_url")) or not str(row.get("relationship") or "").strip() or not str(row.get("evidence") or "").strip():
            raise ValueError("Spatial annotation needs source_url, relationship and evidence")
        grouped[row["record_id"]].append(row)
    return grouped


def _envelope(name: str, kind: str, rows: list[dict], slug: str, now: str) -> dict:
    """Write the same per-type envelope shape used by RDECollection."""
    value = {"name": name, "type_in_file": [kind], "creation_time": now}
    if kind in {"dataset", "historical_record", "observation"}:
        value["related_dataset_slugs"] = [slug]
    value["rde_objects"] = rows
    return value


def _configuration() -> dict:
    fields = []
    for key, kind, label in [("title", "STRING", "Title"), ("identifier", "URL", "Identifier"),
                             ("manifest_url", "URL", "Source Manifest"), ("provider_names", "STRING", "Providers"),
                             ("place_labels", "STRING", "Reported places"), ("image_count", "INTEGER", "Images"),
                             ("rights_category", "STRING", "Rights category")]:
        fields.append({"id": key, "type": kind, "display_label": {"en": [label]},
                       "nullable": True, "indexable": kind == "STRING", "short_display": key == "title", "hidden": False})
    return {"metadata_field_config": fields, "main_label": "${title}", "sub_label": "${provider_names}",
            "display_thumbnail": False, "external_source": False}


def export_atlas(
    input_directory: Path,
    output_directory: Path,
    *,
    profile_path: Path | None = None,
) -> dict[str, Any]:
    """Export a separate Atlas bundle from an existing Module 7 output directory.

    Returns counts and readiness diagnostics. Schema and referential failures are
    errors; absent descriptive values are reported and retained in staging.
    Input files are never modified. Output must be new/empty to prevent stale
    import files from a previous, differently configured export.
    """
    source, output = input_directory.resolve(), output_directory.resolve()
    profile_path = profile_path.resolve() if profile_path else None
    if output == source or output in source.parents:
        raise ValueError("Atlas output must not replace the Module 7 input directory or its ancestors")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Atlas output directory is not empty; choose a new directory")
    profile = _profile(profile_path)
    records = read_jsonl(source / "common_records.jsonl")
    media = read_jsonl(source / "common_media.jsonl")
    references = read_jsonl(source / "institution_reference_texts.jsonl") if (source / "institution_reference_texts.jsonl").is_file() else []
    ocr = read_jsonl(source / "ocr_document_profiles.jsonl") if (source / "ocr_document_profiles.jsonl").is_file() else []
    record_index = _unique_index(records, "record_id")
    media_index = _unique_index(media, "resource_id")
    _unique_index(references, "reference_text_id")
    _unique_index(ocr, "record_id")
    media_by_record: dict[str, list[dict]] = defaultdict(list)
    refs_by_record: dict[str, list[dict]] = defaultdict(list)
    for row in records:
        if row.get("schema_version") != RECORD_SCHEMA_VERSION:
            raise ValueError("Unsupported common record schema_version")
    for row in media:
        if row.get("schema_version") != MEDIA_SCHEMA_VERSION or row.get("record_id") not in record_index:
            raise ValueError("Unsupported media schema or orphan media record")
        media_by_record[row["record_id"]].append(row)
    for row in references:
        if row.get("record_id") not in record_index:
            raise ValueError("Orphan reference text record")
        if row.get("resource_id") is not None:
            image = media_index.get(row["resource_id"])
            if image is None or image["record_id"] != row["record_id"] or image.get("canvas", {}).get("id") != row.get("canvas", {}).get("id"):
                raise ValueError("Reference text/image/Canvas join is inconsistent")
        refs_by_record[row["record_id"]].append(row)
    for row in ocr:
        if row["record_id"] not in record_index:
            raise ValueError("Orphan OCR profile")
    spatial = _spatial_rows(profile, profile_path, record_index)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    slug = profile["dataset_slug"]
    namespace = uuid5(NAMESPACE_URL, profile["namespace_url"].rstrip("/") + "/atlas/" + slug)

    def uid(kind: str, value: str) -> str:
        return str(uuid5(namespace, kind + ":" + value))

    dataset_id = uid("dataset", slug)
    historical_records, observations, links, staged, readiness = [], [], [], [], []
    intervals = []
    for record in records:
        rid = record["record_id"]
        obj = record.get("object", {})
        manifest_url = record.get("source", {}).get("manifest_url")
        if not _http_url(manifest_url):
            raise ValueError(f"Record {rid} has no valid source Manifest URL")
        images = sorted(media_by_record[rid], key=lambda r: (r.get("sequence") or 0, r["resource_id"]))
        refs = refs_by_record[rid]
        if record.get("media_count") != len(images):
            raise ValueError(f"Record {rid} media_count differs from the linked image count")
        rights = record.get("rights", {})
        if rights.get("research_status") != "retained" or rights.get("usage_permissions", {}).get("academic_analysis") is not True:
            raise ValueError(f"Record {rid} has no explicit research handoff permission")
        span, pending = _date_range(obj.get("dates", []))
        hr_id = uid("historical_record", manifest_url)
        issues = [pending] if pending else []
        if not spatial[rid]:
            issues.append("no_evidence_backed_coordinates")
        if not obj.get("places"):
            issues.append("no_reported_place")
        staged.append({"record_id": rid, "atlas_historical_record_id": hr_id if span else None,
                       "common_record": record, "media": images, "institution_reference_texts": refs})
        readiness.append({"record_id": rid, "manifest_url": manifest_url, "rde_exported": bool(span),
                          "issues": issues, "image_count": len(images), "reference_text_count": len(refs),
                          "public_reuse_eligible": rights.get("public_reuse_eligible", False)})
        if span is None:
            continue
        intervals.append(span)
        own_observations = []
        for point in spatial[rid]:
            observation_id = uid("observation", manifest_url + ":" + point["annotation_id"])
            own_observations.append(observation_id)
            observations.append({"id": observation_id, "rde_type": "observation", "historical_record": hr_id,
                                 "geometry": point["geometry"], "has_geometries": [], "part_of_point_of_interest": None})
        provider_names = [r.get("provider_name", "") for r in record.get("source", {}).get("providers", [])]
        statements = rights.get("statements", [])
        historical_records.append({
            "id": hr_id, "rde_type": "historical_record", "dataset": dataset_id,
            **_times(span), "paradata": "a", "has_observations": own_observations,
            "rights_attribution": "; ".join(str(s.get("raw_value")) for s in statements if s.get("raw_value")) or rights.get("category"),
            "metadata": {"title": obj.get("title"), "identifier": obj.get("identifier"), "record_id": rid,
                         "manifest_url": manifest_url, "provider_names": "; ".join(provider_names),
                         "place_labels": "; ".join(str(p.get("raw") or "") for p in obj.get("places", [])),
                         "image_count": len(images), "reference_text_count": len(refs), "rights_category": rights.get("category"),
                         "rights": deepcopy(rights), "common_record": deepcopy(record), "media": images,
                         "institution_reference_texts": refs, "spatial_evidence": spatial[rid],
                         "granularity": "manifest_document_not_extracted_content",
                         "temporal_mapping": {"method": "narrowest_compatible_stated_year_interval", "selected_years": list(span),
                                              "precision": "year_bounds_not_exact_timestamps", "original_dates": obj.get("dates", [])}}
        })
        links.append({"record_id": rid, "atlas_historical_record_id": hr_id, "atlas_dataset_id": dataset_id,
                      "manifest_url": manifest_url, "resource_ids": [r["resource_id"] for r in images]})

    if len({r["id"] for r in historical_records}) != len(historical_records):
        raise ValueError("Multiple common records use the same Manifest URL; deduplicate before Atlas export")
    areas = []
    area_ids = list(profile.get("external_area_ids", []))
    # Only a real set of explicitly supplied points can define a spatial extent.
    if observations and not area_ids:
        xs = [r["geometry"]["coordinates"][0] for r in observations]
        ys = [r["geometry"]["coordinates"][1] for r in observations]
        left, right, bottom, top = min(xs), max(xs), min(ys), max(ys)
        if left == right:
            left, right = max(-180, left - 1e-9), min(180, right + 1e-9)
        if bottom == top:
            bottom, top = max(-90, bottom - 1e-9), min(90, top + 1e-9)
        area_id = uid("area", json.dumps([left, bottom, right, top]))
        area_ids = [area_id]
        areas.append({"id": area_id, "rde_type": "area", "slug": slug + "-observed-extent",
                      "name": {"en": [slug + " evidence-backed point extent"]},
                      "geometry": {"type": "Polygon", "coordinates": [[[left, bottom], [right, bottom], [right, top], [left, top], [left, bottom]]]}})
    datasets = []
    if historical_records:
        datasets.append({"id": dataset_id, "rde_type": "dataset", "slug": slug, "name": profile["dataset_name"],
                         **_times((min(s[0] for s in intervals), max(s[1] for s in intervals))),
                         "creation_time": now, "version": profile["dataset_version"], "sources": [],
                         "has_areas": area_ids, "configuration": _configuration(),
                         "metadata": [{"type": "STRING", "label": {"en": ["Scope"]},
                                       "value": {"en": ["Research harvest; public redistribution permissions remain per record. Document metadata, not extracted historical events."]}}]})
    schema = json.loads(TARGET_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    groups = [("dataset", "dataset", datasets), ("historical_records", "historical_record", historical_records),
              ("observations", "observation", observations), ("areas", "area", areas)]
    envelopes = [_envelope(name, kind, rows, slug, now) for name, kind, rows in groups if rows]
    for envelope in envelopes:
        validator.validate(envelope)
    # All data preparation and validation finishes before creating output files.
    (output / "rde").mkdir(parents=True, exist_ok=True)
    (output / "staging").mkdir()
    paths = []
    for envelope in envelopes:
        path = output / "rde" / (envelope["name"] + ".json")
        # Preserve header-before-payload ordering for Atlas streaming importers.
        path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths.append(path)
    package = output / "rde/collection.jsonl"
    package.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in envelopes), encoding="utf-8")
    write_jsonl(output / "staging/records.jsonl", staged)
    write_jsonl(output / "staging/ocr_document_profiles.jsonl", ocr)
    write_jsonl(output / "record_readiness.jsonl", readiness)
    write_jsonl(output / "record_links.jsonl", links)
    spatial_ready = bool(datasets and area_ids)
    summary = {
        "adapter_version": "0.1.0", "generated_at": now, "target_library": "time-atlas-python 0.3.0",
        "target_commit": TARGET_COMMIT, "team_schema_status": "not_supplied_not_certified",
        "input_records": len(records), "staged_records": len(staged), "historical_records": len(historical_records),
        "pending_date_records": len(records) - len(historical_records), "media": len(media), "reference_texts": len(references),
        "ocr_profiles": len(ocr), "datasets": len(datasets), "observations": len(observations), "local_areas": len(areas),
        "public_reuse_eligible_records": sum(r.get("rights", {}).get("public_reuse_eligible") is True for r in records),
        "local_envelope_validation": "passed", "spatial_index_configured": spatial_ready,
        "external_area_verification_required": bool(profile.get("external_area_ids")),
        "self_contained_collection": bool(spatial_ready and not profile.get("external_area_ids")),
        "sdk_validation": "not_run_by_exporter_use_validate_atlas_bundle.py",
        "server_import_tested": False, "uploaded": False, "published": False,
        "readiness": "candidate_collection" if spatial_ready else "staging_missing_dataset_area_or_dates",
        "input_directory": str(source), "output_directory": str(output),
        "notes": ["All research records remain in staging, including missing-date and unknown/restricted-rights records.",
                  "No geocoding, OCR extraction, reference-text download, backend source registration or publication is performed.",
                  "Dataset.sources stays empty: external Manifest URLs are retained in HR metadata, not invented backend UUIDs.",
                  "Area configuration is required by the current SDK's strict validation; text-only place names are not coordinates."]}
    write_json(output / "atlas_export_report.json", summary)
    write_json(output / "profile_used.json", profile)
    write_json(output / "files.json", {"files": [file_descriptor(p) for p in paths + [package]]})
    log = output / "log" / ("Atlas_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_log.txt")
    log.parent.mkdir()
    log.write_text("\n".join(f"{k}: {v}" for k, v in summary.items()) + "\n", encoding="utf-8")
    return summary
