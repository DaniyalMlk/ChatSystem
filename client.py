import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import queue

# Try to import the bot, but prevent crashing if it's missing
try:
    from chat_bot_client import ChatBotClient
except ImportError:
    class ChatBotClient:
        def set_personality(self, p): pass
        def chat(self, p): return "Error: chat_bot_client.py missing"

class ChatClient:
    def __init__(self):
        # --- 1. SETUP THE ROOT WINDOW FIRST (Crucial for Mac) ---
        self.root = tk.Tk()
        self.root.withdraw() # Hide it while we ask for names

        # --- 2. SETUP DATA QUEUE (Thread-Safe Mailbox) ---
        self.msg_queue = queue.Queue()

        # --- 3. ASK QUESTIONS (Using self.root as parent) ---
        self.PORT = 12345
        
        self.HOST = simpledialog.askstring("Connect", "Enter Server IP:", 
                                           parent=self.root, 
                                           initialvalue="localhost")
        if not self.HOST: 
            self.root.destroy()
            return

        self.nickname = simpledialog.askstring("Identity", "Choose a Nickname:", 
                                               parent=self.root)
        if not self.nickname: 
            self.root.destroy()
            return

        # --- 4. CONNECT TO NETWORK ---
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((self.HOST, self.PORT))
        except:
            messagebox.showerror("Error", f"Could not connect to {self.HOST}")
            self.root.destroy()
            return

        # --- 5. FINISH GUI SETUP ---
        self.root.deiconify() # Show the window now
        self.root.title(f"Chat: {self.nickname}")
        self.root.geometry("500x600")
        self.root.configure(bg="#f0f0f0")

        # Chat Area
        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled', wrap=tk.WORD, 
                                                   bg="white", font=("Arial", 11))
        self.chat_area.pack(padx=10, pady=10, expand=True, fill='both')

        # Tags for colors
        self.chat_area.tag_config('self', foreground='blue', justify='right', rmargin=10)
        self.chat_area.tag_config('other', foreground='black', justify='left', lmargin=10)
        self.chat_area.tag_config('bot', foreground='purple', justify='left', font=("Arial", 11, "italic"))
        self.chat_area.tag_config('system', foreground='gray', justify='center', font=("Arial", 9))

        # Input Area
        self.input_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.input_frame.pack(padx=10, pady=10, fill='x')

        self.msg_entry = tk.Entry(self.input_frame, font=("Arial", 12))
        self.msg_entry.pack(side='left', fill='x', expand=True)
        self.msg_entry.bind("<Return>", self.process_message) 

        self.send_btn = tk.Button(self.input_frame, text="Send", command=self.process_message, bg="#0084ff")
        self.send_btn.pack(side='right', padx=5)

        self.info_lbl = tk.Label(self.root, text="Tip: Type '@bot hello' to talk to AI", bg="#f0f0f0", fg="gray")
        self.info_lbl.pack(side='bottom', pady=5)

        # Initialize Bot
        self.bot = ChatBotClient()
        self.bot.set_personality("Smart")

        # --- 6. START PROCESSES ---
        # A. Start the Network Thread (Background)
        self.running = True
        threading.Thread(target=self.receive_loop, daemon=True).start()

        # B. Start the GUI Checker (Main Thread)
        self.root.after(100, self.check_queue)
        
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.mainloop()

    def receive_loop(self):
        """Background thread: Listens to server, puts msg in Queue."""
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    self.msg_queue.put(message) # <--- SAFELY DROP IN MAILBOX
            except:
                self.client.close()
                break

    def check_queue(self):
        """Main Thread: Checks mailbox every 100ms and updates screen."""
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                
                # Decide color/tag based on message content
                tag = 'other'
                if msg.startswith("ChatBot:"): tag = 'bot'
                elif "joined" in msg or "left" in msg: tag = 'system'
                
                self.display_text(msg, tag)
        except queue.Empty:
            pass
        
        if self.running:
            self.root.after(100, self.check_queue) # Run again in 0.1s

    def display_text(self, text, tag):
        self.chat_area.config(state='normal')
        self.chat_area.insert('end', text + '\n', tag)
        self.chat_area.see('end')
        self.chat_area.config(state='disabled')

    def process_message(self, event=None):
        msg = self.msg_entry.get()
        if not msg: return
        self.msg_entry.delete(0, 'end')

        # Show locally
        self.display_text(f"{self.nickname}: {msg}", 'self')

        # Send to server
        self.client.send(f"{self.nickname}: {msg}".encode('utf-8'))

        # Check Bot
        if msg.startswith("@bot"):
            prompt = msg.replace("@bot", "").strip()
            threading.Thread(target=self.handle_bot_response, args=(prompt,)).start()

    def handle_bot_response(self, prompt):
        self.msg_queue.put("Bot is thinking...")
        reply = self.bot.chat(prompt)
        bot_msg = f"ChatBot: {reply}"
        
        self.client.send(bot_msg.encode('utf-8')) # Send to others
        self.msg_queue.put(bot_msg)               # Show locally

    def stop(self):
        self.running = False
        self.client.close()
        self.root.destroy()

if __name__ == "__main__":
    ChatClient()