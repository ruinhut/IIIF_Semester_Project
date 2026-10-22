"""Deterministic local IIIF and HTML site for Module 3 tests."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread
from typing import Any, ClassVar
from urllib.parse import parse_qs, urlsplit


class FixtureHandler(BaseHTTPRequestHandler):
    request_counts: ClassVar[dict[str, int]] = {}
    base_url: ClassVar[str] = ""

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        """Model a read-only catalogue that requires JSON-body offsets."""
        parts = urlsplit(self.path)
        if parts.path != "/catalogue-search":
            self._send(404, b"not found", "text/plain")
            return
        if self.headers.get("X-Catalogue-Site") != "public":
            self._send(403, b"missing catalogue scope", "text/plain")
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        offset = body.get("offset", 0)
        self.request_counts[f"POST:{offset}"] = self.request_counts.get(f"POST:{offset}", 0) + 1
        values = [{"id": 11}, {"id": 13}][offset:offset + 1]
        self._json({"hits": values, "total": 2})

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        parts = urlsplit(self.path)
        path = parts.path
        query = parse_qs(parts.query)
        self.request_counts[path] = self.request_counts.get(path, 0) + 1
        if path == "/api-items":
            page = int(query.get("page", ["1"])[0])
            values = {
                1: [
                    {"o:id": 11, "o:media": [{"o:id": 101}]},
                    {"o:id": 12, "o:media": []},
                ],
                2: [{"o:id": 13, "o:media": [{"o:id": 102}]}],
            }.get(page, [])
            self._json(values, "application/ld+json")
            return
        if path == "/api-artworks":
            self._json(
                {
                    "data": [
                        {"id": 21, "is_public_domain": True},
                        {"id": 22, "is_public_domain": False},
                    ]
                },
                "application/json",
            )
            return
        if path == "/omeka/api/items":
            page = int(query.get("page", ["1"])[0])
            values = (
                [{"o:id": 31, "o:media": [{"o:id": 301}]}]
                if page == 1
                else []
            )
            self._json(values, "application/ld+json")
            return
        if path == "/omeka/s/demo/page/home":
            self._html(
                """<!doctype html><html><head>
                <script src="/omeka/application/asset/js/omeka.js"></script>
                </head><body>Omeka S test site</body></html>"""
            )
            return
        if path.startswith("/omeka/iiif/3/") and path.endswith("/manifest"):
            identifier = path.split("/")[4]
            self._json(
                {
                    "@context": "http://iiif.io/api/presentation/3/context.json",
                    "id": f"{self.base_url}{path}",
                    "type": "Manifest",
                    "label": {"en": [f"Omeka item {identifier}"]},
                    "items": [],
                }
            )
            return
        if path == "/stream":
            self._json(
                {
                    "id": f"{self.base_url}/stream",
                    "type": "OrderedCollection",
                    "last": {"id": f"{self.base_url}/stream/page-1", "type": "OrderedCollectionPage"},
                },
                "application/activity+json",
            )
            return
        if path == "/stream/page-1":
            self._json(
                {
                    "id": f"{self.base_url}/stream/page-1",
                    "type": "OrderedCollectionPage",
                    "prev": {"id": f"{self.base_url}/stream/page-0", "type": "OrderedCollectionPage"},
                    "orderedItems": [
                        {
                            "type": "Update",
                            "object": {"id": f"{self.base_url}/manifest/1", "type": "Manifest"},
                            "endTime": "2026-09-19T10:00:00Z",
                        },
                        {
                            "type": "Delete",
                            "object": {"id": f"{self.base_url}/manifest/deleted", "type": "Manifest"},
                        },
                        {
                            "type": "Update",
                            "object": {"id": f"{self.base_url}/collection", "type": "Collection"},
                        },
                    ],
                },
                "application/activity+json",
            )
            return
        if path == "/stream/page-0":
            self._json(
                {
                    "id": f"{self.base_url}/stream/page-0",
                    "type": "OrderedCollectionPage",
                    "next": {"id": f"{self.base_url}/stream/page-1", "type": "OrderedCollectionPage"},
                    "orderedItems": [
                        {
                            "type": "Update",
                            "object": {"id": f"{self.base_url}/manifest/1", "type": "Manifest"},
                        },
                        {
                            "type": "Create",
                            "object": {"id": f"{self.base_url}/manifest/2", "type": "Manifest"},
                        },
                    ],
                },
                "application/activity+json",
            )
            return
        if path == "/paged-collection-1":
            self._json(
                {
                    "id": f"{self.base_url}/paged-collection-1",
                    "type": "Collection",
                    "items": [
                        {"id": f"{self.base_url}/manifest/1", "type": "Manifest"}
                    ],
                    "next": {"id": f"{self.base_url}/paged-collection-2", "type": "Collection"},
                }
            )
            return
        if path == "/paged-collection-2":
            self._json(
                {
                    "id": f"{self.base_url}/paged-collection-2",
                    "type": "Collection",
                    "items": [
                        {"id": f"{self.base_url}/manifest/2", "type": "Manifest"}
                    ],
                }
            )
            return
        if path == "/provider-api":
            self._json(
                {
                    "records": [
                        {"iiif_manifest": f"{self.base_url}/manifest/3"}
                    ]
                },
                "application/json",
            )
            return
        if path == "/collection":
            self._json(
                {
                    "id": f"{self.base_url}/collection",
                    "type": "Collection",
                    "label": {"en": ["Test collection"]},
                    "items": [
                        {"id": f"{self.base_url}/manifest/2", "type": "Manifest"},
                        {"id": f"{self.base_url}/child", "type": "Collection"},
                    ],
                }
            )
            return
        if path == "/child":
            self._json(
                {
                    "@id": f"{self.base_url}/child",
                    "@type": "sc:Collection",
                    "manifests": [
                        {"@id": f"{self.base_url}/manifest/3", "@type": "sc:Manifest"}
                    ],
                }
            )
            return
        if path.startswith("/manifest/"):
            identifier = path.rsplit("/", 1)[-1]
            self._json(
                {
                    "id": f"{self.base_url}{path}",
                    "type": "Manifest",
                    "label": {"en": [f"Manifest {identifier}"]},
                    "items": [],
                }
            )
            return
        if path.startswith("/templated/") and path.endswith("/manifest"):
            identifier = path.split("/")[2]
            self._json(
                {
                    "@context": "http://iiif.io/api/presentation/2/context.json",
                    "@id": f"{self.base_url}{path}",
                    "@type": "sc:Manifest",
                    "label": f"Templated manifest {identifier}",
                    "sequences": [],
                }
            )
            return
        if path == "/site":
            self._html(
                f"""<!doctype html><html><head></head><body>
                <div data-iiif-manifest="{self.base_url}/manifest/1"></div>
                <a href="/records/item">Digital record</a>
                </body></html>"""
            )
            return
        if path == "/records/item":
            self._html(
                f"""<!doctype html><html><head>
                <link rel="alternate" type="application/ld+json" href="{self.base_url}/collection">
                </head><body>Record</body></html>"""
            )
            return
        if path == "/jsonld-site":
            self._html(
                f"""<html><head><script type="application/ld+json">
                {{"id":"{self.base_url}/manifest/1","type":"Manifest"}}
                </script></head><body></body></html>"""
            )
            return
        if path == "/plain":
            self._html("<html><body>No IIIF links here</body></html>")
            return
        if path == "/bad-json":
            self._send(200, b'{"type":', "application/json")
            return
        if path == "/non-iiif-collection":
            self._json(
                {
                    "@context": "https://example.org/api/context.json",
                    "id": f"{self.base_url}/non-iiif-collection",
                    "type": "db:Collection",
                    "label": "A website-specific collection",
                }
            )
            return
        self._send(404, b"not found", "text/plain")

    def _json(self, value: Any, content_type: str = "application/ld+json") -> None:
        self._send(200, json.dumps(value).encode("utf-8"), content_type)

    def _html(self, value: str) -> None:
        self._send(200, value.encode("utf-8"), "text/html; charset=utf-8")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class LocalHttpServer:
    def __enter__(self) -> "LocalHttpServer":
        FixtureHandler.request_counts = {}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"
        FixtureHandler.base_url = self.base_url
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
