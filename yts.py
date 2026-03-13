"""Compatibility wrapper around the modern CLI."""

from __future__ import annotations

from collections.abc import Mapping

from arles.cli import main


class YTS:
    """Preserve the old `YTS(flags).run()` entry point."""

    def __init__(self, flags: Mapping[str, object], query_string: str = "") -> None:
        self.flags = dict(flags)
        self.query_string = query_string or str(self.flags.get("query_string", ""))

    def run(self) -> int:
        argv = [
            "--quality",
            "2160p",
            "--minimum-rating",
            "7",
            "--sort-by",
            "year",
            "--order-by",
            "desc",
        ]
        if self.query_string:
            argv.extend(["--query", self.query_string])
        if bool(self.flags.get("download_torrents", False)):
            argv.extend(["--download-torrents", "--download-dir", "."])
        else:
            argv.append("--print-only")

        log_filename = str(self.flags.get("log_filename", "") or "")
        if log_filename:
            argv.extend(["--log-file", log_filename])
        if bool(self.flags.get("verbose", False)):
            argv.append("--verbose")

        return main(argv)
