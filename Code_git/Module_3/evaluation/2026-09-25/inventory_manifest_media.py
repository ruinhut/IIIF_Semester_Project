"""Inventory page-image and file resources exposed by discovered IIIF Manifests."""

from __future__ import annotations

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
TIMEOUT_SECONDS = 12
WORKERS = 8


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def resource_id(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        candidate = value.get("id", value.get("@id"))
        return str(candidate) if candidate else None
    return None


def resource_type(value: Any) -> str:
    if not isinstance(value, Mapping):
        return ""
    candidate = value.get("type", value.get("@type", ""))
    if isinstance(candidate, list):
        candidate = candidate[0] if candidate else ""
    return str(candidate).split(":")[-1]


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def iter_bodies(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, list):
        for item in value:
            yield from iter_bodies(item)
        return
    if not isinstance(value, Mapping):
        return
    if resource_type(value) == "Choice":
        for item in as_list(value.get("items", value.get("item"))):
            yield from iter_bodies(item)
        return
    yield value


def add_link_values(target: set[str], value: Any) -> None:
    for item in as_list(value):
        identifier = resource_id(item)
        if identifier:
            target.add(identifier)


def extract_media(manifest: Mapping[str, Any]) -> dict[str, Any]:
    canvases: list[Mapping[str, Any]] = []
    if isinstance(manifest.get("items"), list):
        canvases.extend(
            item for item in manifest["items"]
            if isinstance(item, Mapping) and resource_type(item) == "Canvas"
        )
    for sequence in as_list(manifest.get("sequences")):
        if isinstance(sequence, Mapping):
            canvases.extend(
                item for item in as_list(sequence.get("canvases"))
                if isinstance(item, Mapping)
            )

    body_urls: set[str] = set()
    image_urls: set[str] = set()
    other_body_urls: set[str] = set()
    image_service_urls: set[str] = set()
    auxiliary_urls: set[str] = set()

    add_link_values(auxiliary_urls, manifest.get("rendering"))
    add_link_values(auxiliary_urls, manifest.get("seeAlso"))

    for canvas in canvases:
        add_link_values(auxiliary_urls, canvas.get("rendering"))
        add_link_values(auxiliary_urls, canvas.get("seeAlso"))
        bodies: list[Any] = []

        for annotation_page in as_list(canvas.get("items")):
            if not isinstance(annotation_page, Mapping):
                continue
            for annotation in as_list(annotation_page.get("items")):
                if isinstance(annotation, Mapping):
                    bodies.extend(as_list(annotation.get("body")))

        for annotation in as_list(canvas.get("images")):
            if isinstance(annotation, Mapping):
                bodies.extend(as_list(annotation.get("resource", annotation.get("body"))))

        for body_value in bodies:
            for body in iter_bodies(body_value):
                identifier = resource_id(body)
                media_type = str(body.get("format", "")).casefold()
                kind = resource_type(body).casefold()
                if identifier:
                    body_urls.add(identifier)
                    if kind == "image" or media_type.startswith("image/"):
                        image_urls.add(identifier)
                    else:
                        other_body_urls.add(identifier)
                for service in as_list(body.get("service", body.get("services"))):
                    service_id = resource_id(service)
                    if service_id:
                        image_service_urls.add(service_id)

    rights_values = []
    for key in ("rights", "license"):
        for item in as_list(manifest.get(key)):
            identifier = resource_id(item)
            if identifier:
                rights_values.append(identifier)

    return {
        "canvas_count": len(canvases),
        "content_body_count": len(body_urls),
        "image_body_count": len(image_urls),
        "other_body_count": len(other_body_urls),
        "image_service_count": len(image_service_urls),
        "auxiliary_file_count": len(auxiliary_urls),
        "rights_values": sorted(set(rights_values)),
    }


def fetch_one(item: tuple[str, dict[str, Any]]) -> dict[str, Any]:
    url, metadata = item
    result = {
        "manifest_url": url,
        "providers": metadata["providers"],
        "status": "unknown",
        "http_status": None,
        "error": "",
        "canvas_count": 0,
        "content_body_count": 0,
        "image_body_count": 0,
        "other_body_count": 0,
        "image_service_count": 0,
        "auxiliary_file_count": 0,
        "rights_values": [],
    }
    request = Request(
        url,
        headers={
            "Accept": "application/ld+json, application/json;q=0.9, */*;q=0.1",
            "User-Agent": "iiif-manifest-media-inventory/0.1 (+EPFL DHLAB academic research)",
        },
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            result["http_status"] = int(response.status)
            payload = response.read(MAX_RESPONSE_BYTES + 1)
            if len(payload) > MAX_RESPONSE_BYTES:
                result["status"] = "response_too_large"
                return result
            document = json.loads(payload.decode(response.headers.get_content_charset() or "utf-8-sig"))
            if not isinstance(document, Mapping):
                result["status"] = "json_not_object"
                return result
            if resource_type(document) != "Manifest":
                result["status"] = "not_manifest"
                return result
            result.update(extract_media(document))
            result["status"] = "valid_manifest"
    except HTTPError as exc:
        result["http_status"] = int(exc.code)
        result["status"] = "http_error"
        result["error"] = str(exc)
    except (URLError, TimeoutError, OSError) as exc:
        result["status"] = "network_error"
        result["error"] = str(exc)
    except (json.JSONDecodeError, UnicodeError) as exc:
        result["status"] = "invalid_json"
        result["error"] = str(exc)
    return result


def main() -> None:
    sources = [
        ROOT / "runs/development/module3/output/manifest_urls.jsonl",
        ROOT / "runs/test/module3/output/manifest_urls.jsonl",
    ]
    combined: dict[str, dict[str, Any]] = {}
    for source in sources:
        for row in read_jsonl(source):
            url = str(row["manifest_url"])
            slot = combined.setdefault(url, {"providers": set()})
            for provider in row.get("providers", []):
                name = provider.get("provider_name")
                if name:
                    slot["providers"].add(str(name))

    items = [
        (url, {"providers": sorted(value["providers"])})
        for url, value in sorted(combined.items())
    ]
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(fetch_one, item): item[0] for item in items}
        for index, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if index % 25 == 0 or index == len(items):
                print(f"Fetched {index}/{len(items)}")

    results.sort(key=lambda row: row["manifest_url"])
    output_jsonl = RESULTS / "manifest_media_inventory.jsonl"
    with output_jsonl.open("w", encoding="utf-8", newline="") as handle:
        for row in results:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    provider_totals: dict[str, Counter[str]] = defaultdict(Counter)
    for row in results:
        for provider in row["providers"]:
            provider_totals[provider]["manifest_count"] += 1
            if row["status"] == "valid_manifest":
                provider_totals[provider]["valid_manifest_count"] += 1
                for key in (
                    "canvas_count",
                    "content_body_count",
                    "image_body_count",
                    "other_body_count",
                    "image_service_count",
                    "auxiliary_file_count",
                ):
                    provider_totals[provider][key] += int(row[key])
                if row["rights_values"]:
                    provider_totals[provider]["manifest_with_rights_count"] += 1

    provider_rows = []
    for provider, totals in sorted(provider_totals.items()):
        provider_rows.append({"provider": provider, **dict(totals)})
    fields = [
        "provider", "manifest_count", "valid_manifest_count",
        "manifest_with_rights_count", "canvas_count", "content_body_count",
        "image_body_count", "other_body_count", "image_service_count",
        "auxiliary_file_count",
    ]
    with (RESULTS / "manifest_media_inventory_by_provider.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in provider_rows:
            writer.writerow({field: row.get(field, 0) for field in fields})

    valid = [row for row in results if row["status"] == "valid_manifest"]
    summary = {
        "inventory_date": "2026-09-25",
        "discovered_manifest_url_count": len(results),
        "valid_manifest_count_at_inventory_time": len(valid),
        "status_counts": dict(sorted(Counter(row["status"] for row in results).items())),
        "manifest_with_rights_count": sum(bool(row["rights_values"]) for row in valid),
        "canvas_count": sum(row["canvas_count"] for row in valid),
        "content_body_count": sum(row["content_body_count"] for row in valid),
        "image_body_count": sum(row["image_body_count"] for row in valid),
        "other_body_count": sum(row["other_body_count"] for row in valid),
        "image_service_count": sum(row["image_service_count"] for row in valid),
        "auxiliary_file_count": sum(row["auxiliary_file_count"] for row in valid),
        "limits": {
            "timeout_seconds": TIMEOUT_SECONDS,
            "max_response_bytes": MAX_RESPONSE_BYTES,
            "workers": WORKERS,
        },
        "interpretation": (
            "Counts describe resources declared by currently accessible Manifests. "
            "They are not downloaded image files and have not passed the future rights filter."
        ),
    }
    (RESULTS / "manifest_media_inventory_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
