.PHONY: install lint format typecheck test run-server run-web clean help

PY := venv/Scripts/python.exe
ifeq (,$(wildcard $(PY)))
  PY := python
endif

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install dev dependencies
	$(PY) -m pip install -r requirements-dev.txt

lint: ## Ruff check (lint + isort)
	$(PY) -m ruff check .

lint-fix: ## Ruff check --fix
	$(PY) -m ruff check --fix .

format: ## Ruff format
	$(PY) -m ruff format .

typecheck: ## mypy
	$(PY) -m mypy .

test: ## pytest -v
	$(PY) -m pytest -v

test-cov: ## pytest with coverage
	$(PY) -m pytest --cov --cov-report=term-missing

run-server: ## Run asyncio server
	$(PY) server.py

run-web: ## Serve web client on :8000
	$(PY) -m http.server 8000 --directory web

clean: ## Remove caches
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
