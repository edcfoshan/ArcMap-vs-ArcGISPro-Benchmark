#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Local HTTP server for the benchmark verification console."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .scheduler import VerificationScheduler

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(PACKAGE_DIR, "static")
INDEX_HTML = os.path.join(STATIC_DIR, "index.html")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _read_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _json_response(handler, payload, status=200):
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _text_response(handler, text, content_type="text/plain; charset=utf-8", status=200):
    data = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _guess_mime(path):
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def _build_handler(scheduler):
    class Handler(BaseHTTPRequestHandler):
        server_version = "BenchmarkVerificationConsole/1.0"

        def log_message(self, format, *args):
            return

        def _serve_static(self, path):
            if path == "/":
                if os.path.exists(INDEX_HTML):
                    _text_response(self, _read_file(INDEX_HTML), content_type="text/html; charset=utf-8")
                else:
                    _text_response(self, "index.html is missing", status=500)
                return

            if path.startswith("/static/"):
                rel = path[len("/static/") :]
                local_path = os.path.join(STATIC_DIR, rel)
                if not os.path.exists(local_path) or not os.path.isfile(local_path):
                    _text_response(self, "Not found", status=404)
                    return
                with open(local_path, "rb") as handle:
                    data = handle.read()
                self.send_response(200)
                self.send_header("Content-Type", _guess_mime(local_path))
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            _text_response(self, "Not found", status=404)

        def _read_json_body(self):
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length <= 0:
                return {}
            raw = self.rfile.read(length)
            if not raw:
                return {}
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", "replace")
            return json.loads(raw)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                return self._serve_static("/")

            if parsed.path == "/favicon.ico":
                handler = self
                handler.send_response(204)
                handler.send_header("Content-Length", "0")
                handler.end_headers()
                return

            if parsed.path.startswith("/static/"):
                return self._serve_static(parsed.path)

            if parsed.path == "/api/state":
                return _json_response(self, scheduler.snapshot())

            if parsed.path == "/api/health":
                state = scheduler.snapshot()
                payload = {
                    "ok": True,
                    "status": state.get("status"),
                    "message": state.get("message"),
                    "running": state.get("running", False),
                    "environment": state.get("environment", {}),
                    "config": state.get("config", {}),
                }
                return _json_response(self, payload)

            if parsed.path == "/api/config":
                state = scheduler.snapshot()
                return _json_response(self, state.get("config", {}))

            if parsed.path == "/api/logs":
                state = scheduler.snapshot()
                return _json_response(self, {"logs": state.get("logs", [])})

            if parsed.path == "/api/result":
                query = parse_qs(parsed.query or "")
                scale = (query.get("scale") or [""])[0].strip()
                if not scale:
                    return _json_response(self, {"ok": False, "error": "Missing scale"}, status=400)
                state = scheduler.snapshot()
                for scale_state in state.get("scales", []):
                    if scale_state.get("scale") == scale:
                        return _json_response(self, {"ok": True, "scale": scale_state})
                return _json_response(self, {"ok": False, "error": "Scale not found"}, status=404)

            return _json_response(self, {"ok": False, "error": "Not found"}, status=404)

        def do_POST(self):
            parsed = urlparse(self.path)
            if parsed.path == "/api/start":
                try:
                    payload = self._read_json_body()
                except Exception as exc:
                    return _json_response(self, {"ok": False, "error": str(exc)}, status=400)

                result = scheduler.start(payload)
                status = 200 if result.get("ok") else 400
                return _json_response(self, result, status=status)

            if parsed.path == "/api/stop":
                return _json_response(self, scheduler.stop())

            return _json_response(self, {"ok": False, "error": "Not found"}, status=404)

    return Handler


def create_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    scheduler = VerificationScheduler()
    handler = _build_handler(scheduler)
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.scheduler = scheduler
    return httpd


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark verification web console")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--open-browser", action="store_true", help="Open the console in the default browser")
    args = parser.parse_args(argv)

    httpd = create_server(args.host, args.port)
    actual_host, actual_port = httpd.server_address
    url = "http://{}:{}/".format(actual_host, actual_port)
    print("Benchmark verification console listening on {}".format(url))

    if args.open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Console stopped")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
