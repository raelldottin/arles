"""Minimal example that exercises the compatibility API wrapper."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from api import NewMovieEndpoint


def main() -> int:
    yts_mx = NewMovieEndpoint()
    response = yts_mx.list_movies(
        limit=5,
        page=1,
        quality="2160p",
        minimum_rating=8,
    )
    payload = response.json()
    if not isinstance(payload, Mapping):
        return 1
    data = payload.get("data")
    if not isinstance(data, Mapping):
        return 1
    movies = data.get("movies")
    if not isinstance(movies, Sequence):
        return 1

    for movie in movies:
        if not isinstance(movie, Mapping):
            continue
        title = movie.get("title", "Unknown")
        year = movie.get("year", "Unknown")
        print(f"{title} ({year})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
