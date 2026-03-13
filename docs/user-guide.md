# User Guide

## What arles does

`arles` searches the YTS catalogue and then does one of two things:

- prints the best matching torrent URL for each result
- downloads the selected `.torrent` files into a local directory

The selection logic prefers the requested quality when it exists. If it does not, arles falls back to the healthiest torrent by seed count, peer count, and file size.

## Installation

Create a Python 3.11 environment and install the package:

```bash
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .[dev]
```

You can then use either the console script or the legacy root script:

```bash
.venv/bin/arles --help
.venv/bin/python run.py --help
```

## Common commands

Print the selected torrent URL for a search:

```bash
arles --query "the matrix" --quality 2160p --print-only
```

Download the selected torrents into a folder:

```bash
arles --query "the matrix" --quality 2160p --download-torrents --download-dir ./torrents
```

Return JSON instead of human-readable output:

```bash
arles --query "the matrix" --json
```

Mirror output to a log file:

```bash
arles --query "the matrix" --print-only --log-file ./logs/arles.log
```

## Command reference

`--query`
: Search term passed to the YTS `list_movies` endpoint.

`--quality`
: Preferred torrent quality. Examples: `720p`, `1080p`, `2160p`, or `All`.

`--genre`
: Optional genre filter.

`--minimum-rating`
: Numeric rating floor. `0` disables the filter.

`--sort-by`
: One of `date_added`, `title`, `year`, `rating`, `peers`, `seeds`, `download_count`, or `like_count`.

`--order-by`
: Either `asc` or `desc`.

`--page`
: Page number to request from the catalogue.

`--limit`
: Maximum number of movies to fetch.

`--print-only`
: Print results instead of downloading them. This is also the default mode if `--download-torrents` is not provided.

`--download-torrents`
: Download the selected `.torrent` files.

`--download-dir`
: Output directory used in download mode.

`--json`
: Emit JSON for easier scripting.

`--log-file`
: Mirror standard output to a file.

`--verbose`
: Print execution details such as the resolved query parameters.

`--timeout`
: HTTP timeout in seconds.

`--base-url`
: Override the API base URL. This is mainly useful for tests or local stubs.

## Legacy compatibility

The repo still keeps the original top-level modules for callers that import them directly:

- `run.py`
- `yts.py`
- `api.py`
- `session.py`
- `log.py`

New work should prefer the package modules under [`arles/`](../arles).

## Shell utilities

Two helper shell scripts remain in [`bin/process_directory.sh`](../bin/process_directory.sh) and [`bin/process_torrent.sh`](../bin/process_torrent.sh). They are linted with `shellcheck`, but they are optional utilities and are not required for the Python CLI to work.
