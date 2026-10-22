"""Read original-language references from explicitly configured public catalogues."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import time
from typing import Any, Mapping
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .reference_text import _row


def canvas_image_bodies(canvas):
    """Return declared image bodies, keeping page-to-image ambiguity visible."""
    bodies = [a.get("resource", {}) for a in canvas.get("images", []) if isinstance(a, Mapping)]
    for page in canvas.get("items", []):
        for annotation in page.get("items", []):
            body = annotation.get("body", {})
            bodies.extend(body if isinstance(body, list) else [body])
    return [body for body in bodies if isinstance(body, Mapping)]


def canvas_image_urls(canvas):
    """Inspect image body/service identifiers only, excluding labels and prose."""
    urls = []
    for body in canvas_image_bodies(canvas):
        if not isinstance(body, Mapping):
            continue
        urls.append(str(body.get("id", body.get("@id", ""))))
        services = body.get("service", [])
        for service in services if isinstance(services, list) else [services]:
            if isinstance(service, Mapping):
                urls.append(str(service.get("id", service.get("@id", ""))))
    return urls


def path_value(value: Any, path: str):
    """Read a reviewed dot path without executing expressions from a recipe."""
    if path == "$":
        return value
    for part in path.split("."):
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    return value


def extract_catalogue_references(document, handoff, sources, cache_dir, audit):
    """Enrich an unambiguous one-page document without guessing page alignment.

    Only original-language transcription is exported as OCR reference. English
    translations and document-wide text of multi-page items are not attached to
    an arbitrary page. Raw catalogue JSON and selected field paths are retained.
    This optional enrichment never turns a metadata/download error into loss of
    the otherwise usable document or image.
    """
    providers = {p.get("provider_id") for p in handoff.get("providers", [])}
    output = []
    for source in sources:
        if source.get("provider_id") not in providers:
            continue
        event = {"manifest_id": handoff["manifest_id"], "source_id": source["source_id"],
                 "at": datetime.now(timezone.utc).isoformat()}
        canvases = document.get("items") if isinstance(document.get("items"), list) else [
            c for seq in document.get("sequences", []) for c in seq.get("canvases", [])]
        if len(canvases) != 1:
            event["status"] = "skipped_ambiguous_multi_page_alignment"
            audit.append(event)
            continue
        if len(canvas_image_bodies(canvases[0])) != 1:
            event["status"] = "skipped_ambiguous_canvas_image_alignment"
            audit.append(event)
            continue
        match = re.search(source["manifest_identifier_pattern"], handoff["manifest_url"])
        if not match:
            event["status"] = "manifest_identifier_not_matched"
            audit.append(event)
            continue
        identifier = match.group("identifier")
        url = source["record_url_template"].replace("{identifier}", quote(identifier, safe=""))
        event["catalogue_url"] = url
        if urlsplit(url).scheme not in {"http", "https"}:
            raise ValueError("Catalogue enrichment requires a public HTTP(S) URL")
        cache_dir.mkdir(parents=True, exist_ok=True)
        raw_path = cache_dir / (sha256(url.encode()).hexdigest()[:24] + ".json")
        try:
            if source.get("cache_only") and not raw_path.exists():
                event["status"] = "not_in_selected_catalogue_snapshot"
                continue
            if raw_path.exists():
                data = json.loads(raw_path.read_text(encoding="utf-8"))
                event["fetch_source"] = "cache"
            else:
                time.sleep(float(source.get("request_delay_seconds", 0.2)))
                request = Request(url, headers={"Accept": "application/json",
                    "User-Agent": "iiif-metadata-normalizer/0.1 (+EPFL DHLAB academic research)"})
                with urlopen(request, timeout=float(source.get("timeout_seconds", 25))) as response:
                    body = response.read(8 * 1024 * 1024 + 1)
                    if len(body) > 8 * 1024 * 1024:
                        raise ValueError("Catalogue JSON exceeded 8 MiB")
                    data = json.loads(body)
                    raw_path.write_bytes(body)
                    event.update(fetch_source="network", status_code=response.status)
            record = path_value(data, source.get("record_path", "$"))
            pages = path_value(record, source["page_records_path"])
            if not isinstance(pages, list) or len(pages) != 1:
                event["status"] = "catalogue_does_not_confirm_single_page"
                continue
            # Check the page identifier against the actual Canvas image body or
            # its declared services; a one-page count alone is not enough.
            page_identifier = str(path_value(pages[0], source["page_identifier_path"]) or "")
            canvas = canvases[0]
            pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(page_identifier) + r"(?![A-Za-z0-9])")
            if not page_identifier or not any(pattern.search(url) for url in canvas_image_urls(canvas)):
                event["status"] = "catalogue_image_does_not_match_canvas"
                continue
            text = path_value(record, source["original_text_path"])
            if not isinstance(text, str) or not text.strip():
                event["status"] = "no_original_language_reference"
                continue
            row = _row({"@id": url, "type": "TextualBody", "format": "text/plain", "value": text,
                        "label": "Institution original-language transcription",
                        "language": path_value(record, source["language_path"])},
                manifest_id=handoff["manifest_id"], manifest_url=handoff["manifest_url"],
                providers=handoff.get("providers", []), rights=handoff.get("rights_assessment", {}),
                canvas_index=0, canvas_id=canvas.get("id", canvas.get("@id")),
                canvas_label=str(canvas.get("label", "")), source_kind="catalogue_original_transcription",
                alignment_scope="canvas")
            if not row.get("inline_text", "").strip():
                event["status"] = "no_original_language_reference"
                continue
            row["text_role"] = "original_transcription"
            row["catalogue_provenance"] = {"url": url, "raw_json_path": str(raw_path.resolve()),
                "text_field": source["original_text_path"], "language_field": source["language_path"],
                "alignment_evidence": "single_canvas_and_matching_single_catalogue_image",
                "page_identifier": page_identifier}
            output.append(row)
            event["status"] = "original_reference_extracted"
        except HTTPError as exc:
            event.update(status="catalogue_enrichment_failed", error_type="HTTPError", status_code=exc.code, message=str(exc))
            exc.close()
        except Exception as exc:
            event.update(status="catalogue_enrichment_failed", error_type=type(exc).__name__, message=str(exc))
        finally:
            event["raw_json_path"] = str(raw_path.resolve())
            audit.append(event)
    return output
