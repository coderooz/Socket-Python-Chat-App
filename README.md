# Python Socket + Tkinter Chat App

A simple multi-client chat application with **desktop (Tkinter)** and **web (browser)** clients. The server supports both **raw TCP socket clients** (desktop) and **WebSocket clients** (browser) and relays messages between them in a shared chat channel. Text and file transfer are supported using a small JSON message protocol with base64 encoding for files.

---

## Features

* Single channel (chat group) supporting multiple members.
* Desktop client built with Tkinter (Python) using raw TCP sockets.
* Web client (browser) using WebSocket protocol.
* Server written in Python `asyncio` that accepts both TCP and WebSocket connections and broadcasts messages between all connected clients.
* Send text messages and files (files are base64-encoded and delivered to all clients).
* Simple, clear UI for both desktop and web clients.

---

## Project Structure

```
python-tk-socket-chat/
├── README.md           # This documentation
├── server.py           # Central server (asyncio) - accepts TCP + WebSocket
├── desktop_client.py   # Tkinter desktop client (TCP socket)
├── web/
│   ├── index.html      # Browser UI + JS WebSocket client
│   └── static/         # optional folder for JS/CSS
├── requirements.txt
└── LICENSE
```

---

## Protocol (JSON-over-socket)

All messages are JSON strings followed by a newline (`\n`). Each JSON object has at least these fields:

* `type` — `join` | `text` | `file` | `leave` | `system`
* `username` — sender's display name
* `channel` — chat channel name (we use `main` by default)
* `message` — for `text` and `system` messages
* `filename` & `data` — for `file` messages; `data` is base64-encoded file bytes
* `timestamp` — ISO 8601 timestamp (optional)

Examples:

Text message:

```json
{"type":"text","username":"alice","channel":"main","message":"hello everyone"}
```

File message (shortened):

```json
{"type":"file","username":"bob","channel":"main","filename":"cat.png","data":"iVBORw0KG..."}
```

Join message (sent when client connects):

```json
{"type":"join","username":"alice","channel":"main"}
```

---

## Server: `server.py`

This server uses `asyncio` and the `websockets` library to accept WebSocket clients and `asyncio`'s TCP server to accept raw socket clients. It tracks connected clients and relays messages between them.

> Requirements: Python 3.8+ (3.10+ recommended), `websockets` library.

```python
# server.py
import asyncio
import json
import datetime
from websockets import serve as websocket_serve

# TCP clients: use a list because dicts are unhashable
TCP_CLIENTS = []
WS_CLIENTS = set()
CHANNEL = "main"

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
        except Exception:
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
    print("Starting server...")
    tcp_server = await asyncio.start_server(handle_tcp_client, "0.0.0.0", 8765)
    # websockets.serve will pass either (ws, path) or just (ws) depending on version;
    # our handler accepts an optional `path`.
    ws_server = await websocket_serve(handle_ws, "0.0.0.0", 8766)

    addrs = ", ".join(str(sock.getsockname()) for sock in tcp_server.sockets)
    print(f"TCP server listening on {addrs}, WebSocket on 8766")

    async with tcp_server:
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped")

```

**Notes:**

* TCP server: port **8765** — for desktop client using raw sockets.
* WebSocket server: port **8766** — for browser clients using the WebSocket API.
* Messages are forwarded between both pools so clients on different protocols share the same chat.

---

## Desktop client: `desktop_client.py` (Tkinter + raw sockets)

This is a simple Tkinter GUI. It connects to the TCP server on port 8765 and sends/receives JSON messages as described in the protocol. Files are sent base64 encoded.

