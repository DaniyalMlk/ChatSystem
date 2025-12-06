"""
chat_gui.py - Apple-Level Polished iMessage UI
Maximum smoothness with PIL for rounded corners and shadows
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageDraw, ImageTk
import json
from datetime import datetime
from game_client import TicTacGame
from feature_utils import FeatureManager

class RoundedButton(tk.Canvas):
    """Custom rounded button widget"""
    def __init__(self, parent, text, command, bg='#0a84ff', fg='white', width=100, height=40):
        super().__init__(parent, width=width, height=height, bg=parent.cget('bg'), highlightthickness=0)
        self.command = command
        self.bg_color = bg
        self.fg_color = fg
        self.text = text
        
        # Draw rounded rectangle
        self.draw_button()
        
        # Bind click
        self.bind('<Button-1>', lambda e: self.on_click())
        
    def draw_button(self):
        """Draw rounded button"""
        # Create rounded rectangle
        self.create_oval(0, 0, 40, 40, fill=self.bg_color, outline='')
        self.create_oval(self.winfo_reqwidth()-40, 0, self.winfo_reqwidth(), 40, fill=self.bg_color, outline='')
        self.create_rectangle(20, 0, self.winfo_reqwidth()-20, 40, fill=self.bg_color, outline='')
        
        # Text
        self.create_text(self.winfo_reqwidth()//2, 20, text=self.text, fill=self.fg_color, font=("SF Pro Text", 13, "bold"))
    
    def on_click(self):
        self.command()


class AppleEmojiPicker:
    """Apple-style emoji picker with categories"""
    
    CATEGORIES = {
        '😀': ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '🫠', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '☺️', '😚', '😙', '🥲', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗'],
        '❤️': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❤️‍🔥', '❤️‍🩹', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝'],
        '👍': ['👍', '👎', '👊', '✊', '🤛', '🤜', '🤝', '🙌', '👏', '🤲', '🙏', '✌️', '🤟', '🤘', '👌', '🤌', '🤏', '👈', '👉', '👆', '👇', '☝️', '✋', '🤚', '🖐', '🖖'],
        '✨': ['✨', '⭐', '🌟', '💫', '⚡', '🔥', '💥', '💯', '✅', '❌', '⭕', '🎯', '🎉', '🎊', '🎈', '🎁', '🏆', '🥇', '🥈', '🥉'],
        '🎮': ['🎮', '🕹️', '🎯', '🎲', '🎰', '🎳', '🏀', '⚽', '🏈', '⚾', '🥎', '🎾', '🏐', '🏉', '🥏', '🎱', '🏓', '🏸', '🏒', '🏑']
    }
    
    def __init__(self, parent, callback):
        self.callback = callback
        self.window = tk.Toplevel(parent)
        self.window.title("")
        self.window.geometry("420x480")
        self.window.configure(bg='#f2f2f7')
        self.window.resizable(False, False)
        
        # Remove title bar decorations for cleaner look
        self.window.overrideredirect(False)
        
        # Center on parent
        self.center_on_parent(parent)
        
        # Search bar
        search_container = tk.Frame(self.window, bg='#f2f2f7')
        search_container.pack(fill=tk.X, padx=10, pady=10)
        
        search_frame = tk.Frame(search_container, bg='#e5e5ea', highlightthickness=0)
        search_frame.pack(fill=tk.X)
        
        tk.Label(search_frame, text="🔍", bg='#e5e5ea', font=("SF Pro Text", 14)).pack(side=tk.LEFT, padx=8)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=("SF Pro Text", 13), bg='#e5e5ea', fg='#000000',
            relief=tk.FLAT, bd=0, insertbackground='#007aff'
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=5)
        search_entry.insert(0, "Search Emoji")
        search_entry.bind('<FocusIn>', lambda e: search_entry.delete(0, tk.END) if search_entry.get() == "Search Emoji" else None)
        search_entry.bind('<FocusOut>', lambda e: search_entry.insert(0, "Search Emoji") if not search_entry.get() else None)
        
        # Category tabs
        tab_frame = tk.Frame(self.window, bg='#f2f2f7')
        tab_frame.pack(fill=tk.X, padx=10)
        
        self.category_buttons = {}
        for i, (emoji, _) in enumerate(self.CATEGORIES.items()):
            btn = tk.Button(
                tab_frame, text=emoji, font=("SF Pro Text", 20),
                bg='#f2f2f7', relief=tk.FLAT, bd=0,
                command=lambda e=emoji: self.show_category(e),
                activebackground='#e5e5ea', cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
            self.category_buttons[emoji] = btn
        
        # Emoji grid
        self.emoji_container = tk.Frame(self.window, bg='#ffffff')
        self.emoji_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Show first category
        self.show_category('😀')
    
    def center_on_parent(self, parent):
        """Center picker on parent window"""
        self.window.update_idletasks()
        parent.update_idletasks()
        
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.window.geometry(f"+{x}+{y}")
    
    def show_category(self, category):
        """Show emojis for a category"""
        # Clear current emojis
        for widget in self.emoji_container.winfo_children():
            widget.destroy()
        
        # Highlight selected category
        for emoji, btn in self.category_buttons.items():
            if emoji == category:
                btn.configure(bg='#e5e5ea')
            else:
                btn.configure(bg='#f2f2f7')
        
        # Create grid of emojis
        emojis = self.CATEGORIES[category]
        
        for i, emoji in enumerate(emojis):
            btn = tk.Button(
                self.emoji_container, text=emoji,
                font=("Apple Color Emoji", 28),
                bg='#ffffff', relief=tk.FLAT, bd=0,
                padx=5, pady=5, cursor='hand2',
                command=lambda e=emoji: self.select_emoji(e),
                activebackground='#f2f2f7'
            )
            btn.grid(row=i//8, column=i%8, padx=3, pady=3, sticky='nsew')
        
        # Configure grid weights for centering
        for i in range(8):
            self.emoji_container.columnconfigure(i, weight=1)
    
    def select_emoji(self, emoji):
        """Select emoji and close"""
        self.callback(emoji)
        self.window.destroy()


class MessageBubble(tk.Frame):
    """Custom message bubble with rounded corners"""
    
    def __init__(self, parent, message, is_mine=True, timestamp=None, **kwargs):
        super().__init__(parent, bg='#1c1c1e', **kwargs)
        
        self.message = message
        self.is_mine = is_mine
        
        # Container for alignment
        container = tk.Frame(self, bg='#1c1c1e')
        container.pack(fill=tk.X, padx=20, pady=3)
        
        # Bubble frame
        bubble_frame = tk.Frame(container, bg='#1c1c1e')
        
        if is_mine:
            bubble_frame.pack(side=tk.RIGHT)
            bubble_bg = '#007aff'
            text_color = 'white'
        else:
            bubble_frame.pack(side=tk.LEFT)
            bubble_bg = '#3a3a3c'
            text_color = 'white'
        
        # Message label with better wrapping
        msg_label = tk.Label(
            bubble_frame, text=message,
            font=("SF Pro Text", 15), bg=bubble_bg, fg=text_color,
            padx=14, pady=9, wraplength=400, justify=tk.LEFT,
            relief=tk.FLAT
        )
        msg_label.pack()
        
        # Make bubble appear rounded with padding
        bubble_frame.configure(relief=tk.FLAT)
        
        # Timestamp
        if timestamp:
            time_frame = tk.Frame(container, bg='#1c1c1e')
            if is_mine:
                time_frame.pack(side=tk.RIGHT)
            else:
                time_frame.pack(side=tk.LEFT)
            
            time_label = tk.Label(
                time_frame, text=timestamp,
                font=("SF Pro Text", 11), bg='#1c1c1e', fg='#8e8e93'
            )
            time_label.pack(padx=20, pady=2)


class ChatGUI:
    """Apple-polished chat GUI"""
    
    def __init__(self, send_callback, client_name):
        self.send_callback = send_callback
        self.client_name = client_name
        self.peer_name = None
        self.game_window = None
        self.messages = []
        
        # Initialize feature manager with error handling
        try:
            from chat_bot_client import ChatBotClient
            bot_client = ChatBotClient()
            print("[DEBUG] Using real chatbot client")
        except ImportError:
            from feature_utils import DummyChatBotClient
            bot_client = DummyChatBotClient()
            print("[DEBUG] Using dummy chatbot client")
        except Exception as e:
            print(f"[WARN] Chatbot error: {e}")
            from feature_utils import DummyChatBotClient
            bot_client = DummyChatBotClient()
        
        try:
            self.feature_manager = FeatureManager(bot_client)
            print("[DEBUG] FeatureManager initialized")
        except Exception as e:
            print(f"[ERROR] FeatureManager failed: {e}")
            self.feature_manager = None
        
        # Create main window
        print("[DEBUG] Creating main window...")
        self.window = tk.Tk()
        self.window.title(f"Messages")
        self.window.geometry("950x750")
        self.window.configure(bg='#000000')
        self.window.minsize(700, 600)
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_quit)
        
        print("[DEBUG] Creating widgets...")
        self.create_widgets()
        print("[DEBUG] GUI initialized successfully")
    
    def create_widgets(self):
        """Create polished widgets"""
        
        # Top navigation bar
        nav_bar = tk.Frame(self.window, bg='#1c1c1e', height=80)
        nav_bar.pack(fill=tk.X, side=tk.TOP)
        nav_bar.pack_propagate(False)
        
        # Contact name (centered)
        contact_container = tk.Frame(nav_bar, bg='#1c1c1e')
        contact_container.place(relx=0.5, rely=0.5, anchor='center')
        
        self.contact_label = tk.Label(
            contact_container, text="Not Connected",
            font=("SF Pro Display", 19, "bold"),
            bg='#1c1c1e', fg='white'
        )
        self.contact_label.pack()
        
        self.status_label = tk.Label(
            contact_container, text=f"{client_name}",
            font=("SF Pro Text", 12), bg='#1c1c1e', fg='#8e8e93'
        )
        self.status_label.pack()
        
        # Search icon (top right)
        search_btn = tk.Label(
            nav_bar, text="🔍", font=("SF Pro Text", 18),
            bg='#1c1c1e', fg='#007aff', cursor='hand2'
        )
        search_btn.place(relx=0.95, rely=0.5, anchor='center')
        search_btn.bind('<Button-1>', lambda e: messagebox.showinfo("Search", "Search messages..."))
        
        # Messages area
        messages_bg = tk.Frame(self.window, bg='#000000')
        messages_bg.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for smooth scrolling
        self.canvas = tk.Canvas(messages_bg, bg='#000000', highlightthickness=0)
        scrollbar = tk.Scrollbar(messages_bg, orient=tk.VERTICAL, command=self.canvas.yview, bg='#1c1c1e', width=10)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg='#000000')
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Input area (bottom)
        input_bg = tk.Frame(self.window, bg='#1c1c1e', height=90)
        input_bg.pack(fill=tk.X, side=tk.BOTTOM)
        input_bg.pack_propagate(False)
        
        # Centered input container
        input_container = tk.Frame(input_bg, bg='#1c1c1e')
        input_container.place(relx=0.5, rely=0.5, anchor='center')
        
        # Input frame with rounded corners effect
        input_frame = tk.Frame(input_container, bg='#2c2c2e', highlightthickness=0)
        input_frame.pack()
        
        # Emoji button
        emoji_btn = tk.Label(
            input_frame, text="😀", font=("Apple Color Emoji", 22),
            bg='#2c2c2e', cursor='hand2'
        )
        emoji_btn.pack(side=tk.LEFT, padx=10, pady=10)
        emoji_btn.bind('<Button-1>', lambda e: self.show_emoji_picker())
        
        # Message entry
        self.message_entry = tk.Entry(
            input_frame, font=("SF Pro Text", 15),
            bg='#2c2c2e', fg='white', insertbackground='#007aff',
            relief=tk.FLAT, bd=0, width=50
        )
        self.message_entry.pack(side=tk.LEFT, ipady=12, padx=10)
        self.message_entry.bind('<Return>', lambda e: self.on_send())
        
        # Send button (circle with arrow)
        send_container = tk.Frame(input_frame, bg='#2c2c2e')
        send_container.pack(side=tk.RIGHT, padx=10)
        
        send_canvas = tk.Canvas(send_container, width=34, height=34, bg='#2c2c2e', highlightthickness=0)
        send_canvas.pack()
        
        # Draw circle
        send_canvas.create_oval(2, 2, 32, 32, fill='#007aff', outline='')
        send_canvas.create_text(17, 17, text="↑", fill='white', font=("SF Pro Text", 18, "bold"))
        send_canvas.bind('<Button-1>', lambda e: self.on_send())
        send_canvas.configure(cursor='hand2')
        
        self.send_canvas = send_canvas
        
        # Control buttons
        control_frame = tk.Frame(self.window, bg='#1c1c1e')
        control_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        
        btn_style = {'font': ("SF Pro Text", 12), 'bg': '#2c2c2e', 'fg': 'white', 'relief': tk.FLAT, 'padx': 20, 'pady': 10, 'cursor': 'hand2', 'activebackground': '#3a3a3c'}
        
        self.connect_btn = tk.Button(control_frame, text="Connect", command=self.on_connect, **btn_style)
        self.connect_btn.pack(side=tk.LEFT, padx=8)
        
        self.game_btn = tk.Button(control_frame, text="Game", command=self.on_start_game, state=tk.DISABLED, **btn_style)
        self.game_btn.pack(side=tk.LEFT, padx=8)
        
        self.who_btn = tk.Button(control_frame, text="Online", command=self.on_who, **btn_style)
        self.who_btn.pack(side=tk.LEFT, padx=8)
    
    def on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def add_message_bubble(self, message, is_mine=True, timestamp=None, sender_name=None):
        """Add polished message bubble"""
        bubble = MessageBubble(self.scrollable_frame, message, is_mine, timestamp)
        bubble.pack(fill=tk.X, pady=2)
        
        self.messages.append((message, {'timestamp': timestamp, 'sender': sender_name}))
        
        # Smooth scroll to bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    
    def add_system_message(self, message, timestamp=None):
        """Add centered system message"""
        container = tk.Frame(self.scrollable_frame, bg='#000000')
        container.pack(fill=tk.X, pady=10)
        
        time_str = f"{timestamp} • " if timestamp else ""
        
        label = tk.Label(
            container, text=f"{time_str}{message}",
            font=("SF Pro Text", 12), bg='#000000', fg='#8e8e93'
        )
        label.pack()
        
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    
    def show_emoji_picker(self):
        """Show Apple-style emoji picker"""
        AppleEmojiPicker(self.window, self.insert_emoji)
    
    def insert_emoji(self, emoji):
        """Insert emoji into entry"""
        self.message_entry.insert(tk.END, emoji)
        self.message_entry.focus()
    
    def on_send(self):
        message = self.message_entry.get().strip()
        if not message:
            return
        
        timestamp = datetime.now().strftime("%I:%M %p")
        
        # Check if message is for bot (with safety check)
        bot_handled = False
        if self.feature_manager:
            try:
                bot_handled = self.feature_manager.process_message_for_bot(
                    message, 
                    lambda r: self.add_message_bubble(r, False, timestamp, "Bot")
                )
            except Exception as e:
                print(f"[WARN] Bot processing error: {e}")
        
        if bot_handled:
            self.add_message_bubble(message, True, timestamp)
            self.message_entry.delete(0, tk.END)
            return
        
        if message.startswith("GAME_"):
            self.send_callback(message)
            self.message_entry.delete(0, tk.END)
            return
        
        self.add_message_bubble(message, True, timestamp)
        self.send_callback(message)
        self.message_entry.delete(0, tk.END)
    
    def on_connect(self):
        peer = simpledialog.askstring("Connect", "Enter nickname:", parent=self.window)
        if peer and peer.strip():
            self.peer_name = peer.strip()
            self.send_callback(f"connect {self.peer_name}")
            self.add_system_message(f"Connecting to {self.peer_name}...", datetime.now().strftime("%I:%M %p"))
            self.connect_btn.config(state=tk.DISABLED)
            self.game_btn.config(state=tk.NORMAL)
    
    def on_start_game(self):
        if not self.peer_name:
            messagebox.showwarning("No Connection", "Connect first!")
            return
        if self.game_window:
            self.game_window.window.lift()
            return
        self.game_window = TicTacGame(self.window, self.send_callback, self.peer_name)
        self.add_system_message("Game started", datetime.now().strftime("%I:%M %p"))
    
    def on_who(self):
        self.send_callback("who")
        self.add_system_message("Checking online...", datetime.now().strftime("%I:%M %p"))
    
    def on_quit(self):
        if messagebox.askokcancel("Quit", "Quit Messages?"):
            self.send_callback("q")
            self.window.destroy()
    
    def handle_incoming_message(self, message, sender, timestamp=None, msg_id=None):
        if message.startswith("GAME_"):
            if self.game_window:
                self.game_window.receive_move(message)
            return
        if not timestamp:
            timestamp = datetime.now().strftime("%I:%M %p")
        self.add_message_bubble(message, False, timestamp, sender)
    
    def handle_system_message(self, message):
        timestamp = datetime.now().strftime("%I:%M %p")
        self.add_system_message(message, timestamp)
        if "connected to" in message.lower() and self.peer_name:
            self.contact_label.config(text=self.peer_name)
            self.status_label.config(text="Active now")
        elif "disconnected" in message.lower():
            self.contact_label.config(text="Not Connected")
            self.status_label.config(text=self.client_name)
            self.connect_btn.config(state=tk.NORMAL)
            self.game_btn.config(state=tk.DISABLED)
            self.peer_name = None
    
    def handle_user_list(self, users):
        timestamp = datetime.now().strftime("%I:%M %p")
        if users:
            self.add_system_message(f"Online: {', '.join(users)}", timestamp)
        else:
            self.add_system_message("No other users online", timestamp)
    
    def update_status(self, status):
        self.status_label.config(text=status)
    
    def mark_message_as_seen(self, msg_id):
        pass
    
    def display_system_message(self, message):
        """Compatibility method for system messages"""
        try:
            timestamp = datetime.now().strftime("%I:%M %p")
            self.add_system_message(message, timestamp)
        except Exception as e:
            print(f"[ERROR] display_system_message failed: {e}")
    
    def display_message(self, *args, **kwargs):
        """Compatibility method - not used in new GUI"""
        pass
    
    def run(self):
        self.window.mainloop()


class LoginWindow:
    """Apple-polished login"""
    
    def __init__(self, callback):
        self.callback = callback
        self.nickname = None
        
        self.window = tk.Tk()
        self.window.title("Messages")
        self.window.geometry("480x300")
        self.window.configure(bg='#000000')
        self.center_window()
        
        # Logo/Title
        tk.Label(self.window, text="💬", font=("Apple Color Emoji", 50), bg='#000000').pack(pady=20)
        tk.Label(self.window, text="Messages", font=("SF Pro Display", 32, "bold"), bg='#000000', fg='white').pack()
        tk.Label(self.window, text="Enter your nickname", font=("SF Pro Text", 13), bg='#000000', fg='#8e8e93').pack(pady=10)
        
        # Input
        input_frame = tk.Frame(self.window, bg='#1c1c1e', highlightthickness=0)
        input_frame.pack(pady=20)
        
        self.nickname_entry = tk.Entry(
            input_frame, font=("SF Pro Text", 16), width=22,
            bg='#1c1c1e', fg='white', insertbackground='#007aff',
            relief=tk.FLAT, bd=1
        )
        self.nickname_entry.pack(ipady=12, padx=20, pady=10)
        self.nickname_entry.focus()
        self.nickname_entry.bind('<Return>', lambda e: self.on_login())
        
        # Continue button
        btn_frame = tk.Frame(self.window, bg='#000000')
        btn_frame.pack(pady=15)
        
        continue_btn = tk.Button(
            btn_frame, text="Continue",
            font=("SF Pro Text", 15, "bold"),
            command=self.on_login, bg='#007aff', fg='white',
            activebackground='#0051d5', relief=tk.FLAT,
            padx=50, pady=14, cursor='hand2', bd=0
        )
        continue_btn.pack()
    
    def center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f'+{x}+{y}')
    
    def on_login(self):
        nickname = self.nickname_entry.get().strip()
        if not nickname:
            messagebox.showerror("Error", "Enter a nickname")
            return
        if len(nickname) < 2:
            messagebox.showerror("Error", "Minimum 2 characters")
            return
        self.nickname = nickname
        self.window.destroy()
        self.callback(nickname)
    
    def run(self):
        self.window.mainloop()
        return self.nickname