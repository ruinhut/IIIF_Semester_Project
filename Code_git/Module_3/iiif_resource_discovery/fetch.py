"""Bounded HTTP retrieval for JSON resources and HTML discovery pages."""

from __future__ import annotations

from dataclasses import dataclass
from http.client import HTTPException, IncompleteRead
import json
import socket
import ssl
import time
from typing import Any, Callable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import canonicalize_url


RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    """Describe one bounded retrieval or decoding failure."""

    def __init__(self, url: str, error_type: str, message: str, status_code: int | None = None):
        super().__init__(message)
        self.url = url
        self.error_type = error_type
        self.status_code = status_code


@dataclass(frozen=True)
class FetchedDocument:
    """A bounded HTTP response retained in memory for immediate processing."""

    requested_url: str
    final_url: str
    status_code: int
    content_type: Optional[str]
    body: bytes

    def text(self) -> str:
        """Decode the response using its declared charset or UTF-8."""

        charset = "utf-8"
        if self.content_type:
            for part in self.content_type.split(";")[1:]:
                name, separator, value = part.strip().partition("=")
                if separator and name.casefold() == "charset":
                    charset = value.strip().strip('"') or "utf-8"
        try:
            return self.body.decode(charset)
        except (LookupError, UnicodeDecodeError) as exc:
            raise FetchError(self.final_url, "decode_error", str(exc), self.status_code) from exc

    def json(self) -> Any:
        """Decode JSON, accepting a UTF-8 BOM when present."""

        try:
            return json.loads(self.text().lstrip("\ufeff"))
        except json.JSONDecodeError as exc:
            message = f"{exc.msg} at line {exc.lineno}, column {exc.colno}"
            raise FetchError(self.final_url, "json_decode_error", message, self.status_code) from exc


class HttpFetcher:
    """Retrieve public HTTP(S) resources with time, retry, and size bounds."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        retries: int = 1,
        backoff_seconds: float = 0.5,
        max_response_bytes: int = 4 * 1024 * 1024,
        user_agent: str = "iiif-resource-discovery/0.1 (+academic research)",
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if retries < 0 or backoff_seconds < 0:
            raise ValueError("retries and backoff_seconds must be non-negative")
        if max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive")
        if not user_agent.strip():
            raise ValueError("user_agent must not be empty")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.max_response_bytes = max_response_bytes
        self.user_agent = user_agent.strip()
        self.sleeper = sleeper

    def fetch(
        self, url: str, *,
        accept: str = "application/ld+json, application/json, text/html;q=0.5",
        method: str = "GET", json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> FetchedDocument:
        """Fetch one URL and raise a structured error after bounded retries."""

        canonicalize_url(url)
        method = method.upper()
        if method not in {"GET", "POST"}:
            raise ValueError("Discovery retrieval supports GET and read-only POST search only")
        if method == "GET" and json_body is not None:
            raise ValueError("GET retrieval cannot carry a JSON request body")
        last_error: FetchError | None = None
        for attempt in range(self.retries + 1):
            try:
                return self._fetch_once(url, accept=accept, method=method, json_body=json_body, headers=headers)
            except FetchError as exc:
                last_error = exc
                retryable = exc.status_code in RETRYABLE_STATUS_CODES or exc.error_type in {
                    "timeout",
                    "network_error",
                    "incomplete_response",
                }
                if not retryable or attempt >= self.retries:
                    break
                self.sleeper(self.backoff_seconds * (2**attempt))
        assert last_error is not None
        raise last_error

    def _fetch_once(
        self, url: str, *, accept: str, method: str = "GET",
        json_body: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None,
    ) -> FetchedDocument:
        request_headers = {"Accept": accept, "User-Agent": self.user_agent, **dict(headers or {})}
        body = None
        if json_body is not None:
            body = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        request = Request(
            url,
            headers=request_headers, data=body, method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                try:
                    body = response.read(self.max_response_bytes + 1)
                except IncompleteRead as exc:
                    raise FetchError(
                        response.geturl(),
                        "incomplete_response",
                        f"Server closed the response early after {len(exc.partial)} bytes",
                        int(response.status),
                    ) from exc
                if len(body) > self.max_response_bytes:
                    raise FetchError(
                        response.geturl(),
                        "response_too_large",
                        f"Response exceeded {self.max_response_bytes} bytes",
                        int(response.status),
                    )
                return FetchedDocument(
                    requested_url=url,
                    final_url=response.geturl(),
                    status_code=int(response.status),
                    content_type=response.headers.get("Content-Type"),
                    body=body,
                )
        except HTTPError as exc:
            try:
                raise FetchError(
                    exc.geturl() or url,
                    f"http_{exc.code}",
                    f"HTTP {exc.code}",
                    int(exc.code),
                ) from exc
            finally:
                exc.close()
        except (TimeoutError, socket.timeout) as exc:
            raise FetchError(url, "timeout", str(exc) or "request timed out") from exc
        except ssl.SSLError as exc:
            raise FetchError(url, "tls_error", str(exc)) from exc
        except URLError as exc:
            reason = exc.reason
            error_type = "timeout" if isinstance(reason, (TimeoutError, socket.timeout)) else "network_error"
            raise FetchError(url, error_type, str(reason)) from exc
        except OSError as exc:
            raise FetchError(url, "network_error", str(exc)) from exc
        except HTTPException as exc:
            raise FetchError(url, "network_error", str(exc) or exc.__class__.__name__) from exc


def normalized_media_type(content_type: Optional[str]) -> Optional[str]:
    """Return the lower-case media type without charset parameters."""

    if not content_type:
        return None
    value = content_type.split(";", 1)[0].strip().lower()
    return value or None


def is_json_document(document: FetchedDocument) -> bool:
    """Recognize declared JSON and JSON bodies served with the wrong type."""

    media_type = normalized_media_type(document.content_type)
    if media_type and (media_type == "application/json" or media_type.endswith("+json")):
        return True
    stripped = document.body.lstrip(b"\xef\xbb\xbf \t\r\n")
    return stripped.startswith((b"{", b"["))
