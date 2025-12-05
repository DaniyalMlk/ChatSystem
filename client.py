import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox

# Import the bot class
try:
    from chat_bot_client import ChatBotClient
except ImportError:
    # If file is missing, create a dummy class so app doesn't crash
    class ChatBotClient:
        def set_personality(self, p): pass
        def chat(self, p): return "Error: chat_bot_client.py missing"

class ChatClient:
    def __init__(self):
        # --- NETWORK SETUP ---
        self.PORT = 12345
        
        # Ask for connection details
        self.HOST = simpledialog.askstring("Connect", "Enter Server IP (or 'localhost'):", initialvalue="localhost")
        if not self.HOST: exit()
        
        self.nickname = simpledialog.askstring("Identity", "Choose a Nickname:")
        if not self.nickname: exit()

        # Connect to Server
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((self.HOST, self.PORT))
        except:
            messagebox.showerror("Connection Error", f"Could not connect to {self.HOST}")
            exit()

        # --- CHATBOT SETUP ---
        self.bot = ChatBotClient()
        self.bot.set_personality("Smart") 

        # --- GUI SETUP ---
        self.root = tk.Tk()
        self.root.title(f"Chat: {self.nickname}")
        self.root.geometry("500x600")
        self.root.configure(bg="#f0f0f0")

        # 1. Chat Display
        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled', wrap=tk.WORD, bg="white", font=("Arial", 11))
        self.chat_area.pack(padx=10, pady=10, expand=True, fill='both')

        self.chat_area.tag_config('self', foreground='blue', justify='right', rmargin=10)
        self.chat_area.tag_config('other', foreground='black', justify='left', lmargin=10)
        self.chat_area.tag_config('bot', foreground='purple', justify='left', font=("Arial", 11, "italic"))
        self.chat_area.tag_config('system', foreground='gray', justify='center', font=("Arial", 9))

        # 2. Input Area
        self.input_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.input_frame.pack(padx=10, pady=10, fill='x')

        self.msg_entry = tk.Entry(self.input_frame, font=("Arial", 12))
        self.msg_entry.pack(side='left', fill='x', expand=True)
        self.msg_entry.bind("<Return>", self.process_message) 

        self.send_btn = tk.Button(self.input_frame, text="Send", command=self.process_message, bg="#0084ff")
        self.send_btn.pack(side='right', padx=5)

        self.info_lbl = tk.Label(self.root, text="Tip: Type '@bot hello' to talk to AI", bg="#f0f0f0", fg="gray")
        self.info_lbl.pack(side='bottom', pady=5)

        # --- START THREADS ---
        self.running = True
        threading.Thread(target=self.receive_loop, daemon=True).start()

        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.mainloop()

    def receive_loop(self):
        """Listens for messages from the Server."""
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    # Determine tag
                    tag = 'other'
                    if message.startswith("ChatBot:"): tag = 'bot'
                    elif "joined" in message or "left" in message: tag = 'system'
                    
                    # CRITICAL FIX FOR MAC: Use display_message safe wrapper
                    self.display_message(message, tag)
                    
            except ConnectionAbortedError:
                break
            except:
                self.client.close()
                break

    def display_message(self, message, tag):
        """
        Thread-Safe GUI Update.
        If this is called from a background thread, it schedules the work
        on the main thread using root.after().
        """
        def _update():
            self.chat_area.config(state='normal')
            self.chat_area.insert('end', message + '\n', tag)
            self.chat_area.see('end') 
            self.chat_area.config(state='disabled')
            
        # This is the magic line that fixes the crash:
        self.root.after(0, _update)

    def process_message(self, event=None):
        msg = self.msg_entry.get()
        if not msg: return

        self.msg_entry.delete(0, 'end')

        # Display my own message
        self.display_message(f"{self.nickname}: {msg}", 'self')

        # Send to server
        full_msg = f"{self.nickname}: {msg}"
        self.client.send(full_msg.encode('utf-8'))

        # Check for Bot
        if msg.startswith("@bot"):
            prompt = msg.replace("@bot", "").strip()
            threading.Thread(target=self.handle_bot_response, args=(prompt,)).start()

    def handle_bot_response(self, prompt):
        self.display_message("Bot is thinking...", 'system')
        reply = self.bot.chat(prompt)
        bot_msg = f"ChatBot: {reply}"
        self.client.send(bot_msg.encode('utf-8'))
        self.display_message(bot_msg, 'bot')

    def stop(self):
        self.running = False
        self.client.close()
        self.root.destroy()

if __name__ == "__main__":
    ChatClient()