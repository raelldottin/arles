"""Application exceptions."""


class ArlesError(Exception):
    """Base exception for project-specific failures."""


class YTSAPIError(ArlesError):
    """Raised when the remote API returns an invalid payload."""
