"""Resolve stale image bodies through their explicitly declared IIIF services."""

import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request

from .fetch import DownloadError, ImageFetcher


def download_image(item, fetcher: ImageFetcher, temporary: Path):
    """Try the body first, then a bounded, validated Image API alternative."""
    trace = {"method": "direct", "original_url": item.download_url, "attempts": []}
    try:
        result = fetcher.download(item.download_url, temporary)
        trace["attempts"].append({"url": item.download_url, "status": "downloaded"})
        return result, trace
    except DownloadError as original:
        trace["attempts"].append({"url": original.url, "status": "failed", "error_type": original.error_type,
                                  "status_code": original.status_code})
        # Authentication, access restrictions and transport failures are not URL repairs.
        if original.status_code not in {400, 404, 410, 415, 501} and original.error_type not in {"invalid_image_bytes", "non_image_content_type"}:
            raise
        image = item.media.get("image", {})
        info_urls = []
        if image.get("info_json_url"):
            info_urls.append(str(image["info_json_url"]))
        for service in image.get("service_urls", []):
            base = str(service).rstrip("/")
            info_urls.append(base if base.endswith("/info.json") else base + "/info.json")
        last_error = original
        for info_url in dict.fromkeys(info_urls):
            if urlsplit(info_url).scheme not in {"http", "https"}:
                continue
            try:
                fetcher.sleeper(0.15)
                request = Request(info_url, headers={"Accept": "application/json, application/ld+json",
                                                     "User-Agent": fetcher.user_agent})
                with fetcher.opener(request, timeout=fetcher.timeout_seconds) as response:
                    body = response.read(1024 * 1024 + 1)
                if len(body) > 1024 * 1024:
                    raise ValueError("Image information exceeded 1 MiB")
                info = json.loads(body.decode("utf-8-sig"))
                candidates = image_api_candidates(info, info_url)
                trace["attempts"].append({"url": info_url, "status": "image_service_validated"})
            except Exception as exc:
                trace["attempts"].append({"url": info_url, "status": "info_failed", "message": str(exc)})
                continue
            for candidate in candidates:
                if candidate == item.download_url:
                    continue
                try:
                    fetcher.sleeper(0.15)
                    result = fetcher.download(candidate, temporary)
                    trace.update(method="declared_iiif_image_service", info_json_url=info_url)
                    trace["attempts"].append({"url": candidate, "status": "downloaded"})
                    return result, trace
                except DownloadError as exc:
                    last_error = exc
                    trace["attempts"].append({"url": candidate, "status": "failed", "status_code": exc.status_code,
                                              "error_type": exc.error_type})
                    if exc.status_code in {401, 403}:
                        exc.resolution_trace = trace
                        raise
        last_error.resolution_trace = trace
        raise last_error


def image_api_candidates(info, info_url):
    """Generate only standard requests supported by an Image API description."""
    if not isinstance(info, dict):
        raise ValueError("Image information must be a JSON object")
    contexts = info.get("@context", [])
    contexts = contexts if isinstance(contexts, list) else [contexts]
    contexts = [value for value in contexts if isinstance(value, str)]
    if not any("iiif.io/api/image/" in value for value in contexts):
        raise ValueError("Not an IIIF Image API information document")
    if not all(isinstance(info.get(key), int) and not isinstance(info[key], bool) and info[key] > 0 for key in ("width", "height")):
        raise ValueError("Image information must declare positive pixel dimensions")
    base = str(info.get("id") or info.get("@id") or info_url.removesuffix("/info.json")).rstrip("/")
    if urlsplit(base).scheme not in {"http", "https"}:
        raise ValueError("Image service must have an HTTP URL")
    version3 = any("/image/3/" in value for value in contexts) or info.get("type") == "ImageService3"
    # JPEG is the interoperable delivery format, independent of the source JP2/TIFF.
    sizes = ["max"] if version3 else ["full", "max"]
    advertised = info.get("sizes", [])
    if isinstance(advertised, list) and advertised:
        widths = [row.get("width") for row in advertised if isinstance(row, dict) and isinstance(row.get("width"), int)]
        if widths:
            sizes.append(str(max(widths)) + ",")
    elif not version3:
        sizes.append(str(min(info["width"], info.get("maxWidth", info["width"]))) + ",")
    return [base + f"/full/{size}/0/default.jpg" for size in dict.fromkeys(sizes)]
