"""Local HTTP fixtures for deterministic Module 4 tests."""

from __future__ import annotations

from collections import Counter
from contextlib import AbstractContextManager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from typing import Any


class ManifestTestServer(AbstractContextManager["ManifestTestServer"]):
    def __init__(self) -> None:
        self.requests: Counter[str] = Counter()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                owner.requests[self.path] += 1
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/v3/manifest")
                    self.end_headers()
                    return
                if self.path == "/forbidden":
                    self.send_error(403)
                    return
                if self.path == "/invalid-json":
                    self._send(200, b"{not json", "application/json")
                    return
                if self.path == "/html":
                    self._send(200, b"<html>not json</html>", "text/html")
                    return
                if self.path == "/large":
                    self._send(200, b"x" * 4096, "application/json")
                    return
                if self.path == "/v3/manifest":
                    self._json(owner.v3_manifest())
                    return
                if self.path == "/v2/manifest":
                    self._json(owner.v2_manifest())
                    return
                if self.path == "/missing-id":
                    value = owner.v2_manifest()
                    value.pop("@id")
                    self._json(value)
                    return
                if self.path == "/missing-context":
                    value = owner.v3_manifest()
                    value.pop("@context")
                    self._json(value)
                    return
                if self.path == "/empty":
                    value = owner.v3_manifest()
                    value["items"] = []
                    self._json(value)
                    return
                if self.path == "/wrong-type":
                    self._json(
                        {
                            "@context": "http://iiif.io/api/presentation/3/context.json",
                            "id": owner.url("/wrong-type"),
                            "type": "Collection",
                            "items": [],
                        }
                    )
                    return
                self.send_error(404)

            def _json(self, value: Any) -> None:
                self._send(
                    200,
                    json.dumps(value).encode("utf-8"),
                    "application/ld+json",
                )

            def _send(self, status: int, body: bytes, content_type: str) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def url(self, path: str) -> str:
        return self.base_url + path

    def __enter__(self) -> "ManifestTestServer":
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def v3_manifest(self) -> dict[str, Any]:
        return {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": self.url("/v3/manifest"),
            "type": "Manifest",
            "label": {"en": ["Test book"]},
            "rights": "http://creativecommons.org/publicdomain/mark/1.0/",
            "items": [
                {
                    "id": self.url("/canvas/1"),
                    "type": "Canvas",
                    "label": {"en": ["Page 1"]},
                    "items": [
                        {
                            "id": self.url("/page/1"),
                            "type": "AnnotationPage",
                            "items": [
                                {
                                    "id": self.url("/annotation/1"),
                                    "type": "Annotation",
                                    "motivation": "painting",
                                    "body": {
                                        "id": self.url("/image/1.jpg"),
                                        "type": "Image",
                                        "format": "image/jpeg",
                                        "service": [
                                            {
                                                "id": self.url("/iiif/image/1"),
                                                "type": "ImageService3",
                                            }
                                        ],
                                    },
                                    "target": self.url("/canvas/1"),
                                }
                            ],
                        }
                    ],
                },
                {
                    "id": self.url("/canvas/2"),
                    "type": "Canvas",
                    "label": {"en": ["Page 2"]},
                    "items": [
                        {
                            "id": self.url("/page/2"),
                            "type": "AnnotationPage",
                            "items": [
                                {
                                    "id": self.url("/annotation/2"),
                                    "type": "Annotation",
                                    "motivation": "painting",
                                    "body": {
                                        "type": "Choice",
                                        "items": [
                                            {
                                                "id": self.url("/image/2.jpg"),
                                                "type": "Image",
                                                "format": "image/jpeg",
                                            },
                                            {
                                                "id": self.url("/image/2.png"),
                                                "type": "Image",
                                                "format": "image/png",
                                            },
                                        ],
                                    },
                                    "target": self.url("/canvas/2"),
                                }
                            ],
                        }
                    ],
                },
            ],
        }

    def v2_manifest(self) -> dict[str, Any]:
        return {
            "@context": "http://iiif.io/api/presentation/2/context.json",
            "@id": self.url("/v2/manifest"),
            "@type": "sc:Manifest",
            "label": "Test manuscript",
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "sequences": [
                {
                    "@id": self.url("/sequence/normal"),
                    "@type": "sc:Sequence",
                    "canvases": [
                        {
                            "@id": self.url("/v2/canvas/1"),
                            "@type": "sc:Canvas",
                            "label": "Leaf 1",
                            "images": [
                                {
                                    "@id": self.url("/v2/annotation/1"),
                                    "@type": "oa:Annotation",
                                    "resource": {
                                        "@id": self.url("/v2/image/1.jpg"),
                                        "@type": "dctypes:Image",
                                        "format": "image/jpeg",
                                        "service": {
                                            "@id": self.url("/v2/iiif/image/1"),
                                            "profile": "http://iiif.io/api/image/2/level2.json",
                                        },
                                    },
                                    "on": self.url("/v2/canvas/1"),
                                }
                            ],
                        }
                    ],
                }
            ],
        }
