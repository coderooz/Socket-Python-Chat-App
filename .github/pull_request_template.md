<!-- Please fill in all relevant sections. Delete irrelevant ones. -->

## Summary
<!-- What does this PR do? Link issues with `Fixes #123`. -->

Fixes #

## Changes
- 
- 

## How to test
```bash
pip install -r requirements-dev.txt
ruff check . && ruff format --check .
pytest -v
python server.py  # TCP 8765 + WS 8766
```

## Screenshots / Demo
<!-- If UI changed, add screenshots or a short video. -->

## Checklist
- [ ] `ruff format .` and `ruff check --fix .` pass
- [ ] Tests added/updated and `pytest -v` passes
- [ ] Docs updated (`README.md` / `CHANGELOG.md` / `AGENTS.md` if needed)
- [ ] No secrets committed (`.env` is gitignored)
- [ ] Conventional Commits title (e.g. `feat(server): add rate limiting`)
