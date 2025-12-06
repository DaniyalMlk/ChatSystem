import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import json
import select
from chat_utils import *
from pacman_client import PacmanGame
from feature_utils import FeatureManager

class GUI:
    def __init__(self, send_func, recv_func, sm, socket):
        self.Window = tk.Tk()
        self.Window.withdraw() # Hide main window until login
        self.send = send_func
        self.recv = recv_func
        self.sm = sm
        self.socket = socket
        self.running = True
        
        # Initialize the Feature Manager (AI & Sentiment)
        self.features = FeatureManager()
        self.game_window = None
        
        # Start Login Process
        self.login()
        
    def login(self):
        self.login_win = tk.Toplevel()
        self.login_win.title("Login")
        self.login_win.geometry("300x150")
        self.login_win.resizable(False, False)
        
        tk.Label(self.login_win, text="Please login to continue", font=("Helvetica", 12)).pack(pady=10)
        
        frame = tk.Frame(self.login_win)
        frame.pack(pady=5)
        
        tk.Label(frame, text="Name: ").pack(side=tk.LEFT)
        self.name_entry = tk.Entry(frame)
        self.name_entry.pack(side=tk.LEFT)
        self.name_entry.focus()
        self.name_entry.bind('<Return>', lambda x: self.do_login())
        
        tk.Button(self.login_win, text="LOGIN", command=self.do_login).pack(pady=10)
        
        self.Window.mainloop()

    def do_login(self):
        name = self.name_entry.get()
        if not name: return
        
        # Send login request
        msg = json.dumps({"action":"login", "name":name})
        self.send(msg)
        
        # Wait for response
        response = json.loads(self.recv())
        
        if response["status"] == "ok":
            self.login_win.destroy()
            self.sm.set_state(S_LOGGEDIN)
            self.sm.set_myname(name)
            self.build_main_window(name)
            
            # Start the receiving thread
            threading.Thread(target=self.proc, daemon=True).start()
        else:
            messagebox.showerror("Login Failed", "Username already in use!")

    def build_main_window(self, name):
        self.Window.deiconify()
        self.Window.title(f"ICS Chat System - {name}")
        self.Window.geometry("500x650")
        self.Window.configure(bg="#2C3E50")
        
        # Header
        head_label = tk.Label(self.Window, bg="#17202A", fg="#EAECEE", text=name, font="Helvetica 13 bold", pady=5)
        head_label.pack(fill=tk.X)
        
        # Chat History
        self.text_area = tk.Text(self.Window, width=20, height=2, bg="#17202A", fg="#EAECEE", font="Helvetica 14", padx=5, pady=5)
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.text_area.config(state=tk.DISABLED)
        
        # Configure Tags for Colors (Sentiment Analysis)
        self.text_area.tag_config("green", foreground="#2ECC71") # Positive
        self.text_area.tag_config("red", foreground="#E74C3C")   # Negative
        self.text_area.tag_config("blue", foreground="#3498DB")  # AI/System
        
        # Scrollbar
        scrollbar = tk.Scrollbar(self.text_area)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.text_area.yview)
        
        # Input Area
        input_frame = tk.Frame(self.Window, bg="#2C3E50")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.msg_entry = tk.Entry(input_frame, font="Helvetica 12")
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.msg_entry.bind("<Return>", self.send_msg)
        
        send_btn = tk.Button(input_frame, text="Send", font="Helvetica 10 bold", command=self.send_msg)
        send_btn.pack(side=tk.RIGHT)
        
        # Buttons Area
        btn_frame = tk.Frame(self.Window, bg="#2C3E50")
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        tk.Button(btn_frame, text="Connect (Private)", command=self.connect_peer).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Start Pacman", command=self.start_pacman).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Who is Online?", command=lambda: self.manual_cmd("who")).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Quit", command=self.on_quit, bg="#C0392B", fg="white").pack(side=tk.RIGHT, padx=2)

    def send_msg(self, event=None):
        msg = self.msg_entry.get()
        self.msg_entry.delete(0, tk.END)
        if not msg: return
        
        # Feature 1 & 3: Check for AI Command or Picture
        text_resp, img_resp = self.features.process_ai_command(msg)
        
        if img_resp:
            self.display_text(f"Me: {msg}")
            self.display_image(img_resp)
            return
        elif text_resp:
            self.display_text(f"Me: {msg}")
            self.display_text(text_resp, "blue")
            return
            
        # Normal Chat
        self.sm.chat(msg)
        self.display_text(f"Me: {msg}")

    def connect_peer(self):
        peer = simpledialog.askstring("Connect", "Enter the name of the user to chat with:")
        if peer:
            self.manual_cmd(f"c {peer}")

    def start_pacman(self):
        peer = simpledialog.askstring("Pacman", "Enter opponent name:")
        if peer:
            # Ensure connection first
            self.sm.connect_to(peer)
            # Launch Game Window (You are Pacman)
            self.game_window = PacmanGame(self.Window, self.send_game_data, peer, "pacman")

    def send_game_data(self, data):
        # Send game move through chat protocol
        self.sm.chat(data)

    def manual_cmd(self, cmd):
        # Handle console commands like 'who', 'c peer'
        self.msg_entry.insert(0, cmd)
        self.send_msg()

    def display_text(self, text, tag=None):
        self.text_area.config(state=tk.NORMAL)
        
        # Feature 2: Sentiment Analysis (If no tag provided)
        if not tag and not text.startswith("Me:"):
            # Check sentiment of the actual message part
            content = text.split(":", 1)[-1]
            tag = self.features.analyze_sentiment(content)
            
        self.text_area.insert(tk.END, text + "\n", tag)
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def display_image(self, img_obj):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.image_create(tk.END, image=img_obj)
        self.text_area.insert(tk.END, "\n")
        self.text_area.config(state=tk.DISABLED)
        # Keep reference to avoid garbage collection
        self.text_area.image = img_obj 

    def proc(self):
        """The main loop handling incoming messages from the server"""
        while self.running:
            try:
                read, _, _ = select.select([self.socket], [], [], 0.1)
                if read:
                    msg = self.recv()
                    if not msg: break
                    
                    # --- GAME LOGIC INTERCEPTION ---
                    try:
                        data = json.loads(msg)
                        # Check if this is a game move
                        if "message" in data and "GAME_MOVE:" in data["message"]:
                            parts = data["message"].split(":")
                            # Format: GAME_MOVE:role:x:y
                            
                            # If I have a game window open, update it
                            if self.game_window:
                                self.Window.after(0, self.game_window.handle_incoming_move, parts[1], parts[2], parts[3])
                            
                            # If I don't have a window, but receive a "pacman" move, I must be the ghost!
                            elif "GAME_MOVE:pacman" in data["message"]:
                                opponent = data["from"].strip("[]")
                                self.Window.after(0, lambda: self.launch_ghost(opponent))
                            continue # Stop here, don't show move in chat
                    except: 
                        pass
                    # -------------------------------

                    # Normal Chat Processing
                    out = self.sm.proc("", msg)
                    if out.strip():
                        # Remove the menu/prompt text to keep GUI clean
                        clean_out = out.replace(menu, "")
                        self.Window.after(0, self.display_text, clean_out)
            except: 
                break

    def launch_ghost(self, opponent):
        # Auto-launch game window as Ghost if opponent starts game
        if not self.game_window:
            self.game_window = PacmanGame(self.Window, self.send_game_data, opponent, "ghost")

    def on_quit(self):
        self.running = False
        try:
            self.socket.close()
        except: pass
        self.Window.destroy()
        exit(0)