"""Pure application services."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from arles.downloader import sanitize_path_component
from arles.models import DownloadedTorrent, Movie, SearchFilters, SearchResult, Torrent


class MovieCatalogGateway(Protocol):
    """Protocol for movie catalogue clients."""

    def list_movies(self, filters: SearchFilters) -> list[Movie]:
        """Return the movies that match the provided search filters."""
        ...


class TorrentDownloadGateway(Protocol):
    """Protocol for torrent download infrastructure."""

    def download(self, url: str, destination: Path) -> Path:
        """Download a torrent to the requested destination."""
        ...


class TorrentSelector:
    """Select the best torrent for a movie."""

    def select(
        self, torrents: Sequence[Torrent], *, preferred_quality: str = "All"
    ) -> Torrent | None:
        """Choose the preferred torrent if present, otherwise the healthiest one."""

        if not torrents:
            return None

        desired_quality = preferred_quality.lower()
        if desired_quality != "all":
            matching = [
                torrent
                for torrent in torrents
                if torrent.quality.lower() == desired_quality
            ]
            if matching:
                return max(matching, key=_torrent_score)

        return max(torrents, key=_torrent_score)


class MovieSearchService:
    """Coordinate catalogue lookups and downloads."""

    def __init__(
        self, catalog: MovieCatalogGateway, selector: TorrentSelector | None = None
    ) -> None:
        self._catalog = catalog
        self._selector = selector or TorrentSelector()

    def search(self, filters: SearchFilters) -> list[SearchResult]:
        """Search for movies and attach the selected torrent to each result."""

        return [
            SearchResult(
                movie=movie,
                selected_torrent=self._selector.select(
                    movie.torrents,
                    preferred_quality=filters.quality,
                ),
            )
            for movie in self._catalog.list_movies(filters)
        ]

    def download_results(
        self,
        results: Sequence[SearchResult],
        destination_dir: Path,
        downloader: TorrentDownloadGateway,
    ) -> list[DownloadedTorrent]:
        """Download all selected torrents into the destination directory."""

        destination_dir.mkdir(parents=True, exist_ok=True)
        downloads: list[DownloadedTorrent] = []
        for result in results:
            torrent = result.selected_torrent
            if torrent is None:
                continue
            destination = destination_dir / build_torrent_filename(
                result.movie,
                torrent,
            )
            downloads.append(
                DownloadedTorrent(
                    result=result,
                    path=downloader.download(torrent.url, destination),
                )
            )
        return downloads


def build_torrent_filename(movie: Movie, torrent: Torrent) -> str:
    """Build a predictable torrent filename for local downloads."""

    safe_title = sanitize_path_component(movie.title)
    return f"{safe_title}_{movie.year}_{torrent.quality}.torrent"


def _torrent_score(torrent: Torrent) -> tuple[int, int, int]:
    return (torrent.seeds, torrent.peers, torrent.size_bytes)
