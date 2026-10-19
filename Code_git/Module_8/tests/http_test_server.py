from __future__ import annotations

import base64
import json
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
JPEG_SAMPLE = b"\xff\xd8\xff\xe0" + b"module-eight-test" + b"\xff\xd9"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/image.png":
            self._send(200, "image/png", PNG_1X1)
        elif self.path == "/image.jpg":
            self._send(200, "image/jpeg", JPEG_SAMPLE)
        elif self.path == "/mislabelled":
            self._send(200, "application/octet-stream", PNG_1X1)
        elif self.path == "/text":
            self._send(200, "application/json", b'{"not": "an image"}')
        elif self.path == "/ocr/1":
            self._send(
                200,
                "text/vnd.hocr+html; charset=utf-8",
                b'<html><body><span class="ocrx_word">Reference</span> <span class="ocrx_word">text</span></body></html>',
            )
        elif self.path == "/large":
            self._send(200, "image/jpeg", b"\xff\xd8\xff" + b"x" * 200)
        elif self.path == "/service/info.json":
            host, port = self.server.server_address
            body = {"@context": "http://iiif.io/api/image/3/context.json", "type": "ImageService3",
                    "id": f"http://{host}:{port}/service", "width": 100, "height": 200}
            self._send(200, "application/json", json.dumps(body).encode())
        elif self.path == "/service/full/max/0/default.jpg":
            self._send(200, "image/jpeg", JPEG_SAMPLE)
        elif self.path == "/restricted":
            self._send(403, "text/plain", b"forbidden")
        else:
            self._send(404, "text/plain", b"missing")

    def _send(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A003
        return


@contextmanager
def running_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
