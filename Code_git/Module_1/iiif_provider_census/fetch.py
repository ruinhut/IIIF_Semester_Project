"""Load JSON from local files or HTTP(S) URLs.

All network access for Module 1 is isolated in this file. Keeping it separate
makes the Registry parser easier to test with local fixtures and ensures that
timeouts and retries are applied consistently.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class FetchError(RuntimeError):
    """Raised when a JSON source cannot be retrieved or parsed."""


class JsonFetcher:
    """Retrieve and decode JSON while applying bounded network behavior."""

    def __init__(self, timeout_seconds: float = 20.0, retries: int = 2) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if retries < 0:
            raise ValueError("retries must be non-negative")
        self.timeout_seconds = timeout_seconds
        self.retries = retries

    def load(self, reference: str) -> Any:
        """Return decoded JSON from an HTTP(S), file URI, or filesystem path."""

        parsed = urlparse(reference)
        if parsed.scheme in {"http", "https"}:
            return self._load_http(reference)
        # Local fixtures and manual lists follow the same decoding path as
        # downloaded documents, including support for a UTF-8 BOM.
        if parsed.scheme == "file":
            path = Path(parsed.path)
        else:
            path = Path(reference)
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise FetchError(f"Could not read JSON from {path}: {exc}") from exc

    def _load_http(self, url: str) -> Any:
        """Perform an HTTP GET and retry only a finite number of times."""

        request = Request(
            url,
            headers={
                "Accept": "application/ld+json, application/json;q=0.9",
                "User-Agent": "iiif-provider-census/0.1 (+academic research)",
            },
        )
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    charset = response.headers.get_content_charset() or "utf-8"
                    return json.loads(response.read().decode(charset))
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self.retries:
                    # A short exponential delay avoids immediately repeating a
                    # request against a temporarily unavailable server.
                    time.sleep(0.25 * (2**attempt))
        raise FetchError(f"Could not retrieve JSON from {url}: {last_error}")
