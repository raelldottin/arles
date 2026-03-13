"""Compatibility session wrapper for older imports."""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar
from urllib.parse import urljoin

import requests

from arles.http import DEFAULT_TIMEOUT, QueryValue, RequestsTransport


class NewSession:
    """Legacy wrapper that keeps the old method names in place."""

    headers: ClassVar[dict[str, str]] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def __init__(self, *, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._transport = RequestsTransport(timeout=timeout)

    def get(
        self,
        url: str,
        endpoint: str,
        params: Mapping[str, QueryValue] | None = None,
    ) -> requests.Response:
        """Perform an HTTP GET request."""

        return self._transport.get_response(_join_url(url, endpoint), params)

    def post(self, url: str, endpoint: str) -> requests.Response:
        """Perform an HTTP POST request."""

        return self._transport.post_response(_join_url(url, endpoint))

    def query(
        self,
        url: str,
        endpoint: str,
        params: Mapping[str, QueryValue] | None = None,
    ) -> requests.Response:
        """Perform the default query request."""

        return self.get(url, endpoint, params)


def _join_url(base_url: str, endpoint: str) -> str:
    return urljoin(f"{base_url.rstrip('/')}/", endpoint.lstrip("/"))
