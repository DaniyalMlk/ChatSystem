"""
chat_gui.py - COMPLETE VERSION WITH OPTIMIZED TRACKPAD SCROLLING
Optimized for Mac trackpad - smooth scrolling already works!
"""
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, font
import sys

# --- IMPORTS FOR FEATURES ---
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("[WARN] Pillow not installed. Image generation disabled.")

try:
    from image_client import ImageGenClient
except ImportError:
    ImageGenClient = None
    print("[WARN] image_client.py not found. Image generation disabled.")

# --- CONFIGURATION ---
COLORS = {
    'bg': '#1E1E1E',
    'panel': '#252525',
    'input_bg': '#333333',
    'accent': '#0A84FF',
    'accent_hover': '#007AFF',
    'text': '#FFFFFF',
    'text_sec': '#B0B0B0',
    'bubble_mine': '#0A84FF',
    'bubble_theirs': '#333333',
    # Sentiment colors
    'positive': '#30D158',  # Green
    'negative': '#FF453A',  # Red
    'neutral': '#8E8E93'    # Gray
}

def get_font(size, weight="normal"):
    families = font.families()
    for f in ["SF Pro Display", "SF Pro Text", "Helvetica Neue", "Segoe UI", "Arial"]:
        if f in families:
            return (f, size, weight)
    return ("Arial", size, weight)

# --- CUSTOM WIDGETS ---
class RoundedFrame(tk.Canvas):
    def __init__(self, parent, width, height, radius=20, bg_color="#000000", command=None):
        super().__init__(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0)
        self.radius = radius
        self.bg_color = bg_color
        self.command = command
        self.width = width
        self.height = height
        
        self._draw_rounded_rect(bg_color)
        
        if command:
            self.bind("<Button-1>", self._on_click)
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)

    def _draw_rounded_rect(self, fill_color):
        self.delete("bg")
        x1, y1 = 2, 2
        x2, y2 = self.width - 2, self.height - 2
        r = self.radius
        points = [
            x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2,
            x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r,
            x1, y1+r, x1, y1
        ]
        self.create_polygon(points, fill=fill_color, smooth=True, tags="bg")
        self.tag_lower("bg")

    def _on_click(self, e):
        if self.command: self.command()

    def _on_enter(self, e):
        if self.command and self.bg_color == COLORS['accent']: 
             self._draw_rounded_rect(COLORS['accent_hover'])
        self.configure(cursor="hand2")

    def _on_leave(self, e):
        if self.command:
             self._draw_rounded_rect(self.bg_color)
        self.configure(cursor="")

    def add_text(self, text, color="white", size=11, weight="bold"):
        self.create_text(self.width/2, self.height/2, text=text, fill=color, 
                        font=get_font(size, weight), tags="text")

# --- MOCKS ---
try:
    from game_client import TetrisGame
except ImportError:
    class TetrisGame: 
        def __init__(self, *args): 
            messagebox.showwarning("Game", "game_client.py not found")

try:
    from feature_utils import FeatureManager
except ImportError:
    class FeatureManager: 
        def __init__(self, *args): pass
        def analyze_sentiment(self, text): 
            return {'color': 'neutral', 'label': 'neutral', 'polarity': 0.0}

