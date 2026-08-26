# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < 1.0   | :x:                |

We release from `main` only at the moment — always use the latest commit on `main`.

## Reporting a Vulnerability

If you discover a security vulnerability, please do **not** open a public GitHub issue.

Instead:

1. Email **contact@coderooz.in** with subject `Security: Socket Python Chat App`.
2. Include: description, steps to reproduce, impact, and (if possible) a suggested fix or PoC.
3. Allow up to **72 hours** for an initial response. We will coordinate a fix and disclosure timeline with you.

We follow coordinated disclosure — please give us a reasonable window to patch before publishing details.

## Known Limitations (not vulnerabilities)

This is a demonstration project without production hardening:

- No authentication — anyone who can reach the TCP/WS ports can join.
- No rate limiting or spam protection.
- No encryption in transit — `ws://` / raw TCP, not TLS. Use a reverse proxy (e.g. nginx + `wss://`) if exposing beyond localhost.
- File payloads are fully buffered + base64-encoded — not suitable for large files and may exhaust memory.

If you deploy this beyond a local demo, put it behind TLS + auth and validate/enforce file-size limits.

## Hardening Checklist (for deployers)

- [ ] Bind `HOST` to `127.0.0.1` or a private network, not `0.0.0.0`, unless behind a firewall.
- [ ] Terminate TLS at a reverse proxy and expose `wss://` only.
- [ ] Add authentication (e.g. token / JWT) before `join`.
- [ ] Enforce `MAX_FILE_SIZE` and reject oversized `data` fields.
- [ ] Add rate limiting per IP / per user.

Thank you for helping keep the project and its users safe.
