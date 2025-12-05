import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox

class ChatClient:
    def __init__(self):
        # 1. SETUP NETWORK
        self.PORT = 12345
        
        # Pop-up to ask for IP (so you don't have to edit code)
        # Use 'localhost' if testing alone. Use Host's IP if with a friend.
        self.HOST = simpledialog.askstring("Connect", "Enter Server IP Address:", initialvalue="localhost")
        if not self.HOST: exit()
        
        self.nickname = simpledialog.askstring("Identity", "Choose a Nickname:")
        if not self.nickname: exit()

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((self.HOST, self.PORT))
        except:
            messagebox.showerror("Error", f"Could not connect to server at {self.HOST}")
            exit()

        # 2. SETUP GUI
        self.root = tk.Tk()
        self.root.title(f"Chat App - Logged in as: {self.nickname}")
        self.root.geometry("500x600")

        # Chat Display Area
        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled', wrap=tk.WORD)
        self.chat_area.pack(padx=10, pady=10, expand=True, fill='both')
        
        # Configure "Tags" for alignment/color (Requirement: Dual-sided chat)
        self.chat_area.tag_config('self', foreground='blue', justify='right')
        self.chat_area.tag_config('other', foreground='black', justify='left')
        self.chat_area.tag_config('system', foreground='gray', justify='center', font=("Arial", 10, "italic"))

        # Input Area
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=10, fill='x')

        self.msg_entry = tk.Entry(self.input_frame, font=("Arial", 12))
        self.msg_entry.pack(side='left', fill='x', expand=True)
        self.msg_entry.bind("<Return>", self.send_message) # Press Enter to send

        self.send_btn = tk.Button(self.input_frame, text="Send", command=self.send_message, bg="#dddddd")
        self.send_btn.pack(side='right', padx=5)

        # 3. START LISTENING THREAD
        self.running = True
        gui_thread = threading.Thread(target=self.receive_loop)
        gui_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.mainloop()

    def receive_loop(self):
        """Listens for incoming messages from the server."""
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    # Message from others or system
                    if "joined the chat!" in message or "left the chat!" in message:
                         self.display_message(message, 'system')
                    else:
                         self.display_message(message, 'other')
            except ConnectionAbortedError:
                break
            except:
                print("Connection lost.")
                self.client.close()
                break

    def send_message(self, event=None):
        """Sends your message to the server and displays it locally."""
        msg = self.msg_entry.get()
        if not msg: return

        self.msg_entry.delete(0, 'end')
        
        # 1. Show my own message on the RIGHT side immediately
        self.display_message(f"{self.nickname}: {msg}", 'self')

        # 2. Send to server so others can see it
        full_msg = f"{self.nickname}: {msg}"
        self.client.send(full_msg.encode('utf-8'))

    def display_message(self, message, tag):
        """Helper to insert text into the scrolled window."""
        self.chat_area.config(state='normal')
        self.chat_area.insert('end', message + '\n', tag)
        self.chat_area.config(state='disabled')
        self.chat_area.yview('end') # Auto-scroll to bottom

    def stop(self):
        """Clean shutdown."""
        self.running = False
        self.client.close()
        self.root.destroy()

if __name__ == "__main__":
    ChatClient()