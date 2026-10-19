"""Local deterministic HTTP server used by Module 2 network tests."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import ClassVar


class FixtureHandler(BaseHTTPRequestHandler):
    """Serve fixed responses without contacting any external institution."""

    request_counts: ClassVar[dict[str, int]] = {}

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler defines this name
        self.request_counts[self.path] = self.request_counts.get(self.path, 0) + 1
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/json")
            self.end_headers()
            return
        if self.path == "/json":
            self._send(
                200,
                b'{"id":"https://example.test/stream","type":"OrderedCollection"}',
                "application/activity+json; charset=utf-8",
            )
            return
        if self.path == "/mislabelled-json":
            self._send(200, b'{"type":"Collection"}', "text/plain")
            return
        if self.path == "/html":
            self._send(200, b"<html><body>Institution</body></html>", "text/html; charset=utf-8")
            return
        if self.path == "/bad-json":
            self._send(200, b'{"type":', "application/json")
            return
        if self.path == "/large":
            self._send(200, b"x" * 256, "text/plain")
            return
        if self.path == "/restricted":
            self._send(403, b"forbidden", "text/plain")
            return
        if self.path == "/temporary":
            self._send(503, b"retry later", "text/plain")
            return
        self._send(404, b"not found", "text/plain")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class LocalHttpServer:
    """Context manager that starts and reliably shuts down a local server."""

    def __enter__(self) -> "LocalHttpServer":
        FixtureHandler.request_counts = {}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
