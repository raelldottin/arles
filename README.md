# arles

Arles searches the YTS movie catalogue and can either print the best matching torrent URLs or download the corresponding `.torrent` files locally. The project has been rebuilt as a typed Python package with isolated unit tests, local integration tests, and automated quality gates.

## Highlights

- typed client, service, and downloader layers
- CLI that supports print mode, download mode, JSON output, and log mirroring
- legacy top-level entry points kept as compatibility wrappers
- automated `ruff`, `pyright`, `pytest`, and `shellcheck` checks
- unit and integration tests designed around clear infrastructure boundaries

## Installation

Arles targets Python 3.11 or newer.

```bash
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .[dev]
```

## Quick start

Print the selected torrent links:

```bash
arles --query "the matrix" --quality 2160p --print-only
```

Download the selected torrent files:

```bash
arles --query "the matrix" --quality 2160p --download-torrents --download-dir ./torrents
```

Run the legacy root script if you prefer the original entry point:

```bash
.venv/bin/python run.py --query "the matrix" --print-only
```

## Quality gate

Run the full local verification suite with:

```bash
make check
```

That command runs:

- `ruff check .`
- `pyright`
- `pytest`
- `shellcheck bin/process_directory.sh bin/process_torrent.sh .githooks/pre-commit`

## Documentation

- [User guide](docs/user-guide.md)
- [Testing strategy](docs/testing.md)

## Testing philosophy

The codebase is structured to follow the unit-testing guidance from
*Unit Testing: Principles, Practices, and Patterns*:

- pure decision logic lives in [`arles/service.py`](arles/service.py)
- HTTP and filesystem concerns are kept behind explicit boundaries
- unit tests use fakes for fast, isolated feedback
- integration tests exercise real component wiring against a local stub server instead of the live YTS service