```python
# desktop_client.py
import socket
import threading
import json
import base64
import tkinter as tk
from tkinter import scrolledtext, filedialog, simpledialog, messagebox
import time

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8765
BUFFER = 4096
CHANNEL = 'main'

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title('Tk Chat')
        self.username = simpledialog.askstring('Username', 'Enter display name', parent=root) or f'user-{int(time.time()%1000)}'

        top = tk.Frame(root)
        tk.Label(top, text=f'User: {self.username}').pack(side=tk.LEFT)
        tk.Button(top, text='Send File', command=self.send_file).pack(side=tk.RIGHT)
        top.pack(fill=tk.X)

        self.txt = scrolledtext.ScrolledText(root, state='disabled', height=20)
        self.txt.pack(fill=tk.BOTH, expand=True)

        bottom = tk.Frame(root)
        self.entry = tk.Entry(bottom)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind('<Return>', lambda e: self.send_text())
        tk.Button(bottom, text='Send', command=self.send_text).pack(side=tk.RIGHT)
        bottom.pack(fill=tk.X)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((SERVER_HOST, SERVER_PORT))
        except Exception as e:
            messagebox.showerror('Connection Error', str(e))
            root.destroy()
            return

        # start receiver thread
        self.running = True
        t = threading.Thread(target=self.receiver, daemon=True)
        t.start()

        # send join message
        join = json.dumps({'type':'join','username':self.username,'channel':CHANNEL})
        self.sock.sendall((join + '\n').encode())

        root.protocol('WM_DELETE_WINDOW', self.on_close)

    def append(self, text):
        self.txt['state'] = 'normal'
        self.txt.insert(tk.END, text + '\n')
        self.txt.yview(tk.END)
        self.txt['state'] = 'disabled'

    def receiver(self):
        buff = b''
        while self.running:
            try:
                data = self.sock.recv(BUFFER)
                if not data:
                    break
                buff += data
                while b'\n' in buff:
                    line, buff = buff.split(b'\n', 1)
                    try:
                        obj = json.loads(line.decode())
                        self.handle_msg(obj)
                    except Exception as e:
                        print('Invalid message', e)
            except Exception as e:
                print('Receiver error', e)
                break
        self.running = False

    def handle_msg(self, obj):
        t = obj.get('type')
        if t == 'text' or t == 'system':
            user = obj.get('username')
            msg = obj.get('message')
            ts = obj.get('timestamp','')
            self.root.after(0, lambda: self.append(f'[{user}] {msg}'))
        elif t == 'file':
            user = obj.get('username')
            fname = obj.get('filename')
            data = obj.get('data')
            # ask to save
            def ask_save():
                path = filedialog.asksaveasfilename(initialfile=fname)
                if path:
                    with open(path, 'wb') as f:
                        f.write(base64.b64decode(data))
                    messagebox.showinfo('Saved', f'Saved file to {path}')
                self.append(f'[{user}] sent file: {fname} (saved: {bool(path)})')
            self.root.after(0, ask_save)

    def send_text(self):
        text = self.entry.get().strip()
        if not text:
            return
        obj = {'type':'text','username':self.username,'channel':CHANNEL,'message':text}
        try:
            self.sock.sendall((json.dumps(obj) + '\n').encode())
            self.entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror('Send error', str(e))

    def send_file(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        with open(path, 'rb') as f:
            data = base64.b64encode(f.read()).decode()
        fname = path.split('/')[-1]
        obj = {'type':'file','username':self.username,'channel':CHANNEL,'filename':fname,'data':data}
        try:
            self.sock.sendall((json.dumps(obj) + '\n').encode())
            self.append(f'[you] sent file: {fname}')
        except Exception as e:
            messagebox.showerror('Send error', str(e))

    def on_close(self):
        try:
            leave = json.dumps({'type':'leave','username':self.username,'channel':CHANNEL})
            self.sock.sendall((leave + '\n').encode())
        except: pass
        self.running = False
        try:
            self.sock.close()
        except: pass
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
```

**Notes:**

* Desktop client connects to `SERVER_HOST:8765`. Modify `SERVER_HOST` if server runs elsewhere.
* Incoming file messages trigger a file-save dialog.

---

## Web client: `web/index.html`

A lightweight HTML+JS client using the browser WebSocket API to connect to the server's WebSocket port (8766). It implements the same JSON protocol and presents a simple, clean UI.

