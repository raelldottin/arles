"""Shared pytest fixtures."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse

import pytest


@dataclass(frozen=True, slots=True)
class StubYtsServer:
    """Local HTTP server used by integration tests."""

    base_url: str


def _list_movies_payload(base_url: str) -> dict[str, object]:
    torrent_url = f"{base_url}/torrent/the-matrix-1999-2160p.torrent"
    return {
        "status": "ok",
        "status_message": "Query was successful",
        "data": {
            "movie_count": 1,
            "limit": 1,
            "page_number": 1,
            "movies": [
                {
                    "id": 603,
                    "title": "The Matrix",
                    "year": 1999,
                    "rating": 8.7,
                    "language": "en",
                    "url": f"{base_url}/movies/the-matrix",
                    "imdb_code": "tt0133093",
                    "summary": (
                        "A computer hacker learns about the true nature of reality."
                    ),
                    "genres": ["Action", "Sci-Fi"],
                    "torrents": [
                        {
                            "url": torrent_url,
                            "hash": "abcdef123456",
                            "quality": "2160p",
                            "type": "web",
                            "seeds": 250,
                            "peers": 120,
                            "size": "10.1 GB",
                            "size_bytes": 10844792422,
                        },
                        {
                            "url": f"{base_url}/torrent/the-matrix-1999-1080p.torrent",
                            "hash": "fedcba654321",
                            "quality": "1080p",
                            "type": "bluray",
                            "seeds": 200,
                            "peers": 80,
                            "size": "2.3 GB",
                            "size_bytes": 2469606195,
                        },
                    ],
                }
            ],
        },
    }


@pytest.fixture
def stub_yts_server() -> Iterator[StubYtsServer]:
    """Serve a tiny YTS-compatible API for integration tests."""

    server: ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/v2/list_movies.json":
                self._send_json(_list_movies_payload(f"http://127.0.0.1:{server.server_port}"))
                return

            if parsed.path == "/torrent/the-matrix-1999-2160p.torrent":
                self._send_bytes(b"dummy torrent data")
                return

            if parsed.path == "/torrent/the-matrix-1999-1080p.torrent":
                self._send_bytes(b"fallback torrent data")
                return

            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_json(self, payload: dict[str, object]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_bytes(self, payload: bytes) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "application/x-bittorrent")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield StubYtsServer(base_url=f"http://127.0.0.1:{server.server_port}")
    finally:
        server.shutdown()
        thread.join()
