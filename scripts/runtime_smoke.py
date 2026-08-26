"""Runtime smoke test: TCP <-> WS bridge without subprocess."""

import asyncio
import base64
import json
import os
import pathlib
import sys

# ensure project root on sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# use ephemeral ports
TCP_PORT = 28765
WS_PORT = 28766
HOST = "127.0.0.1"

os.environ["HOST"] = HOST
os.environ["TCP_PORT"] = str(TCP_PORT)
os.environ["WS_PORT"] = str(WS_PORT)

# import server after env set (force reload)
if "server" in sys.modules:
    del sys.modules["server"]

# Patch env before import
import server as srv  # noqa: E402

# Override globals if already imported with old values
srv.HOST = HOST
srv.TCP_PORT = TCP_PORT
srv.WS_PORT = WS_PORT


async def tcp_recv_line(reader):
    line = await asyncio.wait_for(reader.readline(), timeout=3)
    return line


async def main():
    # Start server background task
    print(f"Starting server on {HOST} TCP={TCP_PORT} WS={WS_PORT} ...")
    tcp_server = await asyncio.start_server(srv.handle_tcp_client, HOST, TCP_PORT)
    from websockets import serve as ws_serve

    ws_server = await ws_serve(srv.handle_ws, HOST, WS_PORT)
    print("Servers started")

    await asyncio.sleep(0.5)

    # TCP client 1
    reader1, writer1 = await asyncio.open_connection(HOST, TCP_PORT)
    print("TCP client connected")

    # Send join
    join = json.dumps({"type": "join", "username": "tester1", "channel": "main"}) + "\n"
    writer1.write(join.encode())
    await writer1.drain()
    await asyncio.sleep(0.3)
    # Should have received system join back (via broadcast)
    try:
        line = await tcp_recv_line(reader1)
        print("TCP recv after join:", line.decode().strip()[:200])
        assert b"tester1 joined" in line or b"system" in line
        print("[OK] TCP join broadcast ok")
    except Exception as e:
        print("[FAIL] TCP join failed:", e)
        return False

    # WS client
    import websockets

    async with websockets.connect(f"ws://{HOST}:{WS_PORT}") as ws:
        print("WS connected")
        # WS sends message -> TCP should receive
        await ws.send(
            json.dumps(
                {
                    "type": "text",
                    "username": "wsuser",
                    "channel": "main",
                    "message": "hello from ws",
                }
            )
        )
        # Drain WS own echo (server broadcasts to all including sender)
        try:
            echo = await asyncio.wait_for(ws.recv(), timeout=2)
            print("WS drain own echo:", str(echo)[:120])
            assert "hello from ws" in str(echo)
        except Exception as e:
            print("[FAIL] WS echo drain failed:", e)
            return False
        try:
            line2 = await tcp_recv_line(reader1)
            print("TCP recv WS msg:", line2.decode().strip()[:300])
            assert b"hello from ws" in line2
            print("[OK] WS -> TCP ok")
        except Exception as e:
            print("[FAIL] WS->TCP failed:", e)
            return False

        # TCP sends -> WS receives
        writer1.write(
            (
                json.dumps(
                    {
                        "type": "text",
                        "username": "tester1",
                        "channel": "main",
                        "message": "hello from tcp",
                    }
                )
                + "\n"
            ).encode()
        )
        await writer1.drain()
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            print("WS recv TCP msg:", str(msg)[:300])
            assert "hello from tcp" in str(msg)
            print("[OK] TCP -> WS ok")
        except Exception as e:
            print("[FAIL] TCP->WS failed:", e)
            return False

    # File transfer TCP -> TCP (loopback via server)
    reader2, writer2 = await asyncio.open_connection(HOST, TCP_PORT)
    content = b"test file 123 \x00\xff"
    b64 = base64.b64encode(content).decode()
    writer1.write(
        (
            json.dumps(
                {
                    "type": "file",
                    "username": "tester1",
                    "channel": "main",
                    "filename": "test.txt",
                    "data": b64,
                }
            )
            + "\n"
        ).encode()
    )
    await writer1.drain()
    try:
        line3 = await asyncio.wait_for(reader2.readline(), timeout=3)
        obj = json.loads(line3.decode().strip())
        assert obj["type"] == "file"
        assert base64.b64decode(obj["data"]) == content
        print("[OK] File broadcast ok")
    except Exception as e:
        print("[FAIL] File broadcast failed:", e)
        return False
    finally:
        writer2.close()
        await writer2.wait_closed()

    writer1.close()
    await writer1.wait_closed()
    tcp_server.close()
    ws_server.close()
    await tcp_server.wait_closed()
    await ws_server.wait_closed()
    # clear clients
    srv.TCP_CLIENTS.clear()
    srv.WS_CLIENTS.clear()
    print("Servers stopped")
    return True


if __name__ == "__main__":
    ok = asyncio.run(main())
    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
