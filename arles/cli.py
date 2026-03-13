"""Command-line interface for arles."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from contextlib import nullcontext
from pathlib import Path
from typing import Protocol

from requests import RequestException

from arles.client import YTSClient
from arles.downloader import TorrentDownloader
from arles.exceptions import ArlesError
from arles.http import RequestsTransport
from arles.logging import LogFile
from arles.models import DownloadedTorrent, SearchFilters, SearchResult
from arles.service import MovieSearchService, TorrentDownloadGateway

DEFAULT_BASE_URL = "https://yts.mx"
SORT_CHOICES = (
    "date_added",
    "title",
    "year",
    "rating",
    "peers",
    "seeds",
    "download_count",
    "like_count",
)
ORDER_CHOICES = ("asc", "desc")


class ApplicationService(Protocol):
    """Protocol describing the service methods the CLI needs."""

    def search(self, filters: SearchFilters) -> list[SearchResult]:
        """Return search results for the supplied filters."""
        ...

    def download_results(
        self,
        results: Sequence[SearchResult],
        destination_dir: Path,
        downloader: TorrentDownloadGateway,
    ) -> list[DownloadedTorrent]:
        """Download the selected torrents for the supplied results."""
        ...


class Application:
    """Runtime container for the service graph."""

    def __init__(
        self,
        *,
        service: ApplicationService,
        downloader: TorrentDownloadGateway,
    ) -> None:
        self.service = service
        self.downloader = downloader


ApplicationFactory = Callable[[str, float], Application]


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser."""

    parser = argparse.ArgumentParser(
        description="Search the YTS catalogue and optionally download torrent files.",
    )
    parser.add_argument(
        "-q",
        "--query",
        default="",
        help="Search term forwarded to the YTS list_movies endpoint.",
    )
    parser.add_argument(
        "--quality",
        default="All",
        help="Preferred torrent quality, for example 720p, 1080p, or 2160p.",
    )
    parser.add_argument(
        "--genre",
        default="All",
        help="Genre filter passed to the API.",
    )
    parser.add_argument(
        "--minimum-rating",
        type=_non_negative_float,
        default=0.0,
        help="Only return titles at or above this rating.",
    )
    parser.add_argument(
        "--sort-by",
        choices=SORT_CHOICES,
        default="year",
        help="Sort field used by YTS.",
    )
    parser.add_argument(
        "--order-by",
        choices=ORDER_CHOICES,
        default="desc",
        help="Sort direction used by YTS.",
    )
    parser.add_argument(
        "--page",
        type=_positive_int,
        default=1,
        help="Page number to request from the catalogue.",
    )
    parser.add_argument(
        "--limit",
        type=_positive_int,
        default=20,
        help="Maximum number of movies to request.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "-p",
        "--print-only",
        action="store_true",
        help="Print the selected torrent URLs instead of downloading them.",
    )
    mode_group.add_argument(
        "-d",
        "--download-torrents",
        action="store_true",
        help="Download the selected torrent files.",
    )
    parser.add_argument(
        "--download-dir",
        default=".",
        help="Directory where torrent files should be written in download mode.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output instead of human-readable lines.",
    )
    parser.add_argument(
        "-l",
        "--log-file",
        default="",
        help="Mirror command output into the supplied file.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print extra execution details.",
    )
    parser.add_argument(
        "--timeout",
        type=_positive_float,
        default=10.0,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Override the YTS base URL. Useful for integration testing.",
    )
    return parser


def create_application(base_url: str, timeout: float) -> Application:
    """Create the concrete application graph."""

    transport = RequestsTransport(timeout=timeout)
    return Application(
        service=MovieSearchService(YTSClient(base_url=base_url, transport=transport)),
        downloader=TorrentDownloader(transport=transport),
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    application_factory: ApplicationFactory = create_application,
) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    filters = SearchFilters(
        query_term=args.query,
        quality=args.quality,
        genre=args.genre,
        minimum_rating=args.minimum_rating,
        sort_by=args.sort_by,
        order_by=args.order_by,
        page=args.page,
        limit=args.limit,
    )
    output_context = LogFile(args.log_file) if args.log_file else nullcontext()

    try:
        with output_context:
            if args.verbose:
                print(f"Querying {args.base_url} with {filters.as_api_params()}")

            application = application_factory(args.base_url, args.timeout)
            results = application.service.search(filters)

            if args.download_torrents:
                downloads = application.service.download_results(
                    results,
                    Path(args.download_dir),
                    application.downloader,
                )
                _print_downloads(downloads, as_json=args.json)
            else:
                _print_results(results, as_json=args.json)

            if args.verbose:
                print(f"Processed {len(results)} movie(s).")
    except (ArlesError, RequestException, OSError) as error:
        print(f"arles: {error}", file=sys.stderr)
        return 1

    return 0


def _print_results(results: Sequence[SearchResult], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps([result.to_dict() for result in results], indent=2))
        return

    for result in results:
        torrent = result.selected_torrent
        if torrent is None:
            print(
                f"{result.movie.title} ({result.movie.year}) "
                "- no torrent match found"
            )
            continue
        print(
            f"{result.movie.title} ({result.movie.year}) "
            f"[{torrent.quality}] {torrent.url}"
        )


def _print_downloads(downloads: Sequence[DownloadedTorrent], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps([download.to_dict() for download in downloads], indent=2))
        return

    for download in downloads:
        print(
            "Downloaded "
            f"{download.result.movie.title} "
            f"to {download.path}"
        )


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def _non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be zero or greater")
    return parsed
