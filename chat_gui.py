import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from feature_utils import FeatureManager
from game_client import TicTacGame
import threading
import json

class GUI:
    def __init__(self, system_args, console=None):
        self.system_args = system_args # contains [server_ip, port]
        self.console = console # Reference to the Client object
        self.feature_manager = FeatureManager()
        self.game_window = None
        
        self.root = tk.Tk()
        self.root.title("Python Chat System")
        self.root.geometry("500x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 1. Login Frame
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(expand=True)
        
        tk.Label(self.login_frame, text="Enter Nickname:", font=("Arial", 12)).pack(pady=5)
        self.entry_name = tk.Entry(self.login_frame, font=("Arial", 12))
        self.entry_name.pack(pady=5)
        self.entry_name.bind("<Return>", self.login)
        tk.Button(self.login_frame, text="Login", command=self.login).pack(pady=10)

        # 2. Main Chat Frame (Hidden initially)
        self.chat_frame = tk.Frame(self.root)
        
        # Chat History
        self.chat_area = scrolledtext.ScrolledText(self.chat_frame, state='disabled', height=20)
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Define Color Tags for Sentiment/AI
        self.chat_area.tag_config('positive', foreground='#00AA00') # Green
        self.chat_area.tag_config('negative', foreground='#FF0000') # Red
        self.chat_area.tag_config('neutral', foreground='black')
        self.chat_area.tag_config('bot_res', foreground='blue')     # Blue for AI
        self.chat_area.tag_config('system', foreground='gray', font=("Arial", 10, "italic"))

        # Input Area
        input_frame = tk.Frame(self.chat_frame)
        input_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.msg_entry = tk.Entry(input_frame, font=("Arial", 12))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", self.send_message)
        
        send_btn = tk.Button(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side=tk.RIGHT, padx=5)

        # Control Buttons
        btn_frame = tk.Frame(self.chat_frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Who is Online", command=self.who_online).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Connect", command=self.connect_peer).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Tic-Tac-Toe", command=self.start_game).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Quit", command=self.on_close).pack(side=tk.LEFT, padx=2)

    def login(self, event=None):
        name = self.entry_name.get()
        if len(name) > 0:
            if self.console.login(name):
                self.login_frame.pack_forget()
                self.chat_frame.pack(fill=tk.BOTH, expand=True)
                self.display_text(f"Welcome {name}! You are logged in.\n", 'system')
            else:
                messagebox.showerror("Error", "Login failed.")

    def send_message(self, event=None):
        msg = self.msg_entry.get()
        if not msg: return
        self.msg_entry.delete(0, tk.END)

        # 1. Check for AI Bot Command
        if self.feature_manager.is_bot_command(msg):
            self.display_text(f"[Me]: {msg}\n", 'neutral')
            # Fetch AI response (this might block slightly, ideally threaded)
            response = self.feature_manager.get_bot_response(msg)
            self.display_text(f"[AI]: {response}\n", 'bot_res')
            return

        # 2. Regular Chat / Commands
        self.console.send_to_server(msg)
        
        # Display my own message locally (if chatting)
        if self.console.sm.get_state() == 2: # S_CHATTING
             self.display_text(f"[Me]: {msg}\n", 'neutral')

    def display_text(self, text, tag='neutral'):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, text, tag)
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    def process_incoming(self, msg_package):
        """
        Called by the receiving thread when data arrives.
        msg_package can be a string (chat) or tuple (GAME_MOVE)
        """
        # Handle Game Move Logic
        if isinstance(msg_package, tuple) and msg_package[0] == "GAME":
            raw_move = msg_package[1] # "GAME_MOVE:4"
            try:
                idx = int(raw_move.split(":")[1])
                if self.game_window and self.game_window.winfo_exists():
                    self.game_window.update_board(idx, 'O') # Opponent is O
                else:
                    # Auto-open game if opponent starts one?
                    self.start_game(is_initiator=False)
                    self.game_window.update_board(idx, 'O')
            except:
                pass
            return # Don't print game moves to chat

        # Handle Standard Chat / System Messages
        lines = msg_package.split('\n')
        for line in lines:
            if not line: continue
            
            # Feature C: Sentiment Analysis on incoming chat
            # We assume chat format is "[User] Message"
            if line.startswith("[") and "]" in line:
                try:
                    parts = line.split("] ", 1)
                    header = parts[0] + "] "
                    content = parts[1]
                    tag, _ = self.feature_manager.get_sentiment_color(content)
                    
                    self.display_text(header, 'neutral') # Name in black
                    self.display_text(content + "\n", tag) # Text in sentiment color
                except:
                    self.display_text(line + "\n", 'neutral')
            else:
                self.display_text(line + "\n", 'system')

    def who_online(self):
        self.console.send_to_server("who")

    def connect_peer(self):
        target = simpledialog.askstring("Connect", "Enter friend's name:")
        if target:
            self.console.send_to_server(f"c {target}")

    def start_game(self, is_initiator=True):
        if self.console.sm.get_state() != 2: # S_CHATTING
            messagebox.showwarning("Wait", "You must be connected to a peer first.")
            return
            
        if self.game_window is None or not self.game_window.winfo_exists():
            # Define the callback to send moves
            def send_game_move(move_str):
                self.console.send_to_server(move_str)
                
            self.game_window = TicTacGame(self.root, send_game_move)
            if is_initiator:
                self.display_text("Game Started! You are X.\n", "system")
            else:
                self.display_text("Game Request received! You are O.\n", "system")

    def on_close(self):
        self.console.quit()
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()