```html
<!-- web/index.html -->
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Web Chat</title>
  <style>
    body{font-family:system-ui,Arial;margin:0;display:flex;flex-direction:column;height:100vh}
    header{padding:12px;background:#111;color:#fff}
    #chat{flex:1;overflow:auto;padding:12px;background:#f6f6f6}
    #inputBar{display:flex;padding:8px}
    #msg{flex:1;padding:8px}
    .msg{margin:6px 0;padding:8px;border-radius:6px;background:white;box-shadow:0 1px 2px rgba(0,0,0,0.05)}
    .meta{font-size:12px;color:#666}
  </style>
</head>
<body>
  <header>
    <span id="me">Web User</span>
  </header>
  <div id="chat"></div>
  <div id="inputBar">
    <input id="msg" placeholder="Type a message" />
    <input type="file" id="file" />
    <button id="send">Send</button>
  </div>

<script>
  const WS_URL = 'ws://' + location.hostname + ':8766'; // adjust host if needed
  let username = prompt('Enter display name') || 'web-' + Math.floor(Math.random()*1000);
  document.getElementById('me').textContent = username;

  const ws = new WebSocket(WS_URL);
  const chat = document.getElementById('chat');
  const msgInput = document.getElementById('msg');
  const fileInput = document.getElementById('file');

  function addMessage(text){
    const d = document.createElement('div'); d.className='msg'; d.innerHTML = text; chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
  }

  ws.onopen = () => {
    const join = {type:'join',username:username,channel:'main'};
    ws.send(JSON.stringify(join));
  }

  ws.onmessage = (e) => {
    try{
      const obj = JSON.parse(e.data);
      if(obj.type === 'text' || obj.type === 'system'){
        addMessage(`<div class="meta">${obj.username}</div><div>${obj.message}</div>`);
      } else if(obj.type === 'file'){
        const link = document.createElement('a');
        link.href = 'data:application/octet-stream;base64,' + obj.data;
        link.download = obj.filename;
        link.textContent = `${obj.username} sent file: ${obj.filename} (click to download)`;
        const wrapper = document.createElement('div'); wrapper.className='msg'; wrapper.appendChild(link); chat.appendChild(wrapper);
      }
    }catch(err){console.error(err)}
  }

  document.getElementById('send').addEventListener('click', send);
  msgInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter') send(); });

  function send(){
    const text = msgInput.value.trim();
    if(text){
      ws.send(JSON.stringify({type:'text',username:username,channel:'main',message:text}));
      msgInput.value = '';
    } else if(fileInput.files.length){
      const f = fileInput.files[0];
      const reader = new FileReader();
      reader.onload = () => {
        const b64 = reader.result.split(',')[1];
        ws.send(JSON.stringify({type:'file',username:username,channel:'main',filename:f.name,data:b64}));
        fileInput.value = '';
      };
      reader.readAsDataURL(f); // results like data:...;base64,AAA
    }
  }
</script>
</body>
</html>
```

**Hosting the web client for local testing:**

* Serve the `web/` folder via any simple static server (e.g. `python -m http.server 8000` in the `web/` directory) and then open `http://localhost:8000/index.html` in your browser.
* The page connects to `ws://<host>:8766`. If you open the page from a different machine, adjust the WebSocket URL accordingly.

---

## Requirements (`requirements.txt`)

```
websockets>=10.0
```

(Desktop and web clients use only Python stdlib modules.)

---

## Installation & Run (quick)

1. Clone the repo.

2. Create a virtualenv (recommended) and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # mac/linux
venv\Scripts\Activate     # windows
pip install -r requirements.txt
```

3. Run the server:

```bash
python server.py
```

You should see the server start and listen on TCP port 8765 and WebSocket 8766.

4. Start the desktop client (on the same or another machine):

```bash
python desktop_client.py
```

5. Start the web client: serve `web/` statically and open `web/index.html` in a browser. For local testing:

```bash
cd web
python -m http.server 8000
# open http://localhost:8000 in your browser
```

6. Test:

* Desktop client can send text and files; browser client receives them. Browser can upload files (base64) and desktop clients can save them.

---

## Security & Limitations

* This is a demonstration project. Do **not** expose the server to the public internet without TLS and authentication.
* Files are fully loaded into memory and sent base64-encoded — not suitable for very large files.
* No authentication, rate-limiting, or spam protection.
* WebSocket endpoint is plain `ws://`. For production, use `wss://` behind TLS.

---

## Extending the Project (ideas)

* Add channels/rooms and UI to select rooms.
* Add persistent message history (database) and message retrieval on join.
* Replace the simple TCP protocol with `socket.io` for richer features, reconnection, and namespaces.
* Add authentication (JWT) and TLS support for secure transport.
* Chunked file upload for very large files.

---

## License

MIT

