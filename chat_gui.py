"""
chat_gui.py – Complete Tkinter GUI for Chat Client
(unchanged except: added queue-import + queue-poll + packet-router)
"""
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import json
import queue   # <--- NEW
from game_client import TicTacGame
from feature_utils import FeatureManager


class LoginWindow:
    def __init__(self, parent):
        self.nickname = None
        self.window = tk.Toplevel(parent)
        self.window.title("Chat Login")
        self.window.geometry("400x200")
        self.window.transient(parent)
        self.window.grab_set()

        # center
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth()  // 2) - (400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (200 // 2)
        self.window.geometry(f"+{x}+{y}")

        tk.Label(self.window, text="Welcome to ICS Chat", font=("Arial", 18, "bold"), pady=20).pack()
        frm = tk.Frame(self.window)
        frm.pack(pady=20)
        tk.Label(frm, text="Nickname:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.entry = tk.Entry(frm, font=("Arial", 12), width=20)
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self._ok())
        tk.Button(self.window, text="Login", font=("Arial", 12), command=self._ok, width=15).pack(pady=10)

    def _ok(self):
        nick = self.entry.get().strip()
        if not nick:
            messagebox.showerror("Error", "Please enter a nickname!")
            return
        self.nickname = nick
        self.window.destroy()


class ChatGUI:
    def __init__(self, send_callback, client_name):
        self.send_callback = send_callback
        self.client_name = client_name
        self.peer_name   = None
        self.queue       = queue.Queue()   # <--- NEW

        # feature manager (bot + sentiment)
        try:
            from chat_bot_client import ChatBotClient
            bot = ChatBotClient()
        except:
            from feature_utils import DummyChatBotClient
            bot = DummyChatBotClient()
        self.feature_manager = FeatureManager(bot)

        # main window
        self.window = tk.Tk()
        self.window.title(f"ICS Chat – {client_name}")
        self.window.geometry("700x600")
        self.window.protocol("WM_DELETE_WINDOW", self.on_quit)

        self._build_widgets()
        self.window.after(100, self._poll)   # <--- NEW

    # ---------- GUI construction (same as yours) ----------
    def _build_widgets(self):
        top = tk.Frame(self.window, bg='lightblue', height=40)
        top.pack(side=tk.TOP, fill=tk.X)
        self.status_lbl = tk.Label(top, text=f"Logged in as: {self.client_name} | Not connected",
                                   font=("Arial", 10), bg='lightblue', anchor='w')
        self.status_lbl.pack(fill=tk.X, padx=10, pady=10)

        hist = tk.Frame(self.window)
        hist.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tk.Label(hist, text="Chat History", font=("Arial", 11, "bold")).pack(anchor='w')
        self.chat_hist = scrolledtext.ScrolledText(hist, wrap=tk.WORD, font=("Arial", 10),
                                                   state=tk.DISABLED, height=20)
        self.chat_hist.pack(fill=tk.BOTH, expand=True)
        for tag, color in [('green','green'),('red','red'),('blue','blue'),('gray','gray'),
                           ('bold',None)]:
            self.chat_hist.tag_config(tag, foreground=color, font=("Arial", 10, "bold") if tag=='bold' else None)

        inp = tk.Frame(self.window)
        inp.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(inp, text="Message:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.msg_entry = tk.Entry(inp, font=("Arial", 10))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.msg_entry.bind("<Return>", lambda e: self.on_send())
        tk.Button(inp, text="Send", font=("Arial", 10), command=self.on_send, width=10).pack(side=tk.LEFT, padx=5)

        btn_bar = tk.Frame(self.window)
        btn_bar.pack(fill=tk.X, padx=10, pady=10)
        self.conn_btn = tk.Button(btn_bar, text="Connect (Private)", font=("Arial", 10),
                                  command=self.on_connect, width=15)
        self.conn_btn.pack(side=tk.LEFT, padx=5)
        self.game_btn = tk.Button(btn_bar, text="Start Game", font=("Arial", 10),
                                  command=self.on_start_game, width=15, state=tk.DISABLED)
        self.game_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(btn_bar, text="Who is Online", font=("Arial", 10),
                 command=self.on_who, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_bar, text="Quit", font=("Arial", 10),
                 command=self.on_quit, width=15).pack(side=tk.LEFT, padx=5)

    # ---------- message helpers ----------
    def display_message(self, text, sender=None, color=None, tag=None):
        self.chat_hist.config(state=tk.NORMAL)
        if sender:
            self.chat_hist.insert(tk.END, f"{sender}: ", 'bold' if tag=='bold' else ())
        if color or tag:
            self.chat_hist.insert(tk.END, f"{text}\n", color or tag)
        else:
            self.chat_hist.insert(tk.END, f"{text}\n")
        self.chat_hist.config(state=tk.DISABLED)
        self.chat_hist.see(tk.END)

    def display_system(self, text):
        self.display_message(f"[SYSTEM] {text}", color='gray')

    # ---------- button callbacks ----------
    def on_send(self):
        txt = self.msg_entry.get().strip()
        if not txt: return
        self.msg_entry.delete(0, tk.END)

        # bot trigger
        if txt.startswith("@bot "):
            self.display_message(txt, sender="You", color='blue')
            self.feature_manager.process_message_for_bot(
                txt, lambda rsp: self.display_message(rsp, color='blue'))
            return

        # game messages
        if txt.startswith("GAME_"):
            self.send_callback(txt)
            return

        # normal chat
        self.display_message(txt, sender="You")
        self.send_callback(txt)

    def on_connect(self):
        peer = simpledialog.askstring("Connect", "Target nickname:", parent=self.window)
        if peer and peer.strip():
            self.peer_name = peer.strip()
            self.send_callback(f"connect {peer.strip()}")
            self.display_system(f"Connecting to {peer.strip()}...")
            self.conn_btn.config(state=tk.DISABLED)

    def on_start_game(self):
        if not self.peer_name:
            messagebox.showwarning("No peer", "Connect to someone first!")
            return
        if hasattr(self, "game_window") and self.game_window.window.winfo_exists():
            self.game_window.window.lift(); return
        self.game_window = TicTacGame(self.window, self.send_callback, self.peer_name)
        self.display_system("Game window opened!")

    def on_who(self):
        self.send_callback("who")
        self.display_system("Requesting online users...")

    def on_quit(self):
        if messagebox.askokcancel("Quit", "Really quit?"):
            self.send_callback("q")
            self.window.destroy()

    # ---------- network packet router (NEW) ----------
    def _poll(self):
        try:
            while True:
                pkt = self.queue.get_nowait()
                self._handle_packet(pkt)
        except queue.Empty:
            pass
        self.window.after(100, self._poll)

    def _handle_packet(self, data: dict):
        action = data.get("action")
        if action == "exchange":
            sender = data.get("from", "?")
            msg    = data.get("message", "")
            if msg.startswith("GAME_"):
                if hasattr(self, "game_window") and self.game_window:
                    self.game_window.receive_move(msg)
                return
            colour = self.feature_manager.get_sentiment_color(msg)
            self.display_message(msg, sender=sender, color=colour)

        elif action == "list":
            self.handle_user_list(data.get("results", ""))

        elif action == "connect":
            status = data.get("status")
            if status == "request":
                peer = data.get("from")
                self.peer_name = peer
                self.display_system(f"{peer} connected to you")
                self.status_lbl.config(text=f"Logged in as: {self.client_name} | Chatting with {peer}")
                self.game_btn.config(state=tk.NORMAL)

        elif action == "disconnect":
            self.display_system("Peer disconnected")
            self.status_lbl.config(text=f"Logged in as: {self.client_name} | Not connected")
            self.conn_btn.config(state=tk.NORMAL)
            self.game_btn.config(state=tk.DISABLED)
            self.peer_name = None

    # ---------- stubs so your old gui code still works ----------
    def handle_user_list(self, users):
        self.display_system(f"Online users: {users}" if users else "No other users online")

    def run(self):
        self.window.mainloop()