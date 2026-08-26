# server.py
import asyncio
import datetime
import json
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from websockets import serve as websocket_serve

# Config via env (see .env.example)
HOST = os.getenv("HOST", "0.0.0.0")
TCP_PORT = int(os.getenv("TCP_PORT", "8765"))
WS_PORT = int(os.getenv("WS_PORT", "8766"))
CHANNEL = os.getenv("CHANNEL", "main")

# TCP clients: use a list because dicts are unhashable
TCP_CLIENTS: list[dict] = []
WS_CLIENTS: set = set()


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


async def broadcast(message_json: str):
    """Send message_json (string) to all clients (both TCP and WS)."""
    # TCP clients: write newline-delimited JSON
    for client in list(TCP_CLIENTS):
        try:
            writer = client["writer"]
            writer.write((message_json + "\n").encode())
            await writer.drain()
        except Exception as e:
            print("Error writing to tcp client:", e)
            try:
                TCP_CLIENTS.remove(client)
            except ValueError:
                pass

    # WebSocket clients
    for ws in list(WS_CLIENTS):
        try:
            await ws.send(message_json)
        except Exception as e:
            print("Error writing to ws client:", e)
            WS_CLIENTS.discard(ws)


async def handle_tcp_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    client = {"type": "tcp", "writer": writer, "username": None}
    TCP_CLIENTS.append(client)
    print("TCP client connected", addr)

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            try:
                msg = data.decode().strip()
                obj = json.loads(msg)
            except Exception as e:
                print("Invalid message from", addr, e)
                continue

            # Set username if join
            if obj.get("type") == "join":
                client["username"] = obj.get("username") or f"tcp-{addr}"
                sysmsg = json.dumps(
                    {
                        "type": "system",
                        "username": "__server__",
                        "channel": CHANNEL,
                        "message": f"{client['username']} joined.",
                        "timestamp": now_iso(),
                    }
                )
                await broadcast(sysmsg)
            else:
                # attach timestamp and broadcast
                obj.setdefault("timestamp", now_iso())
                await broadcast(json.dumps(obj))

    except Exception as e:
        print("TCP handler error:", e)

    finally:
        try:
            TCP_CLIENTS.remove(client)
        except ValueError:
            pass
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:  # noqa: S110
            pass
        print("TCP client disconnected", addr)

        # broadcast leave
        if client.get("username"):
            leave = json.dumps(
                {
                    "type": "system",
                    "username": "__server__",
                    "channel": CHANNEL,
                    "message": f"{client['username']} left.",
                    "timestamp": now_iso(),
                }
            )
            await broadcast(leave)


# Accept optional `path` to be compatible with different websockets versions
async def handle_ws(ws, path=None):
    WS_CLIENTS.add(ws)
    print("WS client connected")
    try:
        async for msg in ws:
            try:
                obj = json.loads(msg)
            except Exception as e:
                print("Invalid ws message:", e)
                continue
            obj.setdefault("timestamp", now_iso())
            await broadcast(json.dumps(obj))
    except Exception as e:
        print("WS handler error:", e)
    finally:
        WS_CLIENTS.discard(ws)
        print("WS client disconnected")


async def main():
    msg = (
        f"Starting server (HOST={HOST} "
        f"TCP={TCP_PORT} "
        f"WS={WS_PORT} "
        f"CHANNEL={CHANNEL})..."
    )
    print(msg)
    tcp_server = await asyncio.start_server(handle_tcp_client, HOST, TCP_PORT)
    # websockets.serve will pass either (ws, path) or just (ws) depending on version;
    # our handler accepts an optional `path`.
    _ws_server = await websocket_serve(handle_ws, HOST, WS_PORT)

    addrs = ", ".join(str(sock.getsockname()) for sock in tcp_server.sockets)
    print(f"TCP server listening on {addrs}, WebSocket on {WS_PORT}")

    async with tcp_server:
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped")
