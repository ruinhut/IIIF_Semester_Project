"""Orchestration for one-example and all-image download modes."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any

from .fetch import DownloadError, ImageFetcher, detect_raster_format
from .iiif_service import download_image
from .models import DownloadItem, build_download_items
from .reference import ReferenceTextFetcher
from .store import hash_file, read_jsonl, write_json, write_jsonl, write_linked_json


MODES = {"download-example", "download-all"}


def run_download(config_path: Path, *, mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode}")
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    base = config_path.parent
    records_path = _required_path(base, config, "common_records_jsonl")
    media_path = _required_path(base, config, "common_media_jsonl")
    profiles_path = _required_path(base, config, "ocr_document_profiles_jsonl")
    references_path = _optional_path(
        base, config.get("institution_reference_texts_jsonl")
    )
    output_root = _resolve(base, str(config.get("output_directory", "data/output")))
    run_output = output_root / ("example" if mode == "download-example" else "all")
    log_dir = _resolve(base, str(config.get("log_directory", "data/log")))

    records = read_jsonl(records_path)
    media_rows = read_jsonl(media_path)
    profiles = read_jsonl(profiles_path)
    reference_rows = read_jsonl(references_path) if references_path else []
    require_reference_text = bool(config.get("require_reference_text", False))
    items, skipped = build_download_items(
        records, media_rows, profiles, reference_rows,
        require_academic_analysis_allowed=bool(
            config.get("require_academic_analysis_allowed", True)
        ),
        require_reference_text=require_reference_text,
    )
    if not items:
        raise RuntimeError("No eligible image download URLs were found")

    request_config = config.get("request", {})
    if not isinstance(request_config, dict):
        raise ValueError("request must be a JSON object")
    delay = float(request_config.get("request_delay_seconds", 0.25))
    if delay < 0:
        raise ValueError("request_delay_seconds cannot be negative")
    fetcher = ImageFetcher(
        timeout_seconds=float(request_config.get("timeout_seconds", 30.0)),
        retries=int(request_config.get("retries", 2)),
        backoff_seconds=float(request_config.get("backoff_seconds", 1.0)),
        max_image_bytes=int(request_config.get("max_image_bytes", 100 * 1024 * 1024)),
        user_agent=str(request_config.get("user_agent", "iiif-image-downloader/0.1 (academic research)")),
    )
    reference_fetcher = ReferenceTextFetcher(
        timeout_seconds=float(request_config.get("timeout_seconds", 30.0)),
        max_bytes=int(request_config.get("max_reference_text_bytes", 20 * 1024 * 1024)),
        user_agent=str(request_config.get("user_agent", "iiif-image-downloader/0.1 (academic research)")),
    )
    overwrite = bool(config.get("overwrite_existing", False))
    started = datetime.now().astimezone()
    successes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    network_requests = 0
    downloaded_reference_texts = 0
    reference_text_failures: list[dict[str, Any]] = []

    for item in items:
        relative_directory = item.relative_directory()
        exported_references: list[dict[str, Any]] = []
        if item.reference_texts:
            probe_root = run_output / "_reference_probe"
            probe_directory = probe_root / relative_directory
            probe_directory.mkdir(parents=True, exist_ok=True)
            exported_references, reference_failures = _download_reference_texts(
                item,
                probe_directory,
                reference_fetcher,
            )
            reference_text_failures.extend(reference_failures)
            if not exported_references and require_reference_text:
                failures.append({
                    "resource_id": item.resource_id,
                    "record_id": item.record_id,
                    "sequence": item.sequence,
                    "download_url": item.download_url,
                    "stage": "reference_text",
                    "error_type": "reference_text_required",
                    "message": "No linked institutional reference text could be retrieved",
                    "status_code": None,
                    "attempt_count": 1,
                })
                _remove_empty_parents(probe_directory, probe_root)
                continue
            category = (
                "with_reference" if exported_references else "reference_failed"
            )
        else:
            probe_root = None
            probe_directory = None
            category = "without_reference"

        directory = run_output / category / relative_directory
        directory.mkdir(parents=True, exist_ok=True)
        if probe_directory is not None:
            _move_reference_files(probe_directory, directory)
            _remove_empty_parents(probe_directory, probe_root)
        existing = _existing_image(directory) if not overwrite else None
        success_row: dict[str, Any] | None = None
        if existing is not None:
            # Cached and fresh rows share the configured root, including the mode.
            success_row = _cached_result(item, existing, output_root)
        else:
            if network_requests and delay:
                time.sleep(delay)
            temporary = directory / "image.part"
            network_requests += 1
            try:
                result, resolution = download_image(item, fetcher, temporary)
                image_path = directory / f"image{result.extension}"
                _remove_old_images(directory, except_path=temporary)
                temporary.replace(image_path)
                success_row = {
                    "resource_id": item.resource_id,
                    "record_id": item.record_id,
                    "sequence": item.sequence,
                    "requested_url": result.requested_url,
                    "final_url": result.final_url,
                    "status_code": result.status_code,
                    "content_type": result.content_type,
                    "detected_format": result.detected_format,
                    "bytes": result.byte_count,
                    "sha256": result.sha256,
                    "response_time_ms": result.response_time_ms,
                    "attempt_count": result.attempt_count,
                    "download_status": "downloaded",
                    "image_path": image_path.relative_to(output_root).as_posix(),
                    "bundle_directory": directory.relative_to(output_root).as_posix(),
                    "image_resolution": resolution,
                }
            except DownloadError as exc:
                temporary.unlink(missing_ok=True)
                _remove_reference_files(directory)
                if directory.is_dir() and not any(directory.iterdir()):
                    directory.rmdir()
                failures.append({
                    "resource_id": item.resource_id,
                    "record_id": item.record_id,
                    "sequence": item.sequence,
                    "download_url": item.download_url,
                    "stage": "image",
                    "error_type": exc.error_type,
                    "message": str(exc),
                    "status_code": exc.status_code,
                    "attempt_count": exc.attempt_count,
                    "image_resolution": getattr(exc, "resolution_trace", None),
                })

        if success_row is None:
            continue
        linked_media = dict(item.media)
        linked_image = dict(linked_media.get("image", {}))
        if success_row.get("final_url"):
            linked_image.setdefault("source_id", item.download_url)
            linked_image.update(id=success_row["final_url"], download_url=success_row["final_url"])
            mime_types = {"jpeg": "image/jpeg", "png": "image/png", "jpeg2000": "image/jp2",
                          "tiff": "image/tiff", "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp"}
            if success_row.get("detected_format") in mime_types:
                linked_image["format"] = mime_types[success_row["detected_format"]]
        linked_media["image"] = linked_image
        write_linked_json(
            directory,
            record=item.record,
            media=linked_media,
            profile=item.ocr_profile,
            reference_texts=exported_references,
        )
        downloaded_reference_texts += len(exported_references)
        success_row["reference_texts"] = len(exported_references)
        success_row["output_category"] = category
        successes.append(success_row)

        if mode == "download-example" and successes:
            break

    finished = datetime.now().astimezone()
    status = "completed" if not failures else "completed_with_failures"
    if not failures and reference_text_failures:
        status = "completed_with_reference_failures"
    if not successes:
        status = "failed"
    summary: dict[str, Any] = {
        "module": 8,
        "name": "Linked Image Downloader",
        "schema_version": "module-8-download-0.2",
        "mode": mode,
        "status": status,
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "inputs": {
            "common_records": len(records),
            "common_media": len(media_rows),
            "ocr_document_profiles": len(profiles),
            "institution_reference_texts": len(reference_rows),
        },
        "eligible_images": len(items),
        "attempted_images": len(successes) + sum(
            row.get("stage", "image") == "image" for row in failures
        ),
        "downloaded_images": sum(
            row["download_status"] == "downloaded" for row in successes
        ),
        "cached_images": sum(
            row["download_status"] == "cached" for row in successes
        ),
        "failed_images": sum(
            row.get("stage", "image") == "image" for row in failures
        ),
        "failed_bundles": len(failures),
        "skipped_images": len(skipped),
        "downloaded_bytes": sum(int(row["bytes"]) for row in successes),
        "downloaded_reference_texts": downloaded_reference_texts,
        "reference_text_failures": len(reference_text_failures),
        "output_directory": str(run_output),
    }
    output_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(run_output / "download_index.jsonl", successes)
    write_jsonl(run_output / "failed_downloads.jsonl", failures)
    write_jsonl(run_output / "skipped_downloads.jsonl", skipped)
    write_jsonl(
        run_output / "reference_text_failures.jsonl", reference_text_failures
    )
    write_json(run_output / "download_summary.json", summary)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"Module8_{started.strftime('%Y-%m-%d_%H-%M-%S')}_log.txt"
    _write_log(log_path, summary, failures, skipped)
    summary["log_file"] = str(log_path)
    write_json(run_output / "download_summary.json", summary)
    if not successes:
        raise RuntimeError(f"No image could be downloaded; see {log_path}")
    return summary


def _existing_image(directory: Path) -> Path | None:
    for path in sorted(directory.glob("image.*")):
        if path.suffix != ".part" and path.is_file() and path.stat().st_size > 0:
            with path.open("rb") as handle:
                if detect_raster_format(handle.read(32)) is not None:
                    return path
    return None


def _cached_result(item: DownloadItem, path: Path, output_root: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        detected = detect_raster_format(handle.read(32))
    cached_url = item.download_url
    linked_path = path.parent / "common_media.json"
    if linked_path.exists():
        try:
            cached_image = json.loads(linked_path.read_text(encoding="utf-8")).get("image", {})
            cached_url = str(cached_image.get("download_url") or cached_url)
        except (ValueError, OSError, AttributeError):
            pass
    return {
        "resource_id": item.resource_id,
        "record_id": item.record_id,
        "sequence": item.sequence,
        "requested_url": cached_url,
        "final_url": cached_url,
        "status_code": None,
        "content_type": None,
        "detected_format": detected[0] if detected else None,
        "bytes": path.stat().st_size,
        "sha256": hash_file(path),
        "response_time_ms": 0,
        "attempt_count": 0,
        "download_status": "cached",
        "image_path": path.relative_to(output_root).as_posix(),
        "bundle_directory": path.parent.relative_to(output_root).as_posix(),
    }


def _remove_old_images(directory: Path, *, except_path: Path) -> None:
    for path in directory.glob("image.*"):
        if path != except_path and path.is_file():
            path.unlink()


def _required_path(base: Path, config: dict[str, Any], key: str) -> Path:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Configuration requires {key}")
    path = _resolve(base, value)
    if not path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    return path


def _optional_path(base: Path, value: Any) -> Path | None:
    if value is None or not str(value).strip():
        return None
    path = _resolve(base, str(value))
    if not path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    return path


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _write_log(
    path: Path,
    summary: dict[str, Any],
    failures: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
) -> None:
    lines = [
        "Module 8 - Linked Image Downloader",
        f"Mode: {summary['mode']}",
        f"Status: {summary['status']}",
        f"Started: {summary['started_at']}",
        f"Finished: {summary['finished_at']}",
        f"Eligible images: {summary['eligible_images']}",
        f"Attempted images: {summary['attempted_images']}",
        f"Downloaded images: {summary['downloaded_images']}",
        f"Cached images: {summary['cached_images']}",
        f"Failed images: {summary['failed_images']}",
        f"Failed bundles: {summary['failed_bundles']}",
        f"Skipped images: {summary['skipped_images']}",
        f"Downloaded bytes: {summary['downloaded_bytes']}",
        f"Downloaded institutional reference texts: {summary['downloaded_reference_texts']}",
        f"Reference text failures: {summary['reference_text_failures']}",
        f"Output directory: {summary['output_directory']}",
        "",
    ]
    if failures:
        lines.extend(["Failures:", *[
            f"- {row['resource_id']}: {row['error_type']} - {row['message']}"
            for row in failures
        ], ""])
    if skipped:
        lines.extend(["Skipped:", *[
            f"- {row['resource_id']}: {row['reason']}" for row in skipped
        ], ""])
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _download_reference_texts(
    item: DownloadItem,
    directory: Path,
    fetcher: ReferenceTextFetcher,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _remove_reference_files(directory)
    exported: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for index, row in enumerate(item.reference_texts, 1):
        reference = row.get("reference_text", {})
        if not isinstance(reference, dict):
            continue
        source_url = str(reference.get("id") or "").strip()
        inline_text = str(reference.get("inline_text") or "").strip()
        stem = f"institution_reference_{index:03d}"
        try:
            if inline_text:
                source_path = directory / f"{stem}.txt"
                source_path.write_text(inline_text + "\n", encoding="utf-8")
                result = {
                    **dict(row),
                    "download": {
                        "status": "inline_text_saved",
                        "source_file": source_path.name,
                        "plain_text_file": source_path.name,
                        "bytes": source_path.stat().st_size,
                        "sha256": hash_file(source_path),
                    },
                }
            elif source_url.startswith(("http://", "https://")):
                temporary = directory / f"{stem}.part"
                downloaded = fetcher.download(
                    source_url,
                    temporary,
                    declared_format=reference.get("format"),
                )
                source_path = directory / f"{stem}{downloaded.extension}"
                temporary.replace(source_path)
                plain_path = source_path
                if downloaded.extension != ".txt":
                    plain_path = directory / f"{stem}.txt"
                    plain_path.write_text(
                        downloaded.plain_text + "\n", encoding="utf-8"
                    )
                result = {
                    **dict(row),
                    "download": {
                        "status": "downloaded",
                        "requested_url": downloaded.requested_url,
                        "final_url": downloaded.final_url,
                        "status_code": downloaded.status_code,
                        "content_type": downloaded.content_type,
                        "source_file": source_path.name,
                        "plain_text_file": plain_path.name,
                        "bytes": downloaded.byte_count,
                        "sha256": downloaded.sha256,
                        "response_time_ms": downloaded.response_time_ms,
                    },
                }
            else:
                raise DownloadError(
                    source_url,
                    "missing_reference_text_url",
                    "Reference text has neither inline text nor an HTTP URL",
                )
            exported.append(result)
        except DownloadError as exc:
            failures.append({
                "reference_text_id": row.get("reference_text_id"),
                "resource_id": item.resource_id,
                "record_id": item.record_id,
                "source_url": source_url or None,
                "error_type": exc.error_type,
                "message": str(exc),
                "status_code": exc.status_code,
            })
    return exported, failures


def _remove_reference_files(directory: Path) -> None:
    for path in directory.glob("institution_reference_*"):
        if path.is_file():
            path.unlink()
    linked_json = directory / "institution_reference_texts.json"
    linked_json.unlink(missing_ok=True)


def _move_reference_files(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    _remove_reference_files(target)
    for path in source.glob("institution_reference_*"):
        if path.is_file():
            path.replace(target / path.name)


def _remove_empty_parents(directory: Path, stop: Path | None) -> None:
    current = directory
    while stop is not None and current.is_relative_to(stop):
        try:
            current.rmdir()
        except OSError:
            break
        if current == stop:
            break
        current = current.parent
