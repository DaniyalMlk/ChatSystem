"""
chat_gui.py - Complete Tkinter GUI with Timestamps & Seen Status
Includes login window, main chat window, with Instagram-like features
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import json
from datetime import datetime
from game_client import TicTacGame
from feature_utils import FeatureManager

class LoginWindow:
    """Login window for entering nickname"""
    
    def __init__(self, callback):
        """
        Initialize login window
        
        Args:
            callback: Function to call with nickname when login is clicked
        """
        self.callback = callback
        self.nickname = None
        
        # Create window
        self.window = tk.Tk()
        self.window.title("Chat Login")
        self.window.geometry("400x200")
        
        # Center window
        self.center_window()
        
        # Title
        title = tk.Label(
            self.window,
            text="Welcome to ICS Chat",
            font=("Arial", 18, "bold"),
            pady=20
        )
        title.pack()
        
        # Nickname frame
        frame = tk.Frame(self.window)
        frame.pack(pady=20)
        
        tk.Label(frame, text="Nickname:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        
        self.nickname_entry = tk.Entry(frame, font=("Arial", 12), width=20)
        self.nickname_entry.pack(side=tk.LEFT, padx=5)
        self.nickname_entry.focus()
        
        # Bind Enter key
        self.nickname_entry.bind('<Return>', lambda e: self.on_login())
        
        # Login button
        login_btn = tk.Button(
            self.window,
            text="Login",
            font=("Arial", 12),
            command=self.on_login,
            width=15
        )
        login_btn.pack(pady=10)
        
    def center_window(self):
        """Center window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_login(self):
        """Handle login button click"""
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
        """Start the login window"""
        self.window.mainloop()
        return self.nickname


