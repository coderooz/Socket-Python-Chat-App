# AGENTS.md — Socket Python Chat App

> Project-specific instructions for AI agents (opencode, Cursor, Copilot) and human contributors.

## Project Overview
A multi-client chat app: Python `asyncio` server bridges **raw TCP (desktop Tkinter)** and **WebSocket (browser)** clients. Single channel `main`, JSON-newline protocol, base64 file transfer.

- **Author:** Ranit Saha (Coderooz) — contact@coderooz.in
- **Repo:** https://github.com/coderooz/Socket-Python-Chat-App
- **License:** MIT

## Tech Stack
| Layer | Choice |
|-------|--------|
| Language | Python 3.10+ |
| Server | asyncio + websockets>=10.0 |
| Desktop | Tkinter (stdlib) + socket + threading |
| Web | vanilla HTML/CSS/JS + WebSocket API |
| Lint/Format | Ruff (88 chars) |
| Types | mypy (optional) |
| Tests | pytest + pytest-asyncio |

## Directory Structure
```
.
├── server.py               # asyncio server (TCP 8765 + WS 8766)
├── desktop_client.py       # Tkinter desktop client
├── web/
│   ├── index.html          # WebSocket browser client
│   └── static/             # optional JS/CSS
├── tests/                  # pytest suite
├── scripts/                # dev helpers
├── .vscode/                # editor config (settings, launch, tasks)
├── .opencode/              # opencode agents/skills (project-local)
├── .github/workflows/      # CI
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml          # ruff/mypy/pytest config
├── .env.example
├── AGENTS.md               # this file
└── README.md
```

## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements-dev.txt   # dev (includes lint/test)
# or pip install -r requirements.txt # prod minimal
```

## Running
```bash
python server.py                  # TCP 8765 + WS 8766
python desktop_client.py          # Tkinter GUI
python -m http.server 8000 --directory web  # web client at http://localhost:8000
```

Ports are configurable via env: `TCP_PORT`, `WS_PORT`, `HOST` (see `.env.example`).

## Conventions
- **Formatting:** Ruff, 88 cols, double quotes, LF. Run `ruff format .` and `ruff check --fix .` before commit.
- **Imports:** isort via Ruff (stdlib → third-party → local).
- **Naming:** `snake_case` for vars/functions, `PascalCase` for classes, `SCREAMING_SNAKE` for constants.
- **Commits:** Conventional Commits — `feat(server): add rate limiting`, `fix(desktop): handle disconnect`.
- **Branches:** `main` is protected; feature branches `feat/`, `fix/`, `chore/`.

## Code Guidelines
- Keep `server.py` / `desktop_client.py` focused; extract shared logic to `src/` if the file exceeds ~300 lines.
- Prefer `asyncio` primitives over threading in server code.
- Never commit secrets; use `.env` (gitignored) and `.env.example` as template.
- Add tests for new protocol fields (`tests/test_protocol.py`).

## Testing
```bash
pytest -v                 # all tests
pytest -v -k protocol     # filter
ruff check . && mypy .    # lint + types
```

## VS Code
- Recommended extensions auto-prompted via `.vscode/extensions.json`.
- Launch configs: `Server`, `Desktop Client`, `Pytest`, `Current File` (Run & Debug panel).
- Tasks: `install`, `lint`, `format`, `typecheck`, `test`, `run:server`, `run:web` (Terminal → Run Task).

## opencode
- Project config: `opencode.jsonc` (model, formatter, LSP, watcher).
- Project agents/skills live in `.opencode/`; global config in `~/.config/opencode/opencode.json`.
- Run `opencode --help` or `/help` inside opencode TUI.

## Security Notes
- No auth/rate-limit yet; do not expose directly to internet without TLS + auth.
- File payloads are fully buffered + base64 — not for large files; validate size.
- See `SECURITY.md` for disclosure policy.

## What Not To Do
- Do not push to `main` without review; open a PR.
- Do not add heavy dependencies without discussion (prefer stdlib).
- Do not modify `.vscode/settings.json` editor defaults without team sync.
