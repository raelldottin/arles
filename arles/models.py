"""Typed models used across the application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SortBy = Literal[
    "date_added",
    "title",
    "year",
    "rating",
    "peers",
    "seeds",
    "download_count",
    "like_count",
]
OrderBy = Literal["asc", "desc"]


@dataclass(frozen=True, slots=True)
class SearchFilters:
    """Filtering options supported by the YTS list endpoint."""

    query_term: str = ""
    quality: str = "All"
    genre: str = "All"
    minimum_rating: float = 0.0
    sort_by: SortBy = "year"
    order_by: OrderBy = "desc"
    page: int = 1
    limit: int = 20

    def as_api_params(self) -> dict[str, str | int | float]:
        """Translate the filter object into query parameters."""

        params: dict[str, str | int | float] = {
            "limit": self.limit,
            "page": self.page,
            "sort_by": self.sort_by,
            "order_by": self.order_by,
        }
        if self.query_term:
            params["query_term"] = self.query_term
        if self.quality.lower() != "all":
            params["quality"] = self.quality
        if self.genre.lower() != "all":
            params["genre"] = self.genre
        if self.minimum_rating > 0:
            params["minimum_rating"] = self.minimum_rating
        return params


@dataclass(frozen=True, slots=True)
class Torrent:
    """A torrent option exposed by YTS."""

    url: str
    hash: str
    quality: str
    kind: str
    seeds: int
    peers: int
    size: str
    size_bytes: int

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-serialisable representation of the torrent."""

        return {
            "url": self.url,
            "hash": self.hash,
            "quality": self.quality,
            "kind": self.kind,
            "seeds": self.seeds,
            "peers": self.peers,
            "size": self.size,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class Movie:
    """A movie returned by the YTS catalogue."""

    movie_id: int
    title: str
    year: int
    rating: float
    language: str | None
    url: str | None
    imdb_code: str | None
    summary: str
    genres: tuple[str, ...]
    torrents: tuple[Torrent, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation of the movie."""

        return {
            "movie_id": self.movie_id,
            "title": self.title,
            "year": self.year,
            "rating": self.rating,
            "language": self.language,
            "url": self.url,
            "imdb_code": self.imdb_code,
            "summary": self.summary,
            "genres": list(self.genres),
            "torrents": [torrent.to_dict() for torrent in self.torrents],
        }


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A movie plus the torrent selected for it."""

    movie: Movie
    selected_torrent: Torrent | None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation of the result."""

        return {
            "movie": self.movie.to_dict(),
            "selected_torrent": (
                self.selected_torrent.to_dict()
                if self.selected_torrent is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class DownloadedTorrent:
    """A downloaded torrent file and the result that produced it."""

    result: SearchResult
    path: Path

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation of the download."""

        return {
            "result": self.result.to_dict(),
            "path": str(self.path),
        }
