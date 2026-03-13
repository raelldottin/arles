"""Logging helpers for mirroring stdout to a file."""

from __future__ import annotations

import sys
from contextlib import AbstractContextManager, redirect_stdout
from pathlib import Path
from typing import TextIO


class _TeeWriter:
    def __init__(self, primary: TextIO, secondary: TextIO) -> None:
        self._primary = primary
        self._secondary = secondary

    def write(self, text: str) -> int:
        self._primary.write(text)
        self._secondary.write(text)
        return len(text)

    def flush(self) -> None:
        self._primary.flush()
        self._secondary.flush()


class LogFile(AbstractContextManager["LogFile"]):
    """Context manager that mirrors stdout into a log file."""

    def __init__(self, filename: str | Path) -> None:
        self._path = Path(filename)
        self._handle: TextIO | None = None
        self._redirect: AbstractContextManager[object] | None = None

    def __enter__(self) -> LogFile:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self._path.open("w", encoding="utf-8")
        self._redirect = redirect_stdout(_TeeWriter(sys.stdout, self._handle))
        self._redirect.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._redirect is not None:
            self._redirect.__exit__(exc_type, exc_value, traceback)
        if self._handle is not None:
            self._handle.close()
        self._redirect = None
        self._handle = None
