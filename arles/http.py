"""HTTP transport helpers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from arles.exceptions import YTSAPIError

QueryValue = str | int | float | bool
QueryParams = Mapping[str, QueryValue]

DEFAULT_TIMEOUT = 10.0
DEFAULT_USER_AGENT = "arles/0.1.0"


def build_retry_session() -> requests.Session:
    """Build a requests session with sensible retry defaults."""

    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class RequestsTransport:
    """Thin wrapper around requests to keep infrastructure concerns isolated."""

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._session = session or build_retry_session()
        self._timeout = timeout

    def get_response(
        self, url: str, params: QueryParams | None = None
    ) -> requests.Response:
        """Perform a GET request and raise on failure."""

        response = self._session.get(
            url,
            params=_normalise_params(params),
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response

    def post_response(
        self, url: str, json_body: Mapping[str, object] | None = None
    ) -> requests.Response:
        """Perform a POST request and raise on failure."""

        response = self._session.post(url, json=json_body, timeout=self._timeout)
        response.raise_for_status()
        return response

    def get_json(
        self, url: str, params: QueryParams | None = None
    ) -> Mapping[str, object]:
        """Perform a GET request and validate that the response is a JSON object."""

        response = self.get_response(url, params)
        payload = cast(object, response.json())
        if not isinstance(payload, Mapping):
            raise YTSAPIError("Expected a JSON object from the API response.")
        return cast(Mapping[str, object], payload)

    def download(self, url: str, destination: Path) -> Path:
        """Download a file to the requested destination."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        with self._session.get(url, stream=True, timeout=self._timeout) as response:
            response.raise_for_status()
            with destination.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        handle.write(chunk)
        return destination


def _normalise_params(
    params: QueryParams | None,
) -> dict[str, str | int | float] | None:
    if params is None:
        return None

    normalised: dict[str, str | int | float] = {}
    for key, value in params.items():
        normalised[key] = str(value).lower() if isinstance(value, bool) else value
    return normalised
