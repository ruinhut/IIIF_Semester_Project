"""Download and decode institution-provided OCR/transcription resources."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .fetch import DownloadError, _base_content_type


@dataclass(frozen=True)
class DownloadedReferenceText:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str | None
    byte_count: int
    sha256: str
    response_time_ms: int
    extension: str
    plain_text: str


class ReferenceTextFetcher:
    def __init__(
        self,
        *,
        timeout_seconds: float = 30.0,
        max_bytes: int = 20 * 1024 * 1024,
        user_agent: str = "iiif-image-downloader/0.1 (academic research)",
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes
        self.user_agent = user_agent

    def download(
        self, url: str, temporary_path: Path, *, declared_format: str | None
    ) -> DownloadedReferenceText:
        started = time.perf_counter()
        request = Request(
            url,
            headers={
                "Accept": "text/html, text/plain, application/xml, text/xml, application/json;q=0.8, */*;q=0.1",
                "User-Agent": self.user_agent,
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read(self.max_bytes + 1)
                if not payload:
                    raise DownloadError(url, "empty_reference_text", "Reference text is empty")
                if len(payload) > self.max_bytes:
                    raise DownloadError(
                        url,
                        "reference_text_too_large",
                        f"Reference text exceeded {self.max_bytes} bytes",
                        status_code=int(response.getcode()),
                    )
                content_type = _base_content_type(response.headers.get("Content-Type"))
                if content_type and not _is_text_content_type(content_type):
                    raise DownloadError(
                        url,
                        "non_text_content_type",
                        f"Unexpected reference-text Content-Type: {content_type}",
                        status_code=int(response.getcode()),
                    )
                extension = _extension(declared_format or content_type, url)
                temporary_path.parent.mkdir(parents=True, exist_ok=True)
                temporary_path.write_bytes(payload)
                plain_text = _to_plain_text(payload, declared_format or content_type)
                if not plain_text.strip():
                    raise DownloadError(
                        url,
                        "empty_decoded_reference_text",
                        "Reference resource contains no decodable text",
                        status_code=int(response.getcode()),
                    )
                return DownloadedReferenceText(
                    requested_url=url,
                    final_url=str(response.geturl()),
                    status_code=int(response.getcode()),
                    content_type=content_type,
                    byte_count=len(payload),
                    sha256=sha256(payload).hexdigest(),
                    response_time_ms=round((time.perf_counter() - started) * 1000),
                    extension=extension,
                    plain_text=plain_text,
                )
        except DownloadError:
            temporary_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            temporary_path.unlink(missing_ok=True)
            raise DownloadError(url, "reference_text_unreachable", str(exc)) from exc


def _is_text_content_type(value: str) -> bool:
    return value.startswith("text/") or value.endswith("+xml") or value in {
        "application/xml",
        "application/xhtml+xml",
        "application/json",
        "application/octet-stream",
    }


def _extension(media_type: str | None, url: str) -> str:
    value = str(media_type or "").casefold()
    if "hocr" in value:
        return ".hocr.html"
    if "html" in value:
        return ".html"
    if "xml" in value or "alto" in value:
        return ".xml"
    if "json" in value:
        return ".json"
    suffix = Path(urlparse(url).path).suffix
    return suffix if suffix in {".txt", ".html", ".xml", ".json"} else ".txt"


def _to_plain_text(payload: bytes, media_type: str | None) -> str:
    text = payload.decode("utf-8-sig", errors="replace")
    value = str(media_type or "").casefold()
    if "html" in value or "hocr" in value or "<html" in text[:500].casefold():
        parser = _VisibleTextParser()
        parser.feed(text)
        return " ".join(parser.parts)
    if "xml" in value or "alto" in value:
        root = ET.fromstring(payload)
        if root.tag.rsplit("}", 1)[-1].casefold() == "alto":
            # ALTO's Description contains filenames, models and processing
            # parameters. Only layout String/CONTENT values are page OCR.
            # ElementTree handles namespaces and XML entities without losing
            # apostrophes, quotes, or ampersands inside recognized words.
            lines = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "TextLine"]
            if not lines:
                lines = [root]
            return "\n".join(
                " ".join(node.get("CONTENT", "").strip() for node in line.iter()
                         if node.tag.rsplit("}", 1)[-1] == "String" and node.get("CONTENT", "").strip())
                for line in lines
            ).strip()
        text = re.sub(r"<String[^>]+CONTENT=[\"']([^\"']+)[\"'][^>]*/?>", r" \1 ", text, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden: list[str] = []

    def handle_starttag(self, tag, attrs) -> None:
        # Empty hOCR pages often contain only a filename in <head><title>.
        # That filename, CSS and JavaScript are not recognized page text.
        if tag in {"head", "title", "script", "style"}:
            self.hidden.append(tag)

    def handle_endtag(self, tag) -> None:
        if tag in self.hidden:
            index = len(self.hidden) - 1 - self.hidden[::-1].index(tag)
            del self.hidden[index:]

    def handle_data(self, data: str) -> None:
        if self.hidden:
            return
        value = re.sub(r"\s+", " ", data).strip()
        if value:
            self.parts.append(value)
