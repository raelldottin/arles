"""Unit tests for the service layer."""

from __future__ import annotations

from pathlib import Path

from arles.models import Movie, SearchFilters, Torrent
from arles.service import MovieSearchService, TorrentSelector, build_torrent_filename


class FakeCatalog:
    def __init__(self, movies: list[Movie]) -> None:
        self._movies = movies
        self.received_filters: SearchFilters | None = None

    def list_movies(self, filters: SearchFilters) -> list[Movie]:
        self.received_filters = filters
        return list(self._movies)


class FakeDownloader:
    def __init__(self) -> None:
        self.downloads: list[tuple[str, Path]] = []

    def download(self, url: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(url, encoding="utf-8")
        self.downloads.append((url, destination))
        return destination


def test_selector_prefers_requested_quality_when_available() -> None:
    selector = TorrentSelector()

    result = selector.select(
        [
            _torrent("1080p", seeds=200, peers=50, size_bytes=100),
            _torrent("2160p", seeds=120, peers=40, size_bytes=200),
        ],
        preferred_quality="2160p",
    )

    assert result is not None
    assert result.quality == "2160p"


def test_selector_falls_back_to_best_seeded_torrent_when_quality_is_missing() -> None:
    selector = TorrentSelector()

    result = selector.select(
        [
            _torrent("1080p", seeds=10, peers=4, size_bytes=100),
            _torrent("720p", seeds=40, peers=10, size_bytes=80),
        ],
        preferred_quality="2160p",
    )

    assert result is not None
    assert result.quality == "720p"


def test_service_passes_filters_to_the_catalogue() -> None:
    filters = SearchFilters(query_term="matrix", quality="2160p")
    catalog = FakeCatalog([_movie()])
    service = MovieSearchService(catalog)

    service.search(filters)

    assert catalog.received_filters == filters


def test_service_downloads_selected_torrents_using_predictable_filenames(
    tmp_path: Path,
) -> None:
    catalog = FakeCatalog([_movie()])
    downloader = FakeDownloader()
    service = MovieSearchService(catalog)

    results = service.search(SearchFilters(query_term="matrix", quality="2160p"))
    downloads = service.download_results(results, tmp_path, downloader)

    assert len(downloads) == 1
    assert downloads[0].path.name == "The_Matrix_1999_2160p.torrent"
    assert downloads[0].path.read_text(encoding="utf-8").endswith(".torrent")


def test_build_torrent_filename_sanitises_titles() -> None:
    filename = build_torrent_filename(
        _movie(title="Spider-Man: Into the Spider-Verse"),
        _torrent("1080p"),
    )

    assert filename == "Spider_Man_Into_the_Spider_Verse_1999_1080p.torrent"


def _movie(title: str = "The Matrix") -> Movie:
    return Movie(
        movie_id=603,
        title=title,
        year=1999,
        rating=8.7,
        language="en",
        url="https://example.com/movies/the-matrix",
        imdb_code="tt0133093",
        summary="A computer hacker learns about the true nature of reality.",
        genres=("Action", "Sci-Fi"),
        torrents=(
            _torrent("2160p", seeds=250, peers=120, size_bytes=10844792422),
            _torrent("1080p", seeds=200, peers=80, size_bytes=2469606195),
        ),
    )


def _torrent(
    quality: str,
    *,
    seeds: int = 10,
    peers: int = 5,
    size_bytes: int = 1024,
) -> Torrent:
    return Torrent(
        url=f"https://example.com/{quality}.torrent",
        hash=f"hash-{quality}",
        quality=quality,
        kind="web",
        seeds=seeds,
        peers=peers,
        size="1 GB",
        size_bytes=size_bytes,
    )
