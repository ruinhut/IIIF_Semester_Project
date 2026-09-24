"""Bounded HTTP checks for candidate IIIF entry points.

The checker observes network and response properties only. It does not walk
Activity Stream pagination, discover Manifest URLs, or validate Manifest
structure; those responsibilities belong to later pipeline modules.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import socket
import ssl
import time
from typing import Any, Callable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .models import EndpointCheck, RedirectHop, validate_http_url


RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}
RESTRICTED_STATUS_CODES = {401, 403}
JSON_MEDIA_TYPES = {"application/json", "application/ld+json", "application/activity+json"}


@dataclass(frozen=True)
class _HttpResponse:
    status_code: int
    final_url: str
    headers: Mapping[str, str]
    body: bytes
    body_truncated: bool
    redirect_chain: tuple[RedirectHop, ...]


class _TrackingRedirectHandler(HTTPRedirectHandler):
    """Follow redirects with urllib while retaining an auditable chain."""

    def __init__(self, max_redirects: int) -> None:
        super().__init__()
        self.max_redirections = max_redirects
        self.max_repeats = max_redirects
        self.hops: list[RedirectHop] = []

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> Optional[Request]:
        self.hops.append(RedirectHop(req.full_url, int(code), newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class EndpointChecker:
    """Check accessibility and basic response properties with bounded retries."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
        retries: int = 1,
        backoff_seconds: float = 0.5,
        max_redirects: int = 10,
        max_response_bytes: int = 2 * 1024 * 1024,
        user_agent: str = "iiif-entry-validator/0.1 (+academic research)",
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if retries < 0:
            raise ValueError("retries must be non-negative")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds must be non-negative")
        if max_redirects < 1:
            raise ValueError("max_redirects must be positive")
        if max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive")
        if not user_agent.strip():
            raise ValueError("user_agent must not be empty")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.max_redirects = max_redirects
        self.max_response_bytes = max_response_bytes
        self.user_agent = user_agent.strip()
        self.sleeper = sleeper

    def check(self, url: str, *, checked_at: str) -> EndpointCheck:
        """Return one classified check without raising for expected HTTP failures."""

        requested_url = validate_http_url(url)
        started = time.monotonic()
        attempt_count = 0
        last_response: _HttpResponse | None = None
        last_exception: Exception | None = None

        for attempt in range(self.retries + 1):
            attempt_count = attempt + 1
            try:
                response = self._request_once(requested_url)
                last_response = response
                last_exception = None
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    break
            except (URLError, TimeoutError, socket.timeout, ssl.SSLError, ValueError) as exc:
                last_exception = exc
                last_response = None
                if not _is_retryable_exception(exc):
                    break

            if attempt < self.retries:
                self.sleeper(self.backoff_seconds * (2**attempt))

        elapsed_ms = max(0, round((time.monotonic() - started) * 1000))
        if last_response is not None:
            return self._classify_response(
                requested_url=requested_url,
                checked_at=checked_at,
                response=last_response,
                response_time_ms=elapsed_ms,
                attempt_count=attempt_count,
            )
        assert last_exception is not None
        return self._classify_exception(
            requested_url=requested_url,
            checked_at=checked_at,
            exception=last_exception,
            response_time_ms=elapsed_ms,
            attempt_count=attempt_count,
        )

    def _request_once(self, url: str) -> _HttpResponse:
        """Perform one GET, including redirects, and read only a bounded body."""

        redirect_handler = _TrackingRedirectHandler(self.max_redirects)
        opener = build_opener(redirect_handler)
        request = Request(
            url,
            headers={
                "Accept": (
                    "application/activity+json, application/ld+json, "
                    "application/json;q=0.9, text/html;q=0.5, */*;q=0.1"
                ),
                "User-Agent": self.user_agent,
            },
            method="GET",
        )
        try:
            with opener.open(request, timeout=self.timeout_seconds) as response:
                body, truncated = _read_bounded(response, self.max_response_bytes)
                return _HttpResponse(
                    status_code=int(response.status),
                    final_url=response.geturl(),
                    headers=dict(response.headers.items()),
                    body=body,
                    body_truncated=truncated,
                    redirect_chain=tuple(redirect_handler.hops),
                )
        except HTTPError as exc:
            try:
                body, truncated = _read_bounded(exc, self.max_response_bytes)
                return _HttpResponse(
                    status_code=int(exc.code),
                    final_url=exc.geturl() or url,
                    headers=dict(exc.headers.items()) if exc.headers else {},
                    body=body,
                    body_truncated=truncated,
                    redirect_chain=tuple(redirect_handler.hops),
                )
            finally:
                exc.close()

    def _classify_response(
        self,
        *,
        requested_url: str,
        checked_at: str,
        response: _HttpResponse,
        response_time_ms: int,
        attempt_count: int,
    ) -> EndpointCheck:
        status = response.status_code
        content_type = _media_type(_header(response.headers, "Content-Type"))
        common = {
            "requested_url": requested_url,
            "final_url": response.final_url,
            "checked_at": checked_at,
            "status_code": status,
            "redirect_chain": response.redirect_chain,
            "content_type": content_type,
            "response_time_ms": response_time_ms,
            "response_bytes": len(response.body),
            "body_truncated": response.body_truncated,
            "attempt_count": attempt_count,
        }

        if status in RESTRICTED_STATUS_CODES:
            return EndpointCheck(
                **common,
                check_result="restricted",
                error_type=f"http_{status}",
                error_message=f"HTTP {status} prevents public access",
            )
        if status in RETRYABLE_STATUS_CODES:
            return EndpointCheck(
                **common,
                check_result="temporary_failure",
                error_type=f"http_{status}",
                error_message=f"HTTP {status} remained after bounded retries",
            )
        if not 200 <= status < 300:
            return EndpointCheck(
                **common,
                check_result="unreachable",
                error_type=f"http_{status}",
                error_message=f"HTTP {status} did not return a successful response",
            )
        if response.body_truncated:
            return EndpointCheck(
                **common,
                check_result="response_too_large",
                error_type="response_too_large",
                error_message=(
                    f"Response exceeded the configured {self.max_response_bytes}-byte limit"
                ),
            )

        charset = _charset(_header(response.headers, "Content-Type"))
        try:
            text = response.body.decode(charset)
        except (LookupError, UnicodeDecodeError) as exc:
            return EndpointCheck(
                **common,
                check_result="reachable_non_json",
                error_type="response_decode_error",
                error_message=_short_error(exc),
            )

        looks_json = _is_json_media_type(content_type) or _looks_like_json(text)
        if not looks_json:
            return EndpointCheck(**common, check_result="reachable_non_json")

        try:
            decoded = json.loads(text.lstrip("\ufeff"))
        except json.JSONDecodeError as exc:
            return EndpointCheck(
                **common,
                check_result="invalid_json",
                json_parseable=False,
                error_type="json_decode_error",
                error_message=f"{exc.msg} at line {exc.lineno}, column {exc.colno}",
            )
        return EndpointCheck(
            **common,
            check_result="reachable_json",
            json_parseable=True,
            json_resource_type=_json_resource_type(decoded),
        )

    def _classify_exception(
        self,
        *,
        requested_url: str,
        checked_at: str,
        exception: Exception,
        response_time_ms: int,
        attempt_count: int,
    ) -> EndpointCheck:
        is_timeout = _is_timeout(exception)
        return EndpointCheck(
            requested_url=requested_url,
            final_url=None,
            checked_at=checked_at,
            check_result="temporary_failure" if is_timeout else "unreachable",
            response_time_ms=response_time_ms,
            attempt_count=attempt_count,
            error_type="timeout" if is_timeout else _exception_type(exception),
            error_message=_short_error(exception),
        )


