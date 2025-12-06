"""
chat_gui.py - Ultra Smooth iMessage-Style GUI
With emoji search, message reactions, and message search
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import json
from datetime import datetime
from game_client import TicTacGame
from feature_utils import FeatureManager

class EmojiPicker:
    """Advanced emoji picker with search"""
    
    EMOJIS = {
        'Smileys': ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙'],
        'Gestures': ['👋', '🤚', '🖐', '✋', '🖖', '👌', '🤌', '🤏', '✌', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝', '👍', '👎', '✊', '👊', '🤛', '🤜', '👏', '🙌'],
        'Hearts': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝'],
        'Symbols': ['✨', '⭐', '🌟', '💫', '✅', '❌', '⚡', '🔥', '💯', '🎉', '🎊', '🎈', '🎁', '🏆'],
        'Popular': ['😂', '❤️', '😍', '🔥', '👍', '😊', '🎉', '💯', '✨', '🙏', '😎', '💪', '🎮', '🎯']
    }
    
    def __init__(self, parent, callback):
        self.callback = callback
        self.window = tk.Toplevel(parent)
        self.window.title("Emojis")
        self.window.geometry("500x400")
        self.window.configure(bg='#2c2c2e')
        
        # Search bar
        search_frame = tk.Frame(self.window, bg='#2c2c2e')
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("SF Pro Text", 12),
            bg='#3a3a3c',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT
        )
        search_entry.pack(fill=tk.X, ipady=6)
        search_entry.insert(0, "Search emojis...")
        search_entry.bind('<FocusIn>', lambda e: search_entry.delete(0, tk.END) if search_entry.get() == "Search emojis..." else None)
        
        # Emoji container
        self.emoji_frame = tk.Frame(self.window, bg='#2c2c2e')
        self.emoji_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.show_all_emojis()
    
    def show_all_emojis(self):
        """Display all emojis by category"""
        for widget in self.emoji_frame.winfo_children():
            widget.destroy()
        
        canvas = tk.Canvas(self.emoji_frame, bg='#2c2c2e', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.emoji_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = tk.Frame(canvas, bg='#2c2c2e')
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for category, emojis in self.EMOJIS.items():
            cat_label = tk.Label(scrollable, text=category, font=("SF Pro Text", 11, "bold"), bg='#2c2c2e', fg='#8e8e93')
            cat_label.pack(anchor='w', padx=5, pady=5)
            
            emoji_row = tk.Frame(scrollable, bg='#2c2c2e')
            emoji_row.pack(fill=tk.X, padx=5)
            
            for i, emoji in enumerate(emojis):
                btn = tk.Button(
                    emoji_row, text=emoji, font=("SF Pro Text", 20),
                    bg='#2c2c2e', fg='white', relief=tk.FLAT,
                    cursor='hand2', command=lambda e=emoji: self.select_emoji(e),
                    activebackground='#3a3a3c'
                )
                btn.grid(row=i//10, column=i%10, padx=2, pady=2)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def on_search(self, *args):
        """Filter emojis by search term"""
        search_term = self.search_var.get().lower()
        if not search_term or search_term == "search emojis...":
            return
        
        # Clear and show filtered
        for widget in self.emoji_frame.winfo_children():
            widget.destroy()
        
        filtered_frame = tk.Frame(self.emoji_frame, bg='#2c2c2e')
        filtered_frame.pack(fill=tk.BOTH, expand=True)
        
        # Simple emoji search (you can expand with emoji names)
        all_emojis = []
        for emojis in self.EMOJIS.values():
            all_emojis.extend(emojis)
        
        for i, emoji in enumerate(all_emojis[:50]):  # Show first 50
            btn = tk.Button(
                filtered_frame, text=emoji, font=("SF Pro Text", 24),
                bg='#2c2c2e', relief=tk.FLAT, cursor='hand2',
                command=lambda e=emoji: self.select_emoji(e)
            )
            btn.grid(row=i//10, column=i%10, padx=3, pady=3)
    
    def select_emoji(self, emoji):
        """Select an emoji"""
        self.callback(emoji)
        self.window.destroy()


class MessageSearch:
    """Message search window"""
    
    def __init__(self, parent, messages, select_callback):
        self.messages = messages
        self.select_callback = select_callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("Search Messages")
        self.window.geometry("400x500")
        self.window.configure(bg='#1c1c1e')
        
        # Search bar
        search_frame = tk.Frame(self.window, bg='#1c1c1e')
        search_frame.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(search_frame, text="Search:", font=("SF Pro Text", 12), bg='#1c1c1e', fg='white').pack(anchor='w')
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        
        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=("SF Pro Text", 13), bg='#2c2c2e', fg='white',
            insertbackground='white', relief=tk.FLAT
        )
        search_entry.pack(fill=tk.X, ipady=8)
        search_entry.focus()
        
        # Results
        self.results_frame = tk.Frame(self.window, bg='#1c1c1e')
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=15)
    
    def on_search(self, *args):
        """Search messages"""
        query = self.search_var.get().lower()
        
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not query:
            return
        
        # Search through messages
        results = [(text, data) for text, data in self.messages if query in text.lower()]
        
        if not results:
            tk.Label(self.results_frame, text="No results found", font=("SF Pro Text", 12), bg='#1c1c1e', fg='#8e8e93').pack(pady=20)
            return
        
        for text, data in results[:20]:  # Show first 20
            result_btn = tk.Button(
                self.results_frame, text=text[:50] + "..." if len(text) > 50 else text,
                font=("SF Pro Text", 11), bg='#2c2c2e', fg='white',
                relief=tk.FLAT, anchor='w', padx=10, pady=8,
                command=lambda t=text: self.select_message(t)
            )
            result_btn.pack(fill=tk.X, pady=2)
    
    def select_message(self, text):
        """Select a message from results"""
        self.select_callback(text)
        self.window.destroy()


class ChatGUI:
    """Ultra smooth iMessage-style chat GUI"""
    
    def __init__(self, send_callback, client_name):
        self.send_callback = send_callback
        self.client_name = client_name
        self.peer_name = None
        self.game_window = None
        self.messages = []  # Store (text, data) tuples for search
        self.message_widgets = {}  # Store message widgets for reactions
        
        # Initialize feature manager
        try:
            from chat_bot_client import ChatBotClient
            bot_client = ChatBotClient()
        except:
            from feature_utils import DummyChatBotClient
            bot_client = DummyChatBotClient()
        
        self.feature_manager = FeatureManager(bot_client)
        
        # Create main window
        self.window = tk.Tk()
        self.window.title(f"Messages - {client_name}")
        self.window.geometry("950x750")
        self.window.configure(bg='#1c1c1e')
        self.window.minsize(700, 600)
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_quit)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create ultra smooth widgets"""
        
        # Top bar
        top_bar = tk.Frame(self.window, bg='#2c2c2e', height=70)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)
        
        # Contact info container
        contact_container = tk.Frame(top_bar, bg='#2c2c2e')
        contact_container.pack(expand=True)
        
        # Contact name
        self.contact_label = tk.Label(
            contact_container, text="Not Connected",
            font=("SF Pro Display", 17, "bold"),
            bg='#2c2c2e', fg='white'
        )
        self.contact_label.pack()
        
        # Status
        self.status_label = tk.Label(
            contact_container, text=f"Logged in as {self.client_name}",
            font=("SF Pro Text", 11), bg='#2c2c2e', fg='#8e8e93'
        )
        self.status_label.pack()
        
        # Search button in top bar
        search_btn = tk.Button(
            top_bar, text="🔍", font=("SF Pro Text", 16),
            bg='#2c2c2e', fg='white', relief=tk.FLAT,
            cursor='hand2', command=self.open_search,
            activebackground='#3a3a3c'
        )
        search_btn.place(relx=0.95, rely=0.5, anchor='center')
        
        # Chat area
        chat_container = tk.Frame(self.window, bg='#1c1c1e')
        chat_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for smooth scrolling
        self.canvas = tk.Canvas(chat_container, bg='#1c1c1e', highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_container, orient=tk.VERTICAL, command=self.canvas.yview, bg='#2c2c2e', width=12)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg='#1c1c1e')
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind resize to adjust canvas width
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Input area
        input_container = tk.Frame(self.window, bg='#2c2c2e', height=80)
        input_container.pack(fill=tk.X, side=tk.BOTTOM)
        input_container.pack_propagate(False)
        
        # Centered input frame
        input_center = tk.Frame(input_container, bg='#2c2c2e')
        input_center.pack(expand=True, fill=tk.X, padx=15, pady=15)
        
        # Input with rounded appearance
        input_bg = tk.Frame(input_center, bg='#3a3a3c')
        input_bg.pack(fill=tk.X)
        
        # Emoji button
        emoji_btn = tk.Button(
            input_bg, text="😀", font=("SF Pro Text", 18),
            bg='#3a3a3c', fg='white', relief=tk.FLAT,
            padx=10, command=self.show_emoji_picker,
            cursor='hand2', activebackground='#48484a'
        )
        emoji_btn.pack(side=tk.LEFT)
        
        # Message entry
        self.message_entry = tk.Entry(
            input_bg, font=("SF Pro Text", 14),
            bg='#3a3a3c', fg='white', insertbackground='white',
            relief=tk.FLAT, bd=0
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=10)
        self.message_entry.bind('<Return>', lambda e: self.on_send())
        
        # Send button
        self.send_btn = tk.Button(
            input_bg, text="↑", font=("SF Pro Text", 20, "bold"),
            bg='#0a84ff', fg='white', relief=tk.FLAT,
            width=3, command=self.on_send, cursor='hand2',
            activebackground='#0070e0'
        )
        self.send_btn.pack(side=tk.RIGHT, padx=8, pady=8)
        
        # Control buttons
        control_frame = tk.Frame(self.window, bg='#2c2c2e')
        control_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=8)
        
        btn_style = {'font': ("SF Pro Text", 11), 'bg': '#3a3a3c', 'fg': 'white', 'relief': tk.FLAT, 'padx': 18, 'pady': 9, 'cursor': 'hand2', 'activebackground': '#48484a'}
        
        self.connect_btn = tk.Button(control_frame, text="Connect", command=self.on_connect, **btn_style)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.game_btn = tk.Button(control_frame, text="Game", command=self.on_start_game, state=tk.DISABLED, **btn_style)
        self.game_btn.pack(side=tk.LEFT, padx=5)
        
        self.who_btn = tk.Button(control_frame, text="Online", command=self.on_who, **btn_style)
        self.who_btn.pack(side=tk.LEFT, padx=5)
    
    def on_canvas_resize(self, event):
        """Adjust canvas width on resize"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def add_message_bubble(self, message, is_mine=True, timestamp=None, sender_name=None):
        """Add smooth message bubble"""
        msg_container = tk.Frame(self.scrollable_frame, bg='#1c1c1e')
        msg_container.pack(fill=tk.X, padx=15, pady=4)
        
        # Bubble alignment
        if is_mine:
            bubble_bg = '#0a84ff'
            text_color = 'white'
            anchor = 'e'
        else:
            bubble_bg = '#3a3a3c'
            text_color = 'white'
            anchor = 'w'
        
        # Bubble frame
        bubble_container = tk.Frame(msg_container, bg='#1c1c1e')
        bubble_container.pack(anchor=anchor)
        
        # Message label with better padding
        msg_label = tk.Label(
            bubble_container, text=message,
            font=("SF Pro Text", 14), bg=bubble_bg, fg=text_color,
            padx=16, pady=11, wraplength=450, justify=tk.LEFT
        )
        msg_label.pack()
        
        # Right-click menu for reactions
        msg_label.bind('<Button-2>', lambda e: self.show_message_menu(e, message, msg_label))
        msg_label.bind('<Button-3>', lambda e: self.show_message_menu(e, message, msg_label))
        
        # Store for search
        self.messages.append((message, {'timestamp': timestamp, 'sender': sender_name}))
        self.message_widgets[message] = msg_label
        
        # Timestamp
        if timestamp:
            time_label = tk.Label(
                msg_container, text=timestamp,
                font=("SF Pro Text", 10), bg='#1c1c1e', fg='#8e8e93'
            )
            time_label.pack(anchor=anchor, padx=18, pady=2)
        
        # Smooth scroll to bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    
    def show_message_menu(self, event, message, widget):
        """Show message context menu"""
        menu = tk.Menu(self.window, tearoff=0, bg='#2c2c2e', fg='white', activebackground='#0a84ff')
        
        menu.add_command(label="❤️ React", command=lambda: self.add_reaction(message, widget, '❤️'))
        menu.add_command(label="😂 React", command=lambda: self.add_reaction(message, widget, '😂'))
        menu.add_command(label="👍 React", command=lambda: self.add_reaction(message, widget, '👍'))
        menu.add_separator()
        menu.add_command(label="📋 Copy", command=lambda: self.copy_message(message))
        
        menu.post(event.x_root, event.y_root)
    
    def add_reaction(self, message, widget, emoji):
        """Add reaction to message"""
        current_text = widget.cget("text")
        if emoji not in current_text:
            widget.config(text=f"{current_text} {emoji}")
    
    def copy_message(self, message):
        """Copy message to clipboard"""
        self.window.clipboard_clear()
        self.window.clipboard_append(message)
        self.add_system_message("Message copied!")
    
    def add_system_message(self, message, timestamp=None):
        """Add system message"""
        msg_container = tk.Frame(self.scrollable_frame, bg='#1c1c1e')
        msg_container.pack(fill=tk.X, pady=10)
        
        time_str = f"{timestamp} • " if timestamp else ""
        sys_label = tk.Label(
            msg_container, text=f"{time_str}{message}",
            font=("SF Pro Text", 11), bg='#1c1c1e', fg='#8e8e93'
        )
        sys_label.pack()
        
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    
    def show_emoji_picker(self):
        """Show advanced emoji picker"""
        EmojiPicker(self.window, self.insert_emoji)
    
    def insert_emoji(self, emoji):
        """Insert emoji into message entry"""
        self.message_entry.insert(tk.END, emoji)
        self.message_entry.focus()
    
    def open_search(self):
        """Open message search"""
        MessageSearch(self.window, self.messages, self.highlight_message)
    
    def highlight_message(self, text):
        """Highlight found message"""
        # In a full implementation, would scroll to and highlight the message
        messagebox.showinfo("Found", f"Message: {text[:50]}...")
    
    def on_send(self):
        """Handle send"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        timestamp = datetime.now().strftime("%I:%M %p")
        
        if self.feature_manager.process_message_for_bot(message, lambda r: self.add_message_bubble(r, False, timestamp, "Bot")):
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
            peer = peer.strip()
            self.peer_name = peer
            self.send_callback(f"connect {peer}")
            self.add_system_message(f"Connecting to {peer}...", datetime.now().strftime("%I:%M %p"))
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
        self.add_system_message("Checking online users...", datetime.now().strftime("%I:%M %p"))
    
    def on_quit(self):
        if messagebox.askokcancel("Quit", "Quit?"):
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
            self.status_label.config(text=f"Logged in as {self.client_name}")
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
    
    def display_message(self, *args, **kwargs):
        pass
    
    def display_system_message(self, message):
        self.add_system_message(message, datetime.now().strftime("%I:%M %p"))
    
    def run(self):
        self.window.mainloop()