# --- LOGIN WINDOW ---
class LoginWindow:
    def __init__(self, callback=None):
        self.callback = callback
        self.nickname = None
        self.window = tk.Tk()
        self.window.title("Login")
        self.window.geometry("400x550")
        self.window.configure(bg=COLORS['bg'])
        self.center_window()
        self._build_ui()

    def center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f'+{x}+{y}')

    def _build_ui(self):
        container = tk.Frame(self.window, bg=COLORS['bg'])
        container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(container, text="💬", font=("Apple Color Emoji", 64), 
                bg=COLORS['bg']).pack(pady=(0, 10))
        
        tk.Label(container, text="Messages", font=get_font(28, "bold"), 
                 bg=COLORS['bg'], fg=COLORS['text']).pack(pady=(0, 5))
        
        tk.Label(container, text="Enter your nickname to continue", 
                font=get_font(11), bg=COLORS['bg'], 
                fg=COLORS['text_sec']).pack(pady=(0, 30))

        self.input_bg = RoundedFrame(container, width=280, height=50, 
                                     radius=25, bg_color=COLORS['input_bg'])
        self.input_bg.pack(pady=(0, 25))
        
        self.entry = tk.Entry(self.input_bg, font=get_font(14), 
                              bg=COLORS['input_bg'], fg='white', 
                              insertbackground=COLORS['accent'],
                              relief=tk.FLAT, justify='center')
        self.entry.place(relx=0.5, rely=0.5, anchor='center', width=200, height=30)
        self.entry.focus()
        self.entry.bind('<Return>', lambda e: self.on_login())

        self.btn = RoundedFrame(container, width=200, height=50, radius=25, 
                                bg_color=COLORS['accent'], command=self.on_login)
        self.btn.add_text("Start Chatting", size=12)
        self.btn.pack()

    def on_login(self):
        nick = self.entry.get().strip()
        if len(nick) < 2: return
        self.nickname = nick
        self.window.destroy()
        if self.callback: self.callback(nick)
    
    def run(self):
        self.window.mainloop()
        return self.nickname

