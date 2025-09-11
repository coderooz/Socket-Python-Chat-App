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