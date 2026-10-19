"""Bounded HTTP retrieval for IIIF Manifest JSON."""

from __future__ import annotations

from dataclasses import dataclass
from http.client import HTTPException, IncompleteRead
import socket
import ssl
import time
from typing import Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import canonicalize_url


RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    """A classified retrieval failure suitable for pipeline output."""

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
class FetchedResponse:
    requested_url: str
    final_url: str
    status_code: int
    content_type: Optional[str]
    body: bytes
    response_time_ms: int
    attempt_count: int


class HttpFetcher:
    """Fetch public HTTP(S) resources with retry, timeout, and size bounds."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        retries: int = 1,
        backoff_seconds: float = 0.5,
        max_response_bytes: int = 16 * 1024 * 1024,
        user_agent: str = "iiif-manifest-validator/0.1 (+academic research)",
        opener: Callable[..., object] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if retries < 0:
            raise ValueError("retries cannot be negative")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative")
        if max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.max_response_bytes = max_response_bytes
        self.user_agent = user_agent
        self.opener = opener
        self.sleeper = sleeper

    def fetch(self, url: str) -> FetchedResponse:
        requested_url = canonicalize_url(url)
        attempts = self.retries + 1
        last_error: FetchError | None = None

        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            request = Request(
                requested_url,
                headers={
                    "Accept": "application/ld+json, application/json;q=0.9, */*;q=0.1",
                    "User-Agent": self.user_agent,
                },
            )
            try:
                with self.opener(request, timeout=self.timeout_seconds) as response:  # type: ignore[attr-defined]
                    body = response.read(self.max_response_bytes + 1)
                    elapsed = round((time.perf_counter() - started) * 1000)
                    final_url = canonicalize_url(response.geturl())
                    status_code = int(response.getcode())
                    content_type = response.headers.get("Content-Type")
                    if len(body) > self.max_response_bytes:
                        raise FetchError(
                            final_url,
                            "response_too_large",
                            f"Response exceeded {self.max_response_bytes} bytes",
                            status_code=status_code,
                            attempt_count=attempt,
                        )
                    return FetchedResponse(
                        requested_url=requested_url,
                        final_url=final_url,
                        status_code=status_code,
                        content_type=content_type,
                        body=body,
                        response_time_ms=elapsed,
                        attempt_count=attempt,
                    )
            except HTTPError as exc:
                error_type = _http_error_type(exc.code)
                last_error = FetchError(
                    requested_url,
                    error_type,
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
            except FetchError:
                raise
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
                reason = getattr(exc, "reason", exc)
                error_type = "timeout" if _is_timeout(reason) else "unreachable"
                last_error = FetchError(
                    requested_url,
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
        raise FetchError(requested_url, "unreachable", "Request failed without a response")


def _http_error_type(status_code: int) -> str:
    if status_code in {401, 403}:
        return "restricted"
    if status_code in {404, 410}:
        return "not_found"
    if status_code in RETRYABLE_STATUS_CODES:
        return "temporary_failure"
    return "http_error"


def _is_timeout(value: object) -> bool:
    if isinstance(value, (TimeoutError, socket.timeout)):
        return True
    return "timed out" in str(value).casefold()
