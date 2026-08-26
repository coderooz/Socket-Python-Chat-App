# Contributing to Socket Python Chat App

Thank you for considering a contribution! This document describes how to set up the project locally and the workflow we use.

## Quick Start

```bash
git clone https://github.com/coderooz/Socket-Python-Chat-App.git
cd Socket-Python-Chat-App

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

pip install -r requirements-dev.txt
```

## Development Workflow

1. **Create a branch** from `main`:

   ```bash
   git checkout -b feat/your-feature
   # or fix/bug-name, chore/task-name
   ```

2. **Make changes** — keep `server.py` / `desktop_client.py` focused. Extract shared logic to `src/` if a file exceeds ~300 lines.

3. **Format & lint** before committing:

   ```bash
   ruff format .
   ruff check --fix .
   mypy .          # optional but recommended
   pytest -v       # must pass
   ```

4. **Commit** using Conventional Commits:

   ```
   feat(server): add rate limiting
   fix(desktop): handle abrupt disconnect
   chore(deps): bump websockets to 12
   docs(readme): clarify env setup
   ```

5. **Push and open a PR** against `main`. Fill in the PR template. CI must pass (lint + tests).

## Branch Naming

- `feat/<short-name>` — new feature
- `fix/<short-name>` — bug fix
- `chore/<short-name>` — tooling, deps, docs
- `docs/<short-name>` — documentation only

`main` is protected — direct pushes are blocked.

## Code Style

- **Formatter:** Ruff `format` (88 cols, double quotes, LF)
- **Linter:** Ruff `check` (isort, pycodestyle, pyflakes, bugbear, etc.)
- **Types:** `mypy` in basic mode — add type hints for new public functions
- **Naming:** `snake_case` for vars/functions, `PascalCase` for classes, `SCREAMING_SNAKE` for constants

VS Code will auto-format on save if you install the recommended extensions (`Extensions` panel → Install recommended).

## Testing

- Tests live in `tests/` (pytest + pytest-asyncio).
- Protocol changes must include tests in `tests/test_protocol.py`.
- Run locally:

  ```bash
  pytest -v
  pytest -v -k protocol
  pytest --cov --cov-report=term-missing
  ```

## Reporting Issues

Use the GitHub issue templates (Bug report / Feature request). Include:

- Steps to reproduce
- Expected vs actual behaviour
- Python version (`python --version`) and OS

## Security

Do **not** open a public issue for security vulnerabilities — see `SECURITY.md`.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