def _read_bounded(stream: Any, limit: int) -> tuple[bytes, bool]:
    data = stream.read(limit + 1)
    return data[:limit], len(data) > limit


def _header(headers: Mapping[str, str], name: str) -> Optional[str]:
    target = name.casefold()
    for key, value in headers.items():
        if key.casefold() == target:
            return value
    return None


def _media_type(content_type_header: Optional[str]) -> Optional[str]:
    if not content_type_header:
        return None
    media_type = content_type_header.split(";", 1)[0].strip().lower()
    return media_type or None


def _charset(content_type_header: Optional[str]) -> str:
    if content_type_header:
        for part in content_type_header.split(";")[1:]:
            name, separator, value = part.strip().partition("=")
            if separator and name.casefold() == "charset":
                return value.strip().strip('"') or "utf-8"
    return "utf-8"


def _is_json_media_type(media_type: Optional[str]) -> bool:
    return bool(media_type and (media_type in JSON_MEDIA_TYPES or media_type.endswith("+json")))


def _looks_like_json(text: str) -> bool:
    stripped = text.lstrip("\ufeff \t\r\n")
    return stripped.startswith("{") or stripped.startswith("[")


def _json_resource_type(value: Any) -> Optional[str]:
    if not isinstance(value, Mapping):
        return None
    resource_type = value.get("type", value.get("@type"))
    if isinstance(resource_type, str):
        return resource_type
    if isinstance(resource_type, list):
        return ", ".join(str(item) for item in resource_type) or None
    return None


def _is_timeout(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    if isinstance(exc, URLError):
        return isinstance(exc.reason, (TimeoutError, socket.timeout))
    return False


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, ValueError):
        return False
    return True


def _exception_type(exc: Exception) -> str:
    if isinstance(exc, ssl.SSLError):
        return "tls_error"
    if isinstance(exc, URLError):
        reason = exc.reason
        if isinstance(reason, socket.gaierror):
            return "dns_error"
        if isinstance(reason, ConnectionRefusedError):
            return "connection_refused"
        return "network_error"
    if isinstance(exc, ValueError):
        return "invalid_url"
    return exc.__class__.__name__.lower()


def _short_error(exc: Exception) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    return text[:500]
