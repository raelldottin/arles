"""Compatibility wrapper for older imports that used the top-level `api` module."""

from __future__ import annotations

from collections.abc import Mapping

from arles.client import YTSClient
from arles.http import QueryValue
from arles.models import SearchFilters
from session import NewSession


class NewMovieEndpoint:
    """Legacy adapter that preserves the old response-oriented surface area."""

    def __init__(
        self,
        *,
        base_url: str = "https://yts.mx",
        request_session: NewSession | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.yts_mx = request_session or NewSession()

    def list_movies(
        self,
        *,
        limit: int = 20,
        page: int = 1,
        quality: str = "All",
        minimum_rating: float = 0.0,
        query_term: str = "",
        genre: str = "All",
        sort_by: str = "year",
        order_by: str = "desc",
        with_rt_ratings: bool = False,
        endpoint: str = "/api/v2/list_movies.json",
        params: Mapping[str, QueryValue] | None = None,
    ):
        endpoint_params = params or SearchFilters(
            limit=limit,
            page=page,
            quality=quality,
            minimum_rating=minimum_rating,
            query_term=query_term,
            genre=genre,
            sort_by=sort_by,  # type: ignore[arg-type]
            order_by=order_by,  # type: ignore[arg-type]
        ).as_api_params()
        if endpoint == "/api/v2/list_movies.json":
            endpoint_params = {
                **endpoint_params,
                "with_rt_ratings": with_rt_ratings,
            }
        return self.yts_mx.query(
            url=self.base_url,
            endpoint=endpoint,
            params=endpoint_params,
        )

    def movie_details(
        self,
        *,
        movie_id: int | None = None,
        imdb_id: str = "",
        with_images: bool = False,
        with_cast: bool = False,
        endpoint: str = "/api/v2/movie_details.json",
    ):
        resolved_movie_id = movie_id
        if resolved_movie_id is None and imdb_id:
            movie = YTSClient(base_url=self.base_url).find_movie_by_imdb(imdb_id)
            if movie is None:
                raise ValueError(f"No movie found for IMDb id {imdb_id}.")
            resolved_movie_id = movie.movie_id
        if resolved_movie_id is None:
            raise ValueError("movie_id or imdb_id must be supplied.")
        return self.yts_mx.query(
            url=self.base_url,
            endpoint=endpoint,
            params={
                "movie_id": resolved_movie_id,
                "with_images": with_images,
                "with_cast": with_cast,
            },
        )