class LoginWindow:
    """Smooth login window"""
    
    def __init__(self, callback):
        self.callback = callback
        self.nickname = None
        
        self.window = tk.Tk()
        self.window.title("Chat Login")
        self.window.geometry("450x270")
        self.window.configure(bg='#1c1c1e')
        self.center_window()
        
        tk.Label(self.window, text="ICS Chat", font=("SF Pro Display", 30, "bold"), bg='#1c1c1e', fg='white', pady=25).pack()
        tk.Label(self.window, text="Enter your nickname to get started", font=("SF Pro Text", 12), bg='#1c1c1e', fg='#8e8e93').pack()
        
        frame = tk.Frame(self.window, bg='#1c1c1e')
        frame.pack(pady=25)
        
        self.nickname_entry = tk.Entry(frame, font=("SF Pro Text", 15), width=25, bg='#2c2c2e', fg='white', insertbackground='white', relief=tk.FLAT, highlightthickness=1, highlightbackground='#3a3a3c', highlightcolor='#0a84ff')
        self.nickname_entry.pack(ipady=10, padx=5)
        self.nickname_entry.focus()
        self.nickname_entry.bind('<Return>', lambda e: self.on_login())
        
        tk.Button(self.window, text="Continue", font=("SF Pro Text", 14, "bold"), command=self.on_login, bg='#0a84ff', fg='white', activebackground='#0070e0', relief=tk.FLAT, padx=45, pady=12, cursor='hand2').pack(pady=20)
    
    def center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f'+{x}+{y}')
    
    def on_login(self):
        nickname = self.nickname_entry.get().strip()
        if not nickname:
            messagebox.showerror("Error", "Enter a nickname!")
            return
        if len(nickname) < 2:
            messagebox.showerror("Error", "Nickname must be 2+ characters!")
            return
        self.nickname = nickname
        self.window.destroy()
        self.callback(nickname)
    
    def run(self):
        self.window.mainloop()
        return self.nickname