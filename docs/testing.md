# Testing Strategy

## Quality commands

The repo ships with one command that runs the full local quality gate:

```bash
make check
```

That expands to:

```bash
.venv/bin/ruff check .
.venv/bin/pyright
.venv/bin/pytest
.venv/bin/shellcheck bin/process_directory.sh bin/process_torrent.sh .githooks/pre-commit
```

## Unit-testing design

The project structure follows the testing guidance from *Unit Testing: Principles, Practices, and Patterns*:

- business rules live in [`arles/service.py`](../arles/service.py)
- infrastructure concerns live behind boundaries in [`arles/client.py`](../arles/client.py), [`arles/http.py`](../arles/http.py), and [`arles/downloader.py`](../arles/downloader.py)
- unit tests isolate those boundaries with fakes instead of live network traffic
- integration tests cover the seams where separate components work together

That separation keeps the fast feedback loop where it belongs:

- unit tests validate selection logic, orchestration, and filename generation
- integration tests validate the HTTP client, downloader, and CLI wiring together

## Integration tests

Integration tests do not call the live YTS service. Instead they boot a small local HTTP server that returns YTS-shaped payloads and serves fake torrent bytes.

This keeps CI reliable while still proving that:

- `requests` transport works
- JSON parsing works
- the service selects the expected torrent
- the CLI can download a file end to end

Run only integration tests with:

```bash
make integration
```

Run only the fast unit suite with:

```bash
make unit
```

## Recommended workflow

Use `make check` before each push so the local verification path stays consistent.
