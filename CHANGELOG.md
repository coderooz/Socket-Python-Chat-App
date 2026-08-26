# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Professional project scaffolding: `.gitignore`, `.gitattributes`, `.editorconfig`, `pyproject.toml`
- VS Code workspace: `settings.json`, `extensions.json`, `launch.json`, `tasks.json`
- opencode project config: `opencode.jsonc` + `AGENTS.md`
- Docs: `CONTRIBUTING.md`, `SECURITY.md`, `.env.example`
- CI: GitHub Actions `ci.yml` (ruff + mypy + pytest on 3.10 / 3.11 / 3.12)
- Templates: PR template, bug/feature issue templates
- Tooling: `requirements-dev.txt`, `Makefile` helpers
- Tests: initial `tests/` suite with protocol tests

### Changed
- README structure aligned with new layout
- License file populated (MIT)

## [0.1.0] - 2025-09-11

### Added
- Initial release: asyncio server bridging TCP + WebSocket
- Tkinter desktop client (raw TCP + file transfer)
- Browser web client (`web/index.html`)
- JSON-newline protocol with base64 file support
- Single channel `main`
- `CODE_OF_CONDUCT.md`

[Unreleased]: https://github.com/coderooz/Socket-Python-Chat-App/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/coderooz/Socket-Python-Chat-App/releases/tag/v0.1.0
