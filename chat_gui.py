"""
chat_gui.py - iMessage-Style Beautiful GUI
Modern, clean interface with chat bubbles and dark theme
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, font as tkfont
import json
from datetime import datetime
from game_client import TicTacGame
from feature_utils import FeatureManager

class LoginWindow:
    """Login window for entering nickname"""
    
    def __init__(self, callback):
        self.callback = callback
        self.nickname = None
        
        # Create window
        self.window = tk.Tk()
        self.window.title("Chat Login")
        self.window.geometry("450x250")
        self.window.configure(bg='#1c1c1e')
        
        # Center window
        self.center_window()
        
        # Title
        title = tk.Label(
            self.window,
            text="ICS Chat",
            font=("SF Pro Display", 28, "bold"),
            bg='#1c1c1e',
            fg='white',
            pady=20
        )
        title.pack()
        
        # Subtitle
        subtitle = tk.Label(
            self.window,
            text="Enter your nickname to get started",
            font=("SF Pro Text", 12),
            bg='#1c1c1e',
            fg='#8e8e93'
        )
        subtitle.pack()
        
        # Nickname frame
        frame = tk.Frame(self.window, bg='#1c1c1e')
        frame.pack(pady=20)
        
        self.nickname_entry = tk.Entry(
            frame,
            font=("SF Pro Text", 14),
            width=25,
            bg='#2c2c2e',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground='#3a3a3c',
            highlightcolor='#0a84ff'
        )
        self.nickname_entry.pack(ipady=8, padx=5)
        self.nickname_entry.focus()
        self.nickname_entry.bind('<Return>', lambda e: self.on_login())
        
        # Login button
        login_btn = tk.Button(
            self.window,
            text="Continue",
            font=("SF Pro Text", 13, "bold"),
            command=self.on_login,
            bg='#0a84ff',
            fg='white',
            activebackground='#0070e0',
            activeforeground='white',
            relief=tk.FLAT,
            padx=40,
            pady=10,
            cursor='hand2'
        )
        login_btn.pack(pady=15)
        
    def center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_login(self):
        nickname = self.nickname_entry.get().strip()
        
        if not nickname:
            messagebox.showerror("Error", "Please enter a nickname!")
            return
        
        if len(nickname) < 2:
            messagebox.showerror("Error", "Nickname must be at least 2 characters!")
            return
        
        self.nickname = nickname
        self.window.destroy()
        self.callback(nickname)
    
    def run(self):
        self.window.mainloop()
        return self.nickname


class ChatGUI:
    """iMessage-style chat GUI"""
    
    def __init__(self, send_callback, client_name):
        self.send_callback = send_callback
        self.client_name = client_name
        self.peer_name = None
        self.game_window = None
        self.messages = {}
        
        # Initialize feature manager
        try:
            from chat_bot_client import ChatBotClient
            bot_client = ChatBotClient()
        except ImportError:
            from feature_utils import DummyChatBotClient
            bot_client = DummyChatBotClient()
        except Exception as e:
            from feature_utils import DummyChatBotClient
            bot_client = DummyChatBotClient()
        
        self.feature_manager = FeatureManager(bot_client)
        
        # Create main window
        self.window = tk.Tk()
        self.window.title(f"Messages - {client_name}")
        self.window.geometry("900x700")
        self.window.configure(bg='#1c1c1e')
        
        # Set minimum size
        self.window.minsize(600, 500)
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_quit)
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create iMessage-style widgets"""
        
        # Top bar
        top_bar = tk.Frame(self.window, bg='#1c1c1e', height=60)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)
        
        # Contact name
        self.contact_label = tk.Label(
            top_bar,
            text="Not Connected",
            font=("SF Pro Display", 16, "bold"),
            bg='#1c1c1e',
            fg='white'
        )
        self.contact_label.pack(pady=15)
        
        # Status label (smaller, underneath)
        self.status_label = tk.Label(
            top_bar,
            text=f"Logged in as {self.client_name}",
            font=("SF Pro Text", 11),
            bg='#1c1c1e',
            fg='#8e8e93'
        )
        self.status_label.pack()
        
        # Chat area with canvas for bubbles
        chat_container = tk.Frame(self.window, bg='#000000')
        chat_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Canvas and scrollbar for messages
        self.canvas = tk.Canvas(
            chat_container,
            bg='#1c1c1e',
            highlightthickness=0
        )
        
        scrollbar = tk.Scrollbar(
            chat_container,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            bg='#2c2c2e',
            troughcolor='#1c1c1e',
            width=12
        )
        
        self.scrollable_frame = tk.Frame(self.canvas, bg='#1c1c1e')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=900)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Input area
        input_container = tk.Frame(self.window, bg='#1c1c1e')
        input_container.pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=15)
        
        # Input frame with rounded appearance
        input_frame = tk.Frame(input_container, bg='#2c2c2e')
        input_frame.pack(fill=tk.X, pady=5)
        
        # Emoji button
        emoji_btn = tk.Button(
            input_frame,
            text="😀",
            font=("SF Pro Text", 16),
            bg='#2c2c2e',
            fg='white',
            relief=tk.FLAT,
            padx=8,
            command=self.show_emoji_picker,
            cursor='hand2',
            activebackground='#3a3a3c'
        )
        emoji_btn.pack(side=tk.LEFT, padx=5)
        
        # Message entry
        self.message_entry = tk.Entry(
            input_frame,
            font=("SF Pro Text", 13),
            bg='#2c2c2e',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT,
            bd=0
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=5)
        self.message_entry.bind('<Return>', lambda e: self.on_send())
        
        # Send button
        self.send_btn = tk.Button(
            input_frame,
            text="↑",
            font=("SF Pro Text", 18, "bold"),
            bg='#0a84ff',
            fg='white',
            relief=tk.FLAT,
            width=3,
            height=1,
            command=self.on_send,
            cursor='hand2',
            activebackground='#0070e0'
        )
        self.send_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Control buttons at bottom
        control_frame = tk.Frame(self.window, bg='#1c1c1e')
        control_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_style = {
            'font': ("SF Pro Text", 11),
            'bg': '#2c2c2e',
            'fg': 'white',
            'relief': tk.FLAT,
            'padx': 15,
            'pady': 8,
            'cursor': 'hand2',
            'activebackground': '#3a3a3c'
        }
        
        self.connect_btn = tk.Button(
            control_frame,
            text="Connect",
            command=self.on_connect,
            **btn_style
        )
        self.connect_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.game_btn = tk.Button(
            control_frame,
            text="Game",
            command=self.on_start_game,
            state=tk.DISABLED,
            **btn_style
        )
        self.game_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.who_btn = tk.Button(
            control_frame,
            text="Online",
            command=self.on_who,
            **btn_style
        )
        self.who_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
    def add_message_bubble(self, message, is_mine=True, timestamp=None, sender_name=None):
        """Add a message bubble to the chat"""
        
        # Container for message
        msg_container = tk.Frame(self.scrollable_frame, bg='#1c1c1e')
        msg_container.pack(fill=tk.X, padx=10, pady=3)
        
        if is_mine:
            # My messages - blue bubble on right
            bubble_bg = '#0a84ff'
            text_color = 'white'
            anchor = 'e'
        else:
            # Their messages - gray bubble on left
            bubble_bg = '#2c2c2e'
            text_color = 'white'
            anchor = 'w'
        
        # Message bubble
        bubble_frame = tk.Frame(msg_container, bg='#1c1c1e')
        bubble_frame.pack(anchor=anchor)
        
        # Message text
        msg_label = tk.Label(
            bubble_frame,
            text=message,
            font=("SF Pro Text", 13),
            bg=bubble_bg,
            fg=text_color,
            padx=15,
            pady=10,
            wraplength=400,
            justify=tk.LEFT
        )
        msg_label.pack()
        
        # Timestamp
        if timestamp:
            time_label = tk.Label(
                msg_container,
                text=timestamp,
                font=("SF Pro Text", 9),
                bg='#1c1c1e',
                fg='#8e8e93'
            )
            time_label.pack(anchor=anchor, padx=15, pady=1)
        
        # Scroll to bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    
    def add_system_message(self, message, timestamp=None):
        """Add a system message"""
        msg_container = tk.Frame(self.scrollable_frame, bg='#1c1c1e')
        msg_container.pack(fill=tk.X, pady=8)
        
        time_str = f"{timestamp} • " if timestamp else ""
        
        sys_label = tk.Label(
            msg_container,
            text=f"{time_str}{message}",
            font=("SF Pro Text", 11),
            bg='#1c1c1e',
            fg='#8e8e93'
        )
        sys_label.pack()
        
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    
    def show_emoji_picker(self):
        """Show emoji picker popup"""
        emojis = ['😀', '😂', '😍', '😢', '😎', '👍', '❤️', '🔥', '✨', '🎉', 
                  '💯', '👋', '🙏', '💪', '🎮', '🎯', '⚡', '🌟', '💬', '✅']
        
        picker = tk.Toplevel(self.window)
        picker.title("Emojis")
        picker.configure(bg='#2c2c2e')
        picker.geometry("300x200")
        
        frame = tk.Frame(picker, bg='#2c2c2e')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for i, emoji in enumerate(emojis):
            btn = tk.Button(
                frame,
                text=emoji,
                font=("SF Pro Text", 20),
                bg='#2c2c2e',
                fg='white',
                relief=tk.FLAT,
                cursor='hand2',
                command=lambda e=emoji: self.insert_emoji(e, picker)
            )
            btn.grid(row=i//5, column=i%5, padx=5, pady=5)
    
    def insert_emoji(self, emoji, picker_window):
        """Insert emoji into message entry"""
        self.message_entry.insert(tk.END, emoji)
        picker_window.destroy()
        self.message_entry.focus()
    
    def on_send(self):
        """Handle send button click"""
        message = self.message_entry.get().strip()
        
        if not message:
            return
        
        timestamp = datetime.now().strftime("%I:%M %p")
        
        # Check if message is for bot
        if self.feature_manager.process_message_for_bot(
            message,
            lambda response: self.add_message_bubble(response, is_mine=False, timestamp=timestamp, sender_name="Bot")
        ):
            self.add_message_bubble(message, is_mine=True, timestamp=timestamp)
            self.message_entry.delete(0, tk.END)
            return
        
        # Check if it's a game message
        if message.startswith("GAME_"):
            self.send_callback(message)
            self.message_entry.delete(0, tk.END)
            return
        
        # Regular message
        self.add_message_bubble(message, is_mine=True, timestamp=timestamp)
        self.send_callback(message)
        self.message_entry.delete(0, tk.END)
    
    def on_connect(self):
        """Handle connect button click"""
        peer = simpledialog.askstring(
            "Connect",
            "Enter the nickname of the person you want to chat with:",
            parent=self.window
        )
        
        if peer and peer.strip():
            peer = peer.strip()
            self.peer_name = peer
            self.send_callback(f"connect {peer}")
            timestamp = datetime.now().strftime("%I:%M %p")
            self.add_system_message(f"Connecting to {peer}...", timestamp)
            self.connect_btn.config(state=tk.DISABLED)
            self.game_btn.config(state=tk.NORMAL)
    
    def on_start_game(self):
        """Handle start game button click"""
        if not self.peer_name:
            messagebox.showwarning("No Connection", "Please connect to someone first!")
            return
        
        if self.game_window:
            messagebox.showinfo("Game Active", "A game is already in progress!")
            self.game_window.window.lift()
            return
        
        self.game_window = TicTacGame(self.window, self.send_callback, self.peer_name)
        timestamp = datetime.now().strftime("%I:%M %p")
        self.add_system_message("Game started", timestamp)
    
    def on_who(self):
        """Handle who is online button click"""
        self.send_callback("who")
        timestamp = datetime.now().strftime("%I:%M %p")
        self.add_system_message("Checking who's online...", timestamp)
    
    def on_quit(self):
        """Handle quit button click"""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            self.send_callback("q")
            self.window.destroy()
    
    def handle_incoming_message(self, message, sender, timestamp=None, msg_id=None):
        """Handle incoming message from server"""
        if message.startswith("GAME_"):
            if self.game_window:
                self.game_window.receive_move(message)
            return
        
        if not timestamp:
            timestamp = datetime.now().strftime("%I:%M %p")
        
        self.add_message_bubble(message, is_mine=False, timestamp=timestamp, sender_name=sender)
    
    def handle_system_message(self, message):
        """Handle system messages from server"""
        timestamp = datetime.now().strftime("%I:%M %p")
        self.add_system_message(message, timestamp)
        
        if "connected to" in message.lower() and self.peer_name:
            self.contact_label.config(text=self.peer_name)
            self.status_label.config(text="Active now")
        elif "disconnected" in message.lower():
            self.contact_label.config(text="Not Connected")
            self.status_label.config(text=f"Logged in as {self.client_name}")
            self.connect_btn.config(state=tk.NORMAL)
            self.game_btn.config(state=tk.DISABLED)
            self.peer_name = None
    
    def handle_user_list(self, users):
        """Handle online user list"""
        timestamp = datetime.now().strftime("%I:%M %p")
        if users:
            user_str = ", ".join(users)
            self.add_system_message(f"Online: {user_str}", timestamp)
        else:
            self.add_system_message("No other users online", timestamp)
    
    def update_status(self, status):
        """Update status label"""
        self.status_label.config(text=status)
    
    def mark_message_as_seen(self, msg_id):
        """Mark message as seen"""
        pass  # Not needed for iMessage style
    
    def display_message(self, *args, **kwargs):
        """Compatibility method - redirects to bubble"""
        pass
    
    def display_system_message(self, message):
        """Compatibility method"""
        timestamp = datetime.now().strftime("%I:%M %p")
        self.add_system_message(message, timestamp)
    
    def run(self):
        """Start the GUI main loop"""
        self.window.mainloop()