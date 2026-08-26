# Architecture

## Overview

This is a single-channel chat system where one `asyncio` server bridges two transport types:

- **Raw TCP** — desktop Tkinter clients (`desktop_client.py`) via `asyncio.start_server` on `TCP_PORT` (default 8765)
- **WebSocket** — browser clients (`web/index.html`) via `websockets` on `WS_PORT` (default 8766)

All clients share channel `main`. Messages are JSON objects terminated by `\n` (TCP) or single WebSocket text frames (WS). The server `broadcast()` fans out every message to both `TCP_CLIENTS` (list) and `WS_CLIENTS` (set).

```
[Tkinter TCP] ──┐
                 ├──► asyncio server (server.py) ──► broadcast ──► all clients
[Browser WS ] ──┘
```

## Protocol

JSON-newline, fields:

- `type`: `join` | `text` | `file` | `leave` | `system`
- `username`, `channel` (`main`), `message` (text/system), `filename`+`data` (file, base64), `timestamp` (ISO 8601)

See `README.md` § Protocol for examples. File payloads are fully buffered — enforce `MAX_FILE_SIZE` if you harden this.

## Server (`server.py`)

- `TCP_CLIENTS: list[dict]` + `WS_CLIENTS: set[WebSocket]` — global mutable state, protected by single-threaded asyncio event loop (no lock needed).
- `handle_tcp_client(reader, writer)` — `readline()` loop, JSON parse, `join` → system broadcast, else attach timestamp and broadcast.
- `handle_ws(ws, path=None)` — `async for msg in ws` loop, same handling (compatible with both websockets v10 and v11 signatures).
- `main()` — starts both listeners on `HOST` (env `HOST`, `TCP_PORT`, `WS_PORT`) and runs forever via `await asyncio.Future()`.

No persistence, no auth, no rate limit — intentional for demo. Add those in `src/middleware/` before exposing beyond localhost.

## Clients

- **Desktop**: Tkinter + `socket` + `threading`. Receiver thread buffers by `\n`, decodes base64 files to `asksaveasfilename`. Hardcoded `SERVER_HOST/PORT` — override via env or `.env.example`.
- **Web**: vanilla `WebSocket` API. `FileReader.readAsDataURL` → base64 split. Download via `data:` URI.

## Configuration

Env overrides (see `.env.example`):

- `HOST` (default `0.0.0.0` server / `127.0.0.1` client)
- `TCP_PORT` (8765), `WS_PORT` (8766), `CHANNEL` (main)

## Extension Points

- Multi-channel: change `CHANNEL` to `channel` routing + UI selector, store `client["channel"]`.
- Persistence: add `src/store.py` with sqlite/mongo, replay on `join`.
- Auth/TLS: JWT check in `handle_ws`/`handle_tcp_client` before register, terminate WS with `wss://` via nginx.
- Chunked files: replace base64 single-frame with chunked `file_start`/`file_chunk`/`file_end`.
