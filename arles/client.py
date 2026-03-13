"""Typed client for the YTS API."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeGuard
from urllib.parse import urljoin

from arles.exceptions import YTSAPIError
from arles.http import QueryParams, RequestsTransport
from arles.models import Movie, SearchFilters, Torrent


class YTSClient:
    """Client responsible for talking to the YTS JSON API."""

    def __init__(
        self,
        *,
        base_url: str = "https://yts.mx",
        transport: RequestsTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport or RequestsTransport()

    def list_movies(self, filters: SearchFilters) -> list[Movie]:
        """List movies that match the provided filters."""

        payload = self._transport.get_json(
            self._url("/api/v2/list_movies.json"),
            filters.as_api_params(),
        )
        return self._extract_movies(payload)

    def movie_details(
        self,
        movie_id: int,
        *,
        with_images: bool = False,
        with_cast: bool = False,
    ) -> Movie:
        """Fetch detailed information for a single movie."""

        payload = self._transport.get_json(
            self._url("/api/v2/movie_details.json"),
            {
                "movie_id": movie_id,
                "with_images": with_images,
                "with_cast": with_cast,
            },
        )
        _ensure_ok(payload)
        data = _require_mapping(payload.get("data"), "data")
        raw_movie = _require_mapping(data.get("movie"), "movie")
        return _parse_movie(raw_movie)

    def find_movie_by_imdb(self, imdb_code: str) -> Movie | None:
        """Resolve a movie from its IMDb code using the list endpoint."""

        movies = self.list_movies(SearchFilters(query_term=imdb_code, limit=1))
        for movie in movies:
            if movie.imdb_code == imdb_code:
                return movie
        return movies[0] if movies else None

    def get_json(
        self, endpoint: str, params: QueryParams | None = None
    ) -> Mapping[str, object]:
        """Expose raw JSON access for advanced callers and compatibility wrappers."""

        return self._transport.get_json(self._url(endpoint), params)

    def _extract_movies(self, payload: Mapping[str, object]) -> list[Movie]:
        _ensure_ok(payload)
        data = _require_mapping(payload.get("data"), "data")
        raw_movies = data.get("movies")
        if raw_movies is None:
            return []
        if not _is_non_string_sequence(raw_movies):
            raise YTSAPIError("Expected 'movies' to be a JSON array.")
        return [
            _parse_movie(_require_mapping(item, "movie entry"))
            for item in raw_movies
        ]

    def _url(self, endpoint: str) -> str:
        return urljoin(f"{self._base_url}/", endpoint.lstrip("/"))


def _parse_movie(data: Mapping[str, object]) -> Movie:
    raw_torrents = data.get("torrents")
    torrents: list[Torrent] = []
    if raw_torrents is not None:
        if not _is_non_string_sequence(raw_torrents):
            raise YTSAPIError("Expected 'torrents' to be a JSON array.")
        torrents = [
            _parse_torrent(_require_mapping(item, "torrent entry"))
            for item in raw_torrents
        ]

    raw_genres = data.get("genres")
    genres: tuple[str, ...] = ()
    if raw_genres is not None:
        if not _is_non_string_sequence(raw_genres):
            raise YTSAPIError("Expected 'genres' to be a JSON array.")
        genres = tuple(_coerce_str(item, "genre") for item in raw_genres)

    return Movie(
        movie_id=_coerce_int(data.get("id"), "id"),
        title=_coerce_str(data.get("title"), "title"),
        year=_coerce_int(data.get("year"), "year", default=0),
        rating=_coerce_float(data.get("rating"), "rating", default=0.0),
        language=_coerce_optional_str(data.get("language")),
        url=_coerce_optional_str(data.get("url")),
        imdb_code=_coerce_optional_str(data.get("imdb_code")),
        summary=_coerce_optional_str(data.get("summary")) or "",
        genres=genres,
        torrents=tuple(torrents),
    )


def _parse_torrent(data: Mapping[str, object]) -> Torrent:
    return Torrent(
        url=_coerce_str(data.get("url"), "torrent.url"),
        hash=_coerce_optional_str(data.get("hash")) or "",
        quality=_coerce_str(data.get("quality"), "torrent.quality"),
        kind=_coerce_optional_str(data.get("type")) or "unknown",
        seeds=_coerce_int(data.get("seeds"), "torrent.seeds", default=0),
        peers=_coerce_int(data.get("peers"), "torrent.peers", default=0),
        size=_coerce_optional_str(data.get("size")) or "",
        size_bytes=_coerce_int(data.get("size_bytes"), "torrent.size_bytes", default=0),
    )


def _ensure_ok(payload: Mapping[str, object]) -> None:
    status = payload.get("status")
    if status is None:
        return
    if _coerce_str(status, "status").lower() != "ok":
        message = (
            _coerce_optional_str(payload.get("status_message"))
            or "unknown API failure"
        )
        raise YTSAPIError(f"YTS API request failed: {message}")


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    raise YTSAPIError(f"Expected '{field_name}' to be a JSON object.")


def _coerce_str(value: object, field_name: str) -> str:
    if isinstance(value, str):
        return value
    raise YTSAPIError(f"Expected '{field_name}' to be a string.")


def _coerce_optional_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _coerce_int(value: object, field_name: str, *, default: int | None = None) -> int:
    if value is None:
        if default is not None:
            return default
        raise YTSAPIError(f"Expected '{field_name}' to be present.")
    if isinstance(value, bool):
        raise YTSAPIError(f"Expected '{field_name}' to be an integer.")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip():
        return int(value)
    raise YTSAPIError(f"Expected '{field_name}' to be an integer.")


def _coerce_float(
    value: object, field_name: str, *, default: float | None = None
) -> float:
    if value is None:
        if default is not None:
            return default
        raise YTSAPIError(f"Expected '{field_name}' to be present.")
    if isinstance(value, bool):
        raise YTSAPIError(f"Expected '{field_name}' to be numeric.")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        return float(value)
    raise YTSAPIError(f"Expected '{field_name}' to be numeric.")


def _is_non_string_sequence(value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )
