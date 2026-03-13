"""Integration tests that exercise the real HTTP boundary locally."""

from __future__ import annotations

from pathlib import Path

import pytest

from arles.cli import main
from arles.client import YTSClient
from arles.models import SearchFilters
from tests.conftest import StubYtsServer


@pytest.mark.integration
def test_client_parses_movies_from_the_local_stub_server(
    stub_yts_server: StubYtsServer,
) -> None:
    client = YTSClient(base_url=stub_yts_server.base_url)

    movies = client.list_movies(SearchFilters(query_term="matrix", quality="2160p"))

    assert len(movies) == 1
    assert movies[0].title == "The Matrix"
    assert movies[0].torrents[0].quality == "2160p"


@pytest.mark.integration
def test_cli_downloads_torrent_using_the_local_stub_server(
    stub_yts_server: StubYtsServer,
    tmp_path: Path,
) -> None:
    exit_code = main(
        [
            "--query",
            "matrix",
            "--quality",
            "2160p",
            "--download-torrents",
            "--download-dir",
            str(tmp_path),
            "--base-url",
            stub_yts_server.base_url,
        ]
    )

    downloaded_file = tmp_path / "The_Matrix_1999_2160p.torrent"
    assert exit_code == 0
    assert downloaded_file.exists()
    assert downloaded_file.read_bytes() == b"dummy torrent data"
