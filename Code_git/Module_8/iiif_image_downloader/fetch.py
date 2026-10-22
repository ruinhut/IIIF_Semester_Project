"""Bounded, retrying and byte-validated image download."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from http.client import HTTPException, IncompleteRead
from pathlib import Path
import socket
import ssl
import time
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


class DownloadError(RuntimeError):
    def __init__(
        self,
        url: str,
        error_type: str,
        message: str,
        *,
        status_code: int | None = None,
        attempt_count: int = 1,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.error_type = error_type
        self.status_code = status_code
        self.attempt_count = attempt_count


@dataclass(frozen=True)
class DownloadedImage:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str | None
    detected_format: str
    extension: str
    byte_count: int
    sha256: str
    response_time_ms: int
    attempt_count: int


class ImageFetcher:
    def __init__(
        self,
        *,
        timeout_seconds: float = 30.0,
        retries: int = 2,
        backoff_seconds: float = 1.0,
        max_image_bytes: int = 100 * 1024 * 1024,
        user_agent: str = "iiif-image-downloader/0.1 (academic research)",
        opener: Callable[..., object] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if retries < 0:
            raise ValueError("retries cannot be negative")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative")
        if max_image_bytes < 1:
            raise ValueError("max_image_bytes must be positive")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.max_image_bytes = max_image_bytes
        self.user_agent = user_agent
        self.opener = opener
        self.sleeper = sleeper

    def download(self, url: str, temporary_path: Path) -> DownloadedImage:
        attempts = self.retries + 1
        last_error: DownloadError | None = None
        temporary_path.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(1, attempts + 1):
            temporary_path.unlink(missing_ok=True)
            started = time.perf_counter()
            request = Request(
                url,
                headers={
                    "Accept": "image/*;q=1.0, application/octet-stream;q=0.2",
                    "User-Agent": self.user_agent,
                },
            )
            try:
                with self.opener(request, timeout=self.timeout_seconds) as response:  # type: ignore[attr-defined]
                    digest = sha256()
                    byte_count = 0
                    header = b""
                    with temporary_path.open("wb") as handle:
                        while True:
                            chunk = response.read(64 * 1024)
                            if not chunk:
                                break
                            if len(header) < 32:
                                header = (header + chunk)[:32]
                            byte_count += len(chunk)
                            if byte_count > self.max_image_bytes:
                                raise DownloadError(
                                    url,
                                    "image_too_large",
                                    f"Image exceeded {self.max_image_bytes} bytes",
                                    status_code=int(response.getcode()),
                                    attempt_count=attempt,
                                )
                            digest.update(chunk)
                            handle.write(chunk)
                    content_type = _base_content_type(
                        response.headers.get("Content-Type")
                    )
                    detected = detect_raster_format(header)
                    if detected is None:
                        raise DownloadError(
                            url,
                            "invalid_image_bytes",
                            f"Response is not a supported raster image (Content-Type: {content_type or 'missing'})",
                            status_code=int(response.getcode()),
                            attempt_count=attempt,
                        )
                    if content_type and not (
                        content_type.startswith("image/")
                        or content_type == "application/octet-stream"
                    ):
                        raise DownloadError(
                            url,
                            "non_image_content_type",
                            f"Unexpected Content-Type: {content_type}",
                            status_code=int(response.getcode()),
                            attempt_count=attempt,
                        )
                    elapsed = round((time.perf_counter() - started) * 1000)
                    return DownloadedImage(
                        requested_url=url,
                        final_url=str(response.geturl()),
                        status_code=int(response.getcode()),
                        content_type=content_type,
                        detected_format=detected[0],
                        extension=detected[1],
                        byte_count=byte_count,
                        sha256=digest.hexdigest(),
                        response_time_ms=elapsed,
                        attempt_count=attempt,
                    )
            except HTTPError as exc:
                last_error = DownloadError(
                    url,
                    _http_error_type(exc.code),
                    f"HTTP {exc.code}: {exc.reason}",
                    status_code=int(exc.code),
                    attempt_count=attempt,
                )
                should_retry = (
                    exc.code in RETRYABLE_STATUS_CODES and attempt < attempts
                )
                exc.close()
                if not should_retry:
                    raise last_error from exc
            except DownloadError as exc:
                temporary_path.unlink(missing_ok=True)
                raise exc
            except (
                URLError,
                TimeoutError,
                socket.timeout,
                ssl.SSLError,
                HTTPException,
                IncompleteRead,
                ConnectionError,
                OSError,
            ) as exc:
                temporary_path.unlink(missing_ok=True)
                reason = getattr(exc, "reason", exc)
                error_type = "timeout" if _is_timeout(reason) else "unreachable"
                last_error = DownloadError(
                    url,
                    error_type,
                    str(reason),
                    attempt_count=attempt,
                )
                if attempt >= attempts:
                    raise last_error from exc
            if attempt < attempts and self.backoff_seconds:
                self.sleeper(self.backoff_seconds * (2 ** (attempt - 1)))

        if last_error is not None:
            raise last_error
        raise DownloadError(url, "unreachable", "Request failed without a response")


def detect_raster_format(header: bytes) -> tuple[str, str] | None:
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg", ".jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", ".png"
    if header.startswith((b"II*\x00", b"MM\x00*")):
        return "tiff", ".tif"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "gif", ".gif"
    if header.startswith(b"BM"):
        return "bmp", ".bmp"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp", ".webp"
    if header.startswith(b"\x00\x00\x00\x0cjP  \r\n\x87\n") or header.startswith(b"\xffO\xffQ"):
        return "jpeg2000", ".jp2"
    return None


def _base_content_type(value: str | None) -> str | None:
    return value.split(";", 1)[0].strip().casefold() if value else None


def _http_error_type(status_code: int) -> str:
    if status_code in {401, 403}:
        return "restricted"
    if status_code in {404, 410}:
        return "not_found"
    if status_code in RETRYABLE_STATUS_CODES:
        return "temporary_failure"
    return "http_error"


def _is_timeout(value: object) -> bool:
    return isinstance(value, (TimeoutError, socket.timeout)) or "timed out" in str(value).casefold()
