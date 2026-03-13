PYTHON ?= .venv/bin/python
PIP ?= $(PYTHON) -m pip
RUFF ?= .venv/bin/ruff
PYRIGHT ?= .venv/bin/pyright
PYTEST ?= .venv/bin/pytest
SHELLCHECK ?= .venv/bin/shellcheck

.PHONY: install lint typecheck unit integration test shellcheck check

install:
	$(PIP) install -e .[dev]

lint:
	$(RUFF) check .

typecheck:
	$(PYRIGHT)

unit:
	$(PYTEST) -m "not integration"

integration:
	$(PYTEST) -m integration

test:
	$(PYTEST)

shellcheck:
	$(SHELLCHECK) bin/process_directory.sh bin/process_torrent.sh .githooks/pre-commit

check: lint typecheck test shellcheck
