"""Torrent file download helpers."""

from __future__ import annotations

import re
from pathlib import Path

from arles.http import RequestsTransport


class TorrentDownloader:
    """Download torrent files to the local filesystem."""

    def __init__(self, *, transport: RequestsTransport | None = None) -> None:
        self._transport = transport or RequestsTransport()

    def download(self, url: str, destination: Path) -> Path:
        """Download a torrent to the provided destination path."""

        return self._transport.download(url, destination)


def sanitize_path_component(value: str) -> str:
    """Convert a movie title into a safe filename fragment."""

    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return cleaned or "movie"
