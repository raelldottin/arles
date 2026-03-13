"""Unit tests for CLI orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from arles.cli import Application, main
from arles.models import DownloadedTorrent, Movie, SearchFilters, SearchResult, Torrent
from arles.service import TorrentDownloadGateway


class FakeService:
    def __init__(
        self,
        *,
        results: list[SearchResult],
        downloads: list[DownloadedTorrent] | None = None,
    ) -> None:
        self._results = results
        self._downloads = downloads or []
        self.received_filters: SearchFilters | None = None
        self.download_destination: Path | None = None

    def search(self, filters: SearchFilters) -> list[SearchResult]:
        self.received_filters = filters
        return list(self._results)

    def download_results(
        self,
        results: Sequence[SearchResult],
        destination_dir: Path,
        downloader: TorrentDownloadGateway,
    ) -> list[DownloadedTorrent]:
        self.download_destination = destination_dir
        return list(self._downloads)


class FakeDownloader:
    def download(self, url: str, destination: Path) -> Path:
        return destination


def test_main_prints_text_results(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = _search_result()
    service = FakeService(results=[result])

    exit_code = main(
        ["--query", "matrix", "--print-only"],
        application_factory=lambda _base_url, _timeout: Application(
            service=service,
            downloader=FakeDownloader(),
        ),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert service.received_filters == SearchFilters(query_term="matrix")
    assert "The Matrix (1999) [2160p]" in captured.out


def test_main_runs_download_mode(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    result = _search_result()
    download = DownloadedTorrent(
        result=result,
        path=tmp_path / "The_Matrix_1999_2160p.torrent",
    )
    service = FakeService(results=[result], downloads=[download])

    exit_code = main(
        [
            "--query",
            "matrix",
            "--download-torrents",
            "--download-dir",
            str(tmp_path),
        ],
        application_factory=lambda _base_url, _timeout: Application(
            service=service,
            downloader=FakeDownloader(),
        ),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert service.download_destination == tmp_path
    assert "Downloaded The Matrix" in captured.out


def _search_result() -> SearchResult:
    torrent = Torrent(
        url="https://example.com/the-matrix-2160p.torrent",
        hash="abcdef123456",
        quality="2160p",
        kind="web",
        seeds=250,
        peers=120,
        size="10.1 GB",
        size_bytes=10844792422,
    )
    movie = Movie(
        movie_id=603,
        title="The Matrix",
        year=1999,
        rating=8.7,
        language="en",
        url="https://example.com/movies/the-matrix",
        imdb_code="tt0133093",
        summary="A computer hacker learns about the true nature of reality.",
        genres=("Action", "Sci-Fi"),
        torrents=(torrent,),
    )
    return SearchResult(movie=movie, selected_torrent=torrent)
