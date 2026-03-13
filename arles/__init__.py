"""Public package exports for arles."""

from arles.client import YTSClient
from arles.models import DownloadedTorrent, Movie, SearchFilters, SearchResult, Torrent
from arles.service import MovieSearchService, TorrentSelector

__all__ = [
    "DownloadedTorrent",
    "Movie",
    "MovieSearchService",
    "SearchFilters",
    "SearchResult",
    "Torrent",
    "TorrentSelector",
    "YTSClient",
]

__version__ = "0.1.0"