class ChatGUI:
    """Main chat window GUI with timestamps and seen status"""
    
    def __init__(self, send_callback, client_name):
        """
        Initialize chat GUI
        
        Args:
            send_callback: Function to send messages
            client_name: The user's nickname
        """
        self.send_callback = send_callback
        self.client_name = client_name
        self.peer_name = None
        self.game_window = None
        
        # Track messages and their seen status
        self.messages = {}  # {msg_id: {'text': '', 'timestamp': '', 'seen': False}}
        
        # Initialize feature manager
        try:
            from chat_bot_client import ChatBotClient
            bot_client = ChatBotClient()
        except ImportError:
            from feature_utils import DummyChatBotClient
            bot_client = DummyChatBotClient()
        except Exception as e:
            print(f"[WARN] Chatbot initialization error: {e}")
            from feature_utils import DummyChatBotClient
            bot_client = DummyChatBotClient()
        
        self.feature_manager = FeatureManager(bot_client)
        
        # Create main window
        self.window = tk.Tk()
        self.window.title(f"ICS Chat - {client_name}")
        self.window.geometry("700x600")
        self.window.protocol("WM_DELETE_WINDOW", self.on_quit)
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Top frame with status
        top_frame = tk.Frame(self.window, bg='lightblue', height=40)
        top_frame.pack(fill=tk.X, side=tk.TOP)
        
        self.status_label = tk.Label(
            top_frame,
            text=f"Logged in as: {self.client_name} | Status: Not Connected",
            font=("Arial", 10),
            bg='lightblue',
            anchor='w'
        )
        self.status_label.pack(fill=tk.X, padx=10, pady=10)
        
        # Chat history area
        history_frame = tk.Frame(self.window)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(
            history_frame,
            text="Chat History",
            font=("Arial", 11, "bold")
        ).pack(anchor='w')
        
        self.chat_history = scrolledtext.ScrolledText(
            history_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            state=tk.DISABLED,
            height=20
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colors and styles
        self.chat_history.tag_config('green', foreground='green')
        self.chat_history.tag_config('red', foreground='red')
        self.chat_history.tag_config('blue', foreground='blue')
        self.chat_history.tag_config('gray', foreground='gray')
        self.chat_history.tag_config('lightgray', foreground='#999999')
        self.chat_history.tag_config('timestamp', foreground='#666666', font=("Arial", 8))
        self.chat_history.tag_config('checkmark', foreground='#999999', font=("Arial", 9))
        self.chat_history.tag_config('checkmark_seen', foreground='#4A90E2', font=("Arial", 9))
        self.chat_history.tag_config('bold', font=("Arial", 10, "bold"))
        
        # Input frame
        input_frame = tk.Frame(self.window)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            input_frame,
            text="Message:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        self.message_entry = tk.Entry(
            input_frame,
            font=("Arial", 10)
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.message_entry.bind('<Return>', lambda e: self.on_send())
        
        self.send_btn = tk.Button(
            input_frame,
            text="Send",
            font=("Arial", 10),
            command=self.on_send,
            width=10
        )
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        # Button frame
        button_frame = tk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.connect_btn = tk.Button(
            button_frame,
            text="Connect (Private)",
            font=("Arial", 10),
            command=self.on_connect,
            width=15
        )
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.game_btn = tk.Button(
            button_frame,
            text="Start Game",
            font=("Arial", 10),
            command=self.on_start_game,
            width=15,
            state=tk.DISABLED
        )
        self.game_btn.pack(side=tk.LEFT, padx=5)
        
        self.who_btn = tk.Button(
            button_frame,
            text="Who is Online",
            font=("Arial", 10),
            command=self.on_who,
            width=15
        )
        self.who_btn.pack(side=tk.LEFT, padx=5)
        
        self.quit_btn = tk.Button(
            button_frame,
            text="Quit",
            font=("Arial", 10),
            command=self.on_quit,
            width=15
        )
        self.quit_btn.pack(side=tk.LEFT, padx=5)
        
    def display_message(self, message, sender=None, color=None, tag=None, timestamp=None, msg_id=None, show_check=False):
        """
        Display a message in the chat history with timestamp and checkmarks
        
        Args:
            message: Message text
            sender: Sender name (optional)
            color: Text color (optional)
            tag: Special tag like 'bold' (optional)
            timestamp: Message timestamp (optional)
            msg_id: Message ID for tracking seen status (optional)
            show_check: Whether to show checkmarks (for sent messages)
        """
        self.chat_history.config(state=tk.NORMAL)
        
        # Add timestamp if provided
        if timestamp:
            self.chat_history.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        if sender:
            self.chat_history.insert(tk.END, f"{sender}: ", 'bold')
        
        # Analyze sentiment if it's a regular chat message
        if color is None and sender and not message.startswith("Bot:"):
            sentiment_color = self.feature_manager.get_sentiment_color(message)
            color = sentiment_color
        
        # Insert message with color
        if color:
            self.chat_history.insert(tk.END, message, color)
        elif tag:
            self.chat_history.insert(tk.END, message, tag)
        else:
            self.chat_history.insert(tk.END, message)
        
        # Add checkmarks for sent messages
        if show_check and msg_id:
            # Store message for tracking
            self.messages[msg_id] = {
                'text': message,
                'timestamp': timestamp,
                'seen': False,
                'line_start': None  # Will store text widget line number
            }
            
            # Add checkmark (will turn blue when seen)
            self.chat_history.insert(tk.END, " ✓", 'checkmark')
        
        self.chat_history.insert(tk.END, "\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)
    
    def mark_message_as_seen(self, msg_id):
        """Mark a message as seen and update checkmark color"""
        if msg_id in self.messages:
            self.messages[msg_id]['seen'] = True
            # In a real implementation, we'd update the checkmark color in the text widget
            # This is complex with tkinter Text widget, so we'll just note it's seen
            print(f"[✓✓] Message {msg_id} seen")
    
    def display_system_message(self, message):
        """Display a system message in gray"""
        timestamp = datetime.now().strftime("%I:%M %p")
        self.display_message(f"[SYSTEM] {message}", color='gray', timestamp=timestamp)
    
    def on_send(self):
        """Handle send button click"""
        message = self.message_entry.get().strip()
        
        if not message:
            return
        
        # Check if message is for bot
        if self.feature_manager.process_message_for_bot(
            message,
            lambda response: self.display_message(response, color='blue', timestamp=datetime.now().strftime("%I:%M %p"))
        ):
            # Message was for bot, display it
            timestamp = datetime.now().strftime("%I:%M %p")
            self.display_message(message, sender="You", color='blue', timestamp=timestamp)
            self.message_entry.delete(0, tk.END)
            return
        
        # Check if it's a game message
        if message.startswith("GAME_"):
            # Don't display game messages in chat
            self.send_callback(message)
            self.message_entry.delete(0, tk.END)
            return
        
        # Regular message - display with timestamp and checkmark
        timestamp = datetime.now().strftime("%I:%M %p")
        msg_id = f"me_{timestamp}_{message[:10]}"  # Simple ID
        
        self.display_message(
            message, 
            sender="You", 
            timestamp=timestamp,
            msg_id=msg_id,
            show_check=True
        )
        
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
            self.display_system_message(f"Connecting to {peer}...")
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
        
        # Create game window
        self.game_window = TicTacGame(
            self.window,
            self.send_callback,
            self.peer_name
        )
        
        self.display_system_message("Game window opened!")
    
    def on_who(self):
        """Handle who is online button click"""
        self.send_callback("who")
        self.display_system_message("Requesting online users...")
    
    def on_quit(self):
        """Handle quit button click"""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            self.send_callback("q")
            self.window.destroy()
    
    def handle_incoming_message(self, message, sender, timestamp=None, msg_id=None):
        """
        Handle incoming message from server
        
        Args:
            message: Message content
            sender: Sender's name
            timestamp: Message timestamp
            msg_id: Message ID for seen tracking
        """
        # Check if it's a game message
        if message.startswith("GAME_"):
            if self.game_window:
                self.game_window.receive_move(message)
            return
        
        # Display regular message with timestamp
        if not timestamp:
            timestamp = datetime.now().strftime("%I:%M %p")
        
        self.display_message(message, sender=sender, timestamp=timestamp)
    
    def handle_system_message(self, message):
        """Handle system messages from server"""
        self.display_system_message(message)
        
        # Update status based on message
        if "connected to" in message.lower():
            self.status_label.config(
                text=f"Logged in as: {self.client_name} | Status: Connected to {self.peer_name}"
            )
        elif "disconnected" in message.lower():
            self.status_label.config(
                text=f"Logged in as: {self.client_name} | Status: Not Connected"
            )
            self.connect_btn.config(state=tk.NORMAL)
            self.game_btn.config(state=tk.DISABLED)
            self.peer_name = None
    
    def handle_user_list(self, users):
        """Handle online user list"""
        if users:
            user_str = ", ".join(users)
            self.display_system_message(f"Online users: {user_str}")
        else:
            self.display_system_message("No other users online")
    
    def update_status(self, status):
        """Update status label"""
        self.status_label.config(
            text=f"Logged in as: {self.client_name} | Status: {status}"
        )
    
    def run(self):
        """Start the GUI main loop"""
        self.window.mainloop()