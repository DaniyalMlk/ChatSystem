#!/usr/bin/env python3
"""
One-file, non-blocking GUI client.
- Opens the socket  
- Shows the login box  
- Starts the receiver thread  
- Hands every incoming JSON to the GUI queue  
- Lets Tk do the rest.
"""
import socket, threading, json, sys, os
import tkinter as tk
from chat_utils import mysend, myrecv
from chat_gui import LoginWindow, ChatGUI   # we keep YOUR gui file

class Client:
    def __init__(self, host=None, port=None):
        self.host = host or os.getenv("CHAT_SERVER_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("CHAT_SERVER_PORT", "1112"))
        self.name = ""
        self.sock = None
        self.gui = None
        self.running = False

    # ------------------------------------------------------
    def start(self):
        # 1. connect TCP
        self.sock = socket.socket()
        try:
            self.sock.connect((self.host, self.port))
        except Exception as e:
            print("Socket error:", e); return

        # 2. login dialog
        root = tk.Tk(); root.withdraw()
        lw = LoginWindow(root)
        root.wait_window(lw.window)
        if not lw.nickname:
            return
        self.name = lw.nickname

        # 3. send login request  (server expects {"action":"login","name":...})
        mysend(self.sock, json.dumps({"action":"login","name":self.name}))

        # 4. wait for server reply  (blocks, but we are not in Tk yet)
        reply = json.loads(myrecv(self.sock))
        if reply.get("status") != "ok":
            print("Login failed:", reply.get("message","?"))
            return
        print("Logged in as", self.name)

        # 5. build real GUI
        self.gui = ChatGUI(self._send, self.name)
        self.gui.sock = self.sock          # give gui access so it can close socket
        self.running = True

        # 6. receiver thread
        threading.Thread(target=self._recv_loop, daemon=True).start()

        # 7. Tk main-loop (blocks until window dies)
        self.gui.run()
        self.stop()

    # ------------------------------------------------------
    def _send(self, payload:str):
        """Called by GUI buttons/entry – ships raw text to server."""
        if not self.running: return
        # wrap in the format the server expects
        mysend(self.sock, json.dumps({"action":"exchange","message":payload}))

    # ------------------------------------------------------
    def _recv_loop(self):
        """Forever read → push into GUI queue."""
        while self.running:
            try:
                raw = myrecv(self.sock)
                if not raw: raise ConnectionResetError
                self.gui.queue.put(json.loads(raw))
            except:
                self.gui.queue.put({"action":"disconnect"})
                break

    # ------------------------------------------------------
    def stop(self):
        self.running = False
        try: self.sock.close()
        except: pass


# ------------------------------------------------------------------
if __name__ == "__main__":
    Client().start()