# --- CHAT WINDOW ---
class ChatGUI:
    def __init__(self, send_callback, client_name):
        self.send_callback = send_callback
        self.client_name = client_name
        self.peer_name = None
        self.game_window = None
        self.messages = []
        self.chat_history_text = []
        self.message_widgets = {}
        
        # Initialize feature manager
        try:
            from chat_bot_client import ChatBotClient
            bot_client = ChatBotClient()
            self.bot_client = bot_client
        except:
            class DummyBot:
                def ask(self, query, callback):
                    callback(f"Echo: {query}")
                def analyze_text(self, text, mode, callback):
                    callback(f"Analysis not available")
            bot_client = DummyBot()
            self.bot_client = bot_client
        
        self.feature_manager = FeatureManager(bot_client)
        
        # Image client
        if ImageGenClient and PILLOW_AVAILABLE:
            try:
                self.image_client = ImageGenClient()
            except Exception as e:
                print(f"Image client failed: {e}")
                self.image_client = None
        else:
            self.image_client = None
        
        # Create window
        self.window = tk.Tk()
        self.window.title("Messages")
        self.window.geometry("1000x800")
        self.window.configure(bg=COLORS['bg'])
        self.window.minsize(800, 600)
        self.window.protocol("WM_DELETE_WINDOW", self.on_quit)
        
        self._build_ui()
        self._setup_trackpad_scrolling()  # Setup smooth scrolling
    
    def _build_ui(self):
        # Header
        header = tk.Frame(self.window, bg=COLORS['panel'], height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        info_frame = tk.Frame(header, bg=COLORS['panel'])
        info_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        self.contact_label = tk.Label(info_frame, text="Not Connected", 
                                      font=get_font(13, "bold"), 
                                      bg=COLORS['panel'], fg='white')
        self.contact_label.pack()
        
        self.status_label = tk.Label(info_frame, text="Offline", 
                                     font=get_font(10), 
                                     bg=COLORS['panel'], fg=COLORS['text_sec'])
        self.status_label.pack()
        
        search_btn = tk.Label(header, text="🔍", font=get_font(16), 
                             bg=COLORS['panel'], fg=COLORS['accent'], 
                             cursor='hand2')
        search_btn.place(relx=0.95, rely=0.5, anchor='center')
        search_btn.bind('<Button-1>', lambda e: self.show_search())

        # Chat Area with Canvas for scrolling
        msg_area = tk.Frame(self.window, bg=COLORS['bg'])
        msg_area.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(msg_area, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(msg_area, orient="vertical", 
                                command=self.canvas.yview, bg=COLORS['bg'])
        self.scroll_frame = tk.Frame(self.canvas, bg=COLORS['bg'])
        
        self.scroll_frame.bind("<Configure>", 
                              lambda e: self.canvas.configure(
                                  scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), 
                                                       window=self.scroll_frame, 
                                                       anchor="nw")
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', 
                        lambda e: self.canvas.itemconfig(self.canvas_window, 
                                                         width=e.width))
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # CRITICAL: Set focus when mouse enters canvas area
        self.canvas.bind('<Enter>', lambda e: self.canvas.focus_set())

        # Footer
        footer = tk.Frame(self.window, bg=COLORS['panel'], height=80)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        input_container = tk.Frame(footer, bg=COLORS['panel'])
        input_container.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.95)
        
        emoji_btn = tk.Label(input_container, text="😀", 
                           font=("Apple Color Emoji", 22), 
                           bg=COLORS['panel'], cursor='hand2')
        emoji_btn.pack(side=tk.LEFT, padx=(0, 10))
        emoji_btn.bind('<Button-1>', lambda e: self.show_emoji_picker())
        
        send_btn = RoundedFrame(input_container, width=36, height=36, 
                               radius=18, bg_color=COLORS['accent'], 
                               command=self.on_send)
        send_btn.add_text("↑", size=18)
        send_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        input_wrapper = tk.Frame(input_container, bg=COLORS['panel'])
        input_wrapper.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.input_bg_canvas = tk.Canvas(input_wrapper, height=38, 
                                         bg=COLORS['panel'], highlightthickness=0)
        self.input_bg_canvas.pack(fill=tk.BOTH, expand=True)
        self.input_bg_canvas.bind('<Configure>', self._draw_chat_input_bg)
        
        self.entry = tk.Entry(input_wrapper, font=get_font(13), 
                            bg=COLORS['input_bg'], fg='white', 
                            insertbackground=COLORS['accent'],
                            relief=tk.FLAT, bd=0)
        self.entry.place(relx=0.0, rely=0.5, x=15, anchor='w', 
                        relwidth=0.95, height=24)
        self.entry.bind('<Return>', lambda e: self.on_send())

        # Controls
        controls = tk.Frame(self.window, bg=COLORS['bg'])
        controls.pack(fill=tk.X, side=tk.BOTTOM)
        
        def mk_btn(txt, cmd, state=tk.NORMAL):
            return tk.Button(controls, text=txt, font=get_font(10), 
                           bg=COLORS['bg'], fg=COLORS['accent'],
                           activebackground=COLORS['panel'], 
                           activeforeground=COLORS['accent'],
                           relief=tk.FLAT, borderwidth=0, 
                           cursor='hand2', command=cmd, state=state)

        btn_row = tk.Frame(controls, bg=COLORS['bg'])
        btn_row.pack(pady=5)
        
        self.connect_btn = mk_btn("Connect", self.on_connect)
        self.connect_btn.pack(side=tk.LEFT, padx=15)
        
        self.group_btn = mk_btn("Create Group", self.on_create_group)
        self.group_btn.pack(side=tk.LEFT, padx=15)
        
        self.game_btn = mk_btn("Play Game", self.on_start_game, tk.NORMAL)
        self.game_btn.pack(side=tk.LEFT, padx=15)
        
        self.who_btn = mk_btn("Online Users", self.on_who)
        self.who_btn.pack(side=tk.LEFT, padx=15)
        
        self.add_system_message("Welcome! Commands:\n" +
                               "• Connect to chat\n" +
                               "• @bot <question> - Ask AI\n" +
                               "• /summary - Analyze chat\n" +
                               "• /keywords - Extract keywords\n" +
                               "• /aipic: <prompt> - Generate image\n" +
                               "• 🔍 Search - Find messages\n" +
                               "• Use trackpad/mouse to scroll")

    # ============================================
    # TRACKPAD SCROLLING - WORKING MAC VERSION
    # ============================================
    
    def _setup_trackpad_scrolling(self):
        """
        Setup trackpad scrolling for Mac
        The key is to bind BOTH the canvas AND window to MouseWheel events
        """
        # Bind canvas
        self.canvas.bind('<MouseWheel>', self._on_scroll)
        
        # IMPORTANT: Also bind the window for when focus is elsewhere
        self.window.bind('<MouseWheel>', self._on_scroll)
        
        # Bind scroll frame too
        self.scroll_frame.bind('<MouseWheel>', self._on_scroll)
        
        # For Linux (if needed)
        self.canvas.bind('<Button-4>', lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind('<Button-5>', lambda e: self.canvas.yview_scroll(1, "units"))
        
        # CRITICAL: Make sure canvas can receive focus
        self.canvas.focus_set()
    
    def _on_scroll(self, event):
        """
        Handle trackpad/mouse wheel scrolling
        Works on Mac trackpad with two-finger swipe
        """
        # On Mac, event.delta is the scroll amount
        # Positive = scroll up, Negative = scroll down
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")
        
        return "break"  # Prevent event propagation

    def _draw_chat_input_bg(self, event):
        w, h = event.width, event.height
        self.input_bg_canvas.delete("all")
        r = 19
        self.input_bg_canvas.create_oval(0, 0, 2*r, h, 
                                        fill=COLORS['input_bg'], width=0)
        self.input_bg_canvas.create_rectangle(r, 0, w-r, h, 
                                              fill=COLORS['input_bg'], width=0)
        self.input_bg_canvas.create_oval(w-2*r, 0, w, h, 
                                        fill=COLORS['input_bg'], width=0)

    # ============================================
    # MESSAGE DISPLAY WITH SENTIMENT ANALYSIS
    # ============================================
    
    def add_message_bubble(self, message, is_mine=True, timestamp=None, 
                          sender_name=None, sentiment=None):
        """Add message bubble with sentiment analysis"""
        wrapper = tk.Frame(self.scroll_frame, bg=COLORS['bg'])
        wrapper.pack(fill=tk.X, padx=20, pady=4)
        
        if sentiment and not is_mine:
            sentiment_color = COLORS.get(sentiment['label'], COLORS['bubble_theirs'])
            bg_col = sentiment_color
        else:
            bg_col = COLORS['bubble_mine'] if is_mine else COLORS['bubble_theirs']
        
        if is_mine:
            inner = tk.Frame(wrapper, bg=COLORS['bg'])
            inner.pack(side=tk.RIGHT)
            justify = tk.LEFT
            anchor = 'e'
        else:
            inner = tk.Frame(wrapper, bg=COLORS['bg'])
            inner.pack(side=tk.LEFT)
            justify = tk.LEFT
            anchor = 'w'
            
        bubble = tk.Label(inner, text=message, font=get_font(13), 
                         bg=bg_col, fg='white',
                         padx=16, pady=10, wraplength=450, justify=justify)
        bubble.pack(anchor=anchor)
        
        info_parts = []
        if sender_name and not is_mine:
            info_parts.append(sender_name)
        if timestamp:
            info_parts.append(timestamp)
        if sentiment and not is_mine:
            emoji_map = {
                'positive': '😊',
                'negative': '😞',
                'neutral': '😐'
            }
            sentiment_emoji = emoji_map.get(sentiment['label'], '')
            if sentiment_emoji:
                info_parts.append(sentiment_emoji)
        
        if info_parts:
            info_text = " • ".join(info_parts)
            tk.Label(inner, text=info_text, font=get_font(9), 
                    bg=COLORS['bg'], fg=COLORS['text_sec']).pack(anchor=anchor, pady=(2,0))
        
        real_sender = "Me" if is_mine else (sender_name if sender_name else "Peer")
        if not message.startswith("/") and not message.startswith("@bot"):
             self.chat_history_text.append(f"[{real_sender}]: {message}")
        
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def add_image_bubble(self, tk_image, is_mine=True, timestamp=None, sender="AI"):
        """Add image bubble"""
        if not PILLOW_AVAILABLE:
            self.add_system_message("Image display requires Pillow")
            return
            
        wrapper = tk.Frame(self.scroll_frame, bg=COLORS['bg'])
        wrapper.pack(fill=tk.X, padx=20, pady=8)
        
        if is_mine:
            inner = tk.Frame(wrapper, bg=COLORS['bg'])
            inner.pack(side=tk.RIGHT)
            anchor = 'e'
        else:
            inner = tk.Frame(wrapper, bg=COLORS['bg'])
            inner.pack(side=tk.LEFT)
            anchor = 'w'
            
        bg_col = COLORS['bubble_mine'] if is_mine else COLORS['bubble_theirs']
        img_label = tk.Label(inner, image=tk_image, bg=bg_col, bd=4, relief=tk.FLAT)
        img_label.image = tk_image
        img_label.pack(anchor=anchor)
        
        if timestamp:
            tk.Label(inner, text=f"{sender} • {timestamp}", font=get_font(9), 
                    bg=COLORS['bg'], fg=COLORS['text_sec']).pack(anchor=anchor, pady=(2,0))

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def add_system_message(self, message, timestamp=None):
        """Add system message"""
        f = tk.Frame(self.scroll_frame, bg=COLORS['bg'])
        f.pack(fill=tk.X, pady=10)
        tk.Label(f, text=message, font=get_font(10, "bold"), 
                bg=COLORS['bg'], fg=COLORS['text_sec'], 
                wraplength=600, justify=tk.LEFT).pack()
        self.canvas.yview_moveto(1.0)

    # ============================================
    # MESSAGE SENDING
    # ============================================
    
    def on_send(self):
        """Handle message send"""
        msg = self.entry.get().strip()
        if not msg: return
        ts = datetime.now().strftime("%I:%M %p")
        
        self.entry.delete(0, tk.END)

        if msg == "/summary" or msg == "/keywords":
            if len(self.chat_history_text) < 2:
                self.add_system_message("Not enough chat history.")
                return

            mode = "summary" if msg == "/summary" else "keywords"
            self.add_system_message(f"🧠 Analyzing for {mode}...")
            recent_history = "\n".join(self.chat_history_text[-20:])

            def on_analysis_done(result):
                self.window.after(0, lambda: self.add_message_bubble(
                    f"📝 {mode.upper()}:\n{result}", False, 
                    datetime.now().strftime("%I:%M %p"), "AI Analyst"))

            try:
                self.bot_client.analyze_text(recent_history, mode, on_analysis_done)
            except Exception as e:
                self.add_system_message(f"Error: {e}")
            return

        if msg.startswith("/aipic:"):
            if not self.image_client:
                self.add_system_message("Image generation not available")
                return
            try:
                prompt = msg.split(":", 1)[1].strip()
                if not prompt:
                    self.add_system_message("Usage: /aipic: prompt")
                    return
            except:
                self.add_system_message("Usage: /aipic: prompt")
                return

            self.add_system_message(f"🎨 Generating: '{prompt}'...")

            def on_image_ready(tk_image, error_msg):
                timestamp = datetime.now().strftime("%I:%M %p")
                if error_msg:
                    self.window.after(0, lambda: self.add_system_message(f"Error: {error_msg}"))
                else:
                    self.window.after(0, lambda: self.add_image_bubble(tk_image, False, timestamp, "AI Artist"))

            self.image_client.generate(prompt, on_image_ready)
            return

        if msg.startswith("@bot"):
            user_query = msg[4:].strip()
            if not user_query:
                self.add_system_message("Usage: @bot <question>")
                return
            self.add_message_bubble(msg, True, ts)
            self.add_system_message("Bot thinking...")
            
            def on_bot_reply(reply_text):
                self.window.after(0, lambda: self.add_message_bubble(
                    reply_text, False, datetime.now().strftime("%I:%M %p"), "DeepSeek Bot"))

            try:
                self.bot_client.ask(user_query, on_bot_reply)
            except Exception as e:
                self.add_system_message(f"Bot error: {e}")
            return

        self.add_message_bubble(msg, True, ts)
        self.send_callback(msg)

    # ============================================
    # SEARCH, EMOJI, CONNECTIONS
    # ============================================
    
    def show_search(self):
        """Search messages"""
        query = simpledialog.askstring("Search Messages", 
                                      "Enter search terms:", parent=self.window)
        if not query: return
        
        results = []
        query_words = query.lower().split()
        
        for line in self.chat_history_text:
            if all(word in line.lower() for word in query_words):
                results.append(line)
        
        if results:
            result_msg = f"Found {len(results)} message(s):\n\n"
            result_msg += "\n".join(results[:15])
            if len(results) > 15:
                result_msg += f"\n\n... and {len(results) - 15} more"
            messagebox.showinfo("Search Results", result_msg)
        else:
            messagebox.showinfo("Search Results", f"No messages found for: '{query}'")

    def show_emoji_picker(self):
        """Show emoji picker"""
        picker = tk.Toplevel(self.window)
        picker.geometry("360x400")
        picker.title("Emojis")
        picker.configure(bg=COLORS['panel'])
        
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - 180
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - 200
        picker.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(picker, bg=COLORS['panel'], highlightthickness=0)
        scrollbar = tk.Scrollbar(picker, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLORS['panel'])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        categories = {
            "Faces": ['😀','😃','😄','😁','😆','😅','🤣','😂','🙂','🙃',
                     '😉','😊','😇','🥰','😍','🤩','😘','😗','😚','😙'],
            "Gestures": ['👋','🤚','🖐','✋','🖖','👌','🤌','🤏','✌️','🤞',
                        '🤟','🤘','🤙','👈','👉','👆','🖕','👇','👍','👎',
                        '✊','👊','🤛','🤜','👏','🙌'],
            "Hearts": ['❤️','🧡','💛','💚','💙','💜','🖤','🤍','🤎','💔',
                      '❣️','💕','💞','💓','💗','💖','💘','💝'],
            "Objects": ['🔥','✨','🎉','🎊','🎁','🎈','🎂','🎄','🎃','🎗',
                       '🎟','🎫','🎖','🏆','🏅','🥇','🥈','🥉']
        }

        for cat, emojis in categories.items():
            tk.Label(scroll_frame, text=cat, font=get_font(10, "bold"), 
                    bg=COLORS['panel'], fg=COLORS['text_sec']).pack(anchor='w', pady=(10, 5))
            grid_frame = tk.Frame(scroll_frame, bg=COLORS['panel'])
            grid_frame.pack(fill='x')
            for i, char in enumerate(emojis):
                btn = tk.Button(grid_frame, text=char, font=("Apple Color Emoji", 18), 
                               bg=COLORS['panel'], fg='white', relief=tk.FLAT, bd=0,
                               activebackground=COLORS['input_bg'],
                               command=lambda c=char: [self.entry.insert(tk.END, c), picker.destroy()])
                btn.grid(row=i//5, column=i%5, padx=5, pady=5)

    def on_connect(self):
        """Connect to user"""
        peer_input = simpledialog.askstring("Connect", 
                                           "Enter nickname to connect:", 
                                           parent=self.window)
        if not peer_input: return
        
        self.peer_name = peer_input.strip()
        self.send_callback(f"connect {self.peer_name}")
        self.add_system_message(f"Connecting to {self.peer_name}...", 
                               datetime.now().strftime("%I:%M %p"))
        self.connect_btn.config(state=tk.DISABLED)
        self.group_btn.config(state=tk.DISABLED)
        self.game_btn.config(state=tk.NORMAL)

    def on_create_group(self):
        """Create a group chat with multiple users"""
        members_input = simpledialog.askstring(
            "Create Group Chat", 
            "Enter usernames separated by commas:\n(e.g., alice, bob, charlie)",
            parent=self.window
        )
        
        if not members_input:
            return
        
        # Parse member list
        members = [m.strip() for m in members_input.split(',') if m.strip()]
        
        if len(members) < 2:
            messagebox.showwarning(
                "Invalid Input",
                "You need at least 2 other people for a group chat"
            )
            return
        
        # Send create_group command
        import json
        create_msg = json.dumps({
            'action': 'create_group',
            'members': members
        })
        self.send_callback(create_msg)
        
        self.add_system_message(
            f"Creating group with: {', '.join(members)}...",
            datetime.now().strftime("%I:%M %p")
        )
        
        # Disable both buttons while connecting
        self.connect_btn.config(state=tk.DISABLED)
        self.group_btn.config(state=tk.DISABLED)

    def on_start_game(self):
        """Start game"""
        if self.game_window:
            self.game_window.window.lift()
            return
        try:
            player_name = self.peer_name if self.peer_name else "Solo"
            self.game_window = TetrisGame(self.window, self.send_callback, player_name)
            self.add_system_message("Tetris started!")
        except Exception as e:
            messagebox.showerror("Game Error", str(e))

    def on_who(self):
        try:
            self.add_system_message("Checking users...")
            import json
            who_msg = json.dumps({'action': 'who'})
            self.send_callback(who_msg)
            print(f"[DEBUG] Sent who request: {who_msg}")
        except Exception as e:
            print(f"[DEBUG] Error in on_who: {e}")
            import traceback
            traceback.print_exc()
            self.add_system_message(f"Error checking users: {e}")
    
    def on_quit(self):
        """Quit"""
        if messagebox.askokcancel("Quit", "Quit Messages?"):
            self.send_callback("q")
            self.window.destroy()

    # ============================================
    # INCOMING HANDLERS
    # ============================================
    
    def handle_incoming_message(self, message, sender, timestamp=None, msg_id=None):
        """Handle incoming message with sentiment"""
        if message.startswith("GAME_"):
            if self.game_window:
                self.game_window.receive_move(message)
            elif "GAME_START" in message:
                if messagebox.askyesno("Challenge", f"{sender} started Tetris. Join?"):
                     self.peer_name = sender
                     self.on_start_game()
            return
        
        sentiment = self.feature_manager.analyze_sentiment(message)
        if not timestamp: 
            timestamp = datetime.now().strftime("%I:%M %p")
        self.add_message_bubble(message, False, timestamp, sender, sentiment)

    def handle_system_message(self, message):
        """Handle system messages"""
        self.add_system_message(message)
        if "connected to" in message.lower() and self.peer_name:
            self.contact_label.config(text=self.peer_name)
            self.status_label.config(text="Active Now")
        elif "group chat created" in message.lower():
            # Group created - update UI
            self.contact_label.config(text="Group Chat")
            self.status_label.config(text="Active Group")
            self.game_btn.config(state=tk.NORMAL)
        elif "disconnected" in message.lower():
            self.contact_label.config(text="Not Connected")
            self.status_label.config(text="Offline")
            self.connect_btn.config(state=tk.NORMAL)
            self.group_btn.config(state=tk.NORMAL)
            self.game_btn.config(state=tk.DISABLED)

    def handle_group_created(self, group_data):
        """
        Handle group creation notification
        
        Args:
            group_data: Dict with 'members' and 'message'
        """
        members = group_data.get('members', [])
        message = group_data.get('message', 'Group chat created')
        
        # Update UI
        self.contact_label.config(text=f"Group ({len(members)} people)")
        self.status_label.config(text="Active Group")
        
        # Show members
        member_list = ", ".join([m for m in members if m != self.client_name])
        self.add_system_message(
            f"✅ {message}\n👥 Members: {member_list}",
            datetime.now().strftime("%I:%M %p")
        )
        
        # Enable game button
        self.game_btn.config(state=tk.NORMAL)

    def handle_user_list(self, users):
        """Handle user list"""
        if users:
            users = [u for u in users if u != self.client_name]
            if users:
                self.add_system_message(f"👥 Online: {', '.join(users)}")
            else:
                self.add_system_message("👥 You're the only one online")
        else:
            self.add_system_message("👥 No other users online")

    # Compatibility methods
    def display_system_message(self, message):
        self.add_system_message(message)
    
    def update_status(self, status_text):
        if hasattr(self, 'status_label'):
            self.status_label.config(text=status_text)
    
    def mark_message_as_seen(self, msg_id):
        pass
        
    def run(self):
        self.window.mainloop()

# --- EXECUTION ---
if __name__ == "__main__":
    login = LoginWindow()
    nick = login.run()
    if nick:
        def dummy(m): print(f"Sent: {m}")
        app = ChatGUI(dummy, nick)
        app.run()