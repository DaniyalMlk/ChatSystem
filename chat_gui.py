"""
chat_gui.py - Premium iOS-Style Dark Theme
FIXED: Pixel-perfect vertical centering for macOS/Windows
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, font
from datetime import datetime

# --- CONFIGURATION ---
COLORS = {
    'bg': '#1E1E1E',           # Charcoal Background
    'panel': '#252525',        # Header/Footer
    'input_bg': '#333333',     # Input Fields
    'accent': '#0A84FF',       # iOS Blue
    'accent_hover': '#007AFF', 
    'text': '#FFFFFF',         # White
    'text_sec': '#B0B0B0',     # Secondary Text
    'bubble_mine': '#0A84FF',  
    'bubble_theirs': '#333333' 
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
        self.delete("bg") # Only delete background tag
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
        self.tag_lower("bg") # Ensure background stays behind text

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
        # Centering text within the canvas
        self.create_text(self.width/2, self.height/2, text=text, fill=color, font=get_font(size, weight), tags="text")

# --- MOCKS ---
try:
    from game_client import TetrisGame
    from feature_utils import FeatureManager
except ImportError:
    class TetrisGame: 
        def __init__(self, *args): pass
    class FeatureManager: 
        def __init__(self, *args): pass

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

        # Icon
        tk.Label(container, text="💬", font=("Apple Color Emoji", 64), bg=COLORS['bg']).pack(pady=(0, 10))
        
        # Titles
        tk.Label(container, text="Messages", font=get_font(28, "bold"), 
                 bg=COLORS['bg'], fg=COLORS['text']).pack(pady=(0, 5))
        
        tk.Label(container, text="Enter your nickname to continue", font=get_font(11), 
                 bg=COLORS['bg'], fg=COLORS['text_sec']).pack(pady=(0, 30))

        # --- THE FIX IS HERE ---
        # 1. Create the rounded background
        self.input_bg = RoundedFrame(container, width=280, height=50, radius=25, bg_color=COLORS['input_bg'])
        self.input_bg.pack(pady=(0, 25))
        
        # 2. Create entry. Note: justify='center' centers the cursor horizontally
        self.entry = tk.Entry(self.input_bg, font=get_font(14), 
                              bg=COLORS['input_bg'], fg='white', insertbackground=COLORS['accent'],
                              relief=tk.FLAT, justify='center')
        
        # 3. USE PLACE() TO CENTER VERTICALLY & HORIZONTALLY
        # relx=0.5, rely=0.5 puts the center of the widget at the center of the frame
        self.entry.place(relx=0.5, rely=0.5, anchor='center', width=200, height=30)
        
        self.entry.focus()
        self.entry.bind('<Return>', lambda e: self.on_login())

        # Button
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
        
        try:
            from chat_bot_client import ChatBotClient
            bot_client = ChatBotClient()
        except:
            class Dummy: pass
            bot_client = Dummy()
        self.feature_manager = FeatureManager(bot_client)
        
        self.window = tk.Tk()
        self.window.title("Messages")
        self.window.geometry("1000x800")
        self.window.configure(bg=COLORS['bg'])
        self.window.minsize(800, 600)
        self.window.protocol("WM_DELETE_WINDOW", self.on_quit)
        
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.window, bg=COLORS['panel'], height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        info_frame = tk.Frame(header, bg=COLORS['panel'])
        info_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        self.contact_label = tk.Label(info_frame, text="Not Connected", font=get_font(13, "bold"), 
                                    bg=COLORS['panel'], fg='white')
        self.contact_label.pack()
        
        self.status_label = tk.Label(info_frame, text="Offline", font=get_font(10), 
                                   bg=COLORS['panel'], fg=COLORS['text_sec'])
        self.status_label.pack()
        
        search_btn = tk.Label(header, text="🔍", font=get_font(16), bg=COLORS['panel'], fg=COLORS['accent'], cursor='hand2')
        search_btn.place(relx=0.95, rely=0.5, anchor='center')
        search_btn.bind('<Button-1>', lambda e: self.show_search())

        # Chat Area
        msg_area = tk.Frame(self.window, bg=COLORS['bg'])
        msg_area.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(msg_area, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(msg_area, orient="vertical", command=self.canvas.yview, bg=COLORS['bg'], troughcolor=COLORS['bg'], activebackground=COLORS['panel'])
        self.scroll_frame = tk.Frame(self.canvas, bg=COLORS['bg'])
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Footer
        footer = tk.Frame(self.window, bg=COLORS['panel'], height=80)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        input_container = tk.Frame(footer, bg=COLORS['panel'])
        input_container.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.95)
        
        emoji_btn = tk.Label(input_container, text="😀", font=("Apple Color Emoji", 22), 
                           bg=COLORS['panel'], cursor='hand2')
        emoji_btn.pack(side=tk.LEFT, padx=(0, 10))
        emoji_btn.bind('<Button-1>', lambda e: self.show_emoji_picker())
        
        send_btn = RoundedFrame(input_container, width=36, height=36, radius=18, bg_color=COLORS['accent'], command=self.on_send)
        send_btn.add_text("↑", size=18)
        send_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # --- FIXED CHAT INPUT ---
        # We create a container for the input to manage layout better
        input_wrapper = tk.Frame(input_container, bg=COLORS['panel'])
        input_wrapper.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # The background pill
        self.input_bg_canvas = tk.Canvas(input_wrapper, height=38, bg=COLORS['panel'], highlightthickness=0)
        self.input_bg_canvas.pack(fill=tk.BOTH, expand=True)
        self.input_bg_canvas.bind('<Configure>', self._draw_chat_input_bg)
        
        # The entry widget on top
        self.entry = tk.Entry(input_wrapper, font=get_font(13), 
                            bg=COLORS['input_bg'], fg='white', insertbackground=COLORS['accent'],
                            relief=tk.FLAT, bd=0)
        # Place relative to wrapper: Centered vertically, offset horizontally
        self.entry.place(relx=0.0, rely=0.5, x=15, anchor='w', relwidth=0.95, height=24)
        self.entry.bind('<Return>', lambda e: self.on_send())

        # Controls
        controls = tk.Frame(self.window, bg=COLORS['bg'])
        controls.pack(fill=tk.X, side=tk.BOTTOM)
        
        def mk_btn(txt, cmd, state=tk.NORMAL):
            return tk.Button(controls, text=txt, font=get_font(10), bg=COLORS['bg'], fg=COLORS['accent'],
                             activebackground=COLORS['panel'], activeforeground=COLORS['accent'],
                             relief=tk.FLAT, borderwidth=0, cursor='hand2', command=cmd, state=state)

        btn_row = tk.Frame(controls, bg=COLORS['bg'])
        btn_row.pack(pady=5)
        self.connect_btn = mk_btn("Connect", self.on_connect)
        self.connect_btn.pack(side=tk.LEFT, padx=15)
        self.game_btn = mk_btn("Play Game", self.on_start_game, tk.DISABLED)
        self.game_btn.pack(side=tk.LEFT, padx=15)
        self.who_btn = mk_btn("Online Users", self.on_who)
        self.who_btn.pack(side=tk.LEFT, padx=15)

    def _draw_chat_input_bg(self, event):
        w, h = event.width, event.height
        self.input_bg_canvas.delete("all")
        r = 19 # Half height
        self.input_bg_canvas.create_oval(0, 0, 2*r, h, fill=COLORS['input_bg'], width=0)
        self.input_bg_canvas.create_rectangle(r, 0, w-r, h, fill=COLORS['input_bg'], width=0)
        self.input_bg_canvas.create_oval(w-2*r, 0, w, h, fill=COLORS['input_bg'], width=0)

    # --- FUNCTIONALITY ---
    def add_message_bubble(self, message, is_mine=True, timestamp=None, sender_name=None):
        wrapper = tk.Frame(self.scroll_frame, bg=COLORS['bg'])
        wrapper.pack(fill=tk.X, padx=20, pady=4)
        
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
            
        bubble = tk.Label(inner, text=message, font=get_font(13), bg=bg_col, fg='white',
                          padx=16, pady=10, wraplength=450, justify=justify)
        bubble.pack(anchor=anchor)
        
        if timestamp:
            tk.Label(inner, text=timestamp, font=get_font(9), bg=COLORS['bg'], fg=COLORS['text_sec']).pack(anchor=anchor, pady=(2,0))

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def add_system_message(self, message, timestamp=None):
        f = tk.Frame(self.scroll_frame, bg=COLORS['bg'])
        f.pack(fill=tk.X, pady=10)
        tk.Label(f, text=message, font=get_font(10, "bold"), bg=COLORS['bg'], fg=COLORS['text_sec']).pack()
        self.canvas.yview_moveto(1.0)

    def on_send(self):
        msg = self.entry.get().strip()
        if not msg: return
        ts = datetime.now().strftime("%I:%M %p")
        
        # 1. Add User Message immediately
        self.add_message_bubble(msg, True, ts)
        self.entry.delete(0, tk.END)

        # 2. Check for Bot Trigger
        if msg.startswith("@bot"):
            user_query = msg[4:].strip()
            
            # Define what happens when the bot finishes thinking
            def on_bot_reply(reply_text):
                # We use .after to ensure this runs on the main GUI thread safely
                self.window.after(0, lambda: self.add_message_bubble(reply_text, False, datetime.now().strftime("%I:%M %p"), "DeepSeek"))

            # Ask the bot (this runs in background)
            try:
                # If you haven't imported it at the top, we do a lazy import here
                from chat_bot_client import ChatBotClient
                
                # Create a persistent bot instance if it doesn't exist yet
                if not hasattr(self, 'bot_client'):
                    self.bot_client = ChatBotClient()
                
                # Send the query
                self.bot_client.ask(user_query, on_bot_reply)
                
            except Exception as e:
                self.add_message_bubble(f"System Error: {e}", False, ts, "System")
            return

        # 3. Game or Network Logic (Keep your existing logic here)
        if msg.startswith("GAME_"):
            self.send_callback(msg)
        else:
            self.send_callback(msg)

    def show_emoji_picker(self):
        picker = tk.Toplevel(self.window)
        picker.geometry("360x400")
        picker.title("Emojis")
        picker.configure(bg=COLORS['panel'])
        
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - 180
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - 200
        picker.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(picker, bg=COLORS['panel'], highlightthickness=0)
        scrollbar = tk.Scrollbar(picker, orient="vertical", command=canvas.yview, bg=COLORS['panel'], troughcolor=COLORS['panel'])
        scroll_frame = tk.Frame(canvas, bg=COLORS['panel'])

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        categories = {
            "Faces": ['😀','😃','😄','😁','😆','😅','🤣','😂','🙂','🙃','😉','😊','😇','🥰','😍','🤩','😘','😗','😚','😙'],
            "Gestures": ['👋','🤚','🖐','✋','🖖','👌','🤌','🤏','✌️','🤞','🤟','🤘','🤙','👈','👉','👆','🖕','👇','👍','👎','✊','👊','🤛','🤜','👏','🙌'],
            "Hearts": ['❤️','🧡','💛','💚','💙','💜','🖤','🤍','🤎','💔','❣️','💕','💞','💓','💗','💖','💘','💝'],
            "Objects": ['🔥','✨','🎉','🎊','🎁','🎈','🎂','🎄','🎃','🎗','🎟','🎫','🎖','🏆','🏅','🥇','🥈','🥉']
        }

        for cat, emojis in categories.items():
            tk.Label(scroll_frame, text=cat, font=get_font(10, "bold"), bg=COLORS['panel'], fg=COLORS['text_sec']).pack(anchor='w', pady=(10, 5))
            grid_frame = tk.Frame(scroll_frame, bg=COLORS['panel'])
            grid_frame.pack(fill='x')
            for i, char in enumerate(emojis):
                btn = tk.Button(grid_frame, text=char, font=("Apple Color Emoji", 18), 
                                bg=COLORS['panel'], fg='white', relief=tk.FLAT, bd=0, activebackground=COLORS['input_bg'],
                                command=lambda c=char: [self.entry.insert(tk.END, c), picker.destroy()])
                btn.grid(row=i//5, column=i%5, padx=5, pady=5)

    def on_connect(self):
        peer = simpledialog.askstring("Connect", "Enter nickname:", parent=self.window)
        if peer and peer.strip():
            self.peer_name = peer.strip()
            self.send_callback(f"connect {self.peer_name}")
            self.add_system_message(f"Connecting to {self.peer_name}...", datetime.now().strftime("%I:%M %p"))
            self.connect_btn.config(state=tk.DISABLED)
            self.game_btn.config(state=tk.NORMAL)

    def on_start_game(self):
        if not self.peer_name: return
        if self.game_window:
            self.game_window.window.lift()
            return
        try:
            # Change TicTacGame to TetrisGame here
            self.game_window = TetrisGame(self.window, self.send_callback, self.peer_name)
            self.add_system_message("Tetris Game started")
        except Exception as e:
            print(e)

    def on_who(self):
        self.send_callback("who")
        self.add_system_message("Checking online users...")
    
    def on_quit(self):
        if messagebox.askokcancel("Quit", "Quit Messages?"):
            self.send_callback("q")
            self.window.destroy()

    def show_search(self):
        s = simpledialog.askstring("Search", "Search:", parent=self.window)
        if s: messagebox.showinfo("Info", "Search logic would go here")

    def handle_incoming_message(self, message, sender, timestamp=None, msg_id=None):
        if message.startswith("GAME_") and self.game_window:
            self.game_window.receive_move(message)
            return
        if not timestamp: timestamp = datetime.now().strftime("%I:%M %p")
        self.add_message_bubble(message, False, timestamp, sender)

    def handle_system_message(self, message):
        self.add_system_message(message)
        if "connected to" in message.lower() and self.peer_name:
            self.contact_label.config(text=self.peer_name)
            self.status_label.config(text="Active Now")
        elif "disconnected" in message.lower():
            self.contact_label.config(text="Not Connected")
            self.status_label.config(text="Offline")
            self.connect_btn.config(state=tk.NORMAL)
            self.game_btn.config(state=tk.DISABLED)

    def handle_user_list(self, users):
        self.add_system_message(f"Online: {', '.join(users) if users else 'None'}")
        
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