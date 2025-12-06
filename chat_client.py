#!/usr/bin/env python3
"""
Fixed Simple Chat Client with better GUI handling
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
import json
from datetime import datetime
import sys
import os

class SimpleChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Dev Chat")
        self.root.geometry("800x600")
        
        # Connection variables
        self.socket = None
        self.connected = False
        self.username = os.getenv('USER', 'Developer')
        
        # Color scheme
        self.colors = {
            'bg': '#f0f0f0',
            'fg': '#333333',
            'input': '#ffffff',
            'button': '#007ACC',
            'button_text': '#ffffff',
            'my_msg': '#e3f2fd',
            'other_msg': '#f5f5f5',
            'system': '#fff3cd',
            'border': '#cccccc'
        }
        
        self.root.configure(bg=self.colors['bg'])
        self.create_connection_screen()
        
    def create_connection_screen(self):
        """Create the connection/login screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        container = tk.Frame(self.root, bg=self.colors['bg'])
        container.place(relx=0.5, rely=0.5, anchor='center')
        
        title = tk.Label(
            container,
            text="👥 Simple Dev Chat",
            font=('Segoe UI', 24, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
        title.pack(pady=20)
        
        conn_frame = tk.Frame(container, bg='white', relief='solid', bd=1)
        conn_frame.pack(padx=20, pady=10)
        
        inner = tk.Frame(conn_frame, bg='white')
        inner.pack(padx=30, pady=30)
        
        tk.Label(inner, text="Server IP:", font=('Segoe UI', 11), bg='white').grid(row=0, column=0, sticky='e', padx=10, pady=10)
        self.server_entry = tk.Entry(inner, font=('Segoe UI', 11), width=20, relief='solid', bd=1)
        self.server_entry.insert(0, "127.0.0.1")
        self.server_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(inner, text="Port:", font=('Segoe UI', 11), bg='white').grid(row=1, column=0, sticky='e', padx=10, pady=10)
        self.port_entry = tk.Entry(inner, font=('Segoe UI', 11), width=20, relief='solid', bd=1)
        self.port_entry.insert(0, "5555")
        self.port_entry.grid(row=1, column=1, padx=10, pady=10)
        
        tk.Label(inner, text="Your Name:", font=('Segoe UI', 11), bg='white').grid(row=2, column=0, sticky='e', padx=10, pady=10)
        self.username_entry = tk.Entry(inner, font=('Segoe UI', 11), width=20, relief='solid', bd=1)
        self.username_entry.insert(0, self.username)
        self.username_entry.grid(row=2, column=1, padx=10, pady=10)
        
        connect_btn = tk.Button(
            inner,
            text="Connect",
            command=self.connect_to_server,
            bg=self.colors['button'],
            fg=self.colors['button_text'],
            font=('Segoe UI', 11, 'bold'),
            padx=40,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        connect_btn.grid(row=3, column=0, columnspan=2, pady=20)
        
        info_text = tk.Label(
            container,
            text="💡 Tip: Share your IP with your partner\nRun 'python simple_chat_server.py' first",
            font=('Segoe UI', 9),
            bg=self.colors['bg'],
            fg='#666666',
            justify='center'
        )
        info_text.pack(pady=10)
        
        self.root.bind('<Return>', lambda e: self.connect_to_server())
        
    def connect_to_server(self):
        """Connect to the chat server"""
        server_ip = self.server_entry.get().strip()
        port = self.port_entry.get().strip()
        self.username = self.username_entry.get().strip()
        
        if not server_ip or not port or not self.username:
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        try:
            port = int(port)
        except:
            messagebox.showerror("Error", "Invalid port number")
            return
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((server_ip, port))
            
            # Send username
            self.socket.send(json.dumps({
                'type': 'connect',
                'username': self.username
            }).encode('utf-8'))
            
            self.connected = True
            
            # Create chat interface FIRST
            self.create_chat_interface()
            
            # THEN start receive thread
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
            # Add welcome message
            self.add_system_message(f"Connected to chat server as {self.username}")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect:\n{str(e)}")
            
    def create_chat_interface(self):
        """Create the main chat interface with proper initialization"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header
        header = tk.Frame(main_container, bg=self.colors['bg'], height=40)
        header.pack(fill='x', pady=(0, 10))
        header.pack_propagate(False)
        
        # Title and status
        title_frame = tk.Frame(header, bg=self.colors['bg'])
        title_frame.pack(side='left', fill='y')
        
        tk.Label(
            title_frame,
            text=f"💬 {self.username}",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        ).pack(side='left', pady=5)
        
        self.status_label = tk.Label(
            title_frame,
            text=" • Connected",
            font=('Segoe UI', 10),
            bg=self.colors['bg'],
            fg='#4CAF50'
        )
        self.status_label.pack(side='left', pady=5)
        
        # Users online
        self.users_label = tk.Label(
            header,
            text="Users: Loading...",
            font=('Segoe UI', 10),
            bg=self.colors['bg'],
            fg='#666666'
        )
        self.users_label.pack(side='right', padx=10, pady=5)
        
        # Chat display with proper frame
        chat_container = tk.Frame(main_container, bg=self.colors['bg'])
        chat_container.pack(fill='both', expand=True, pady=(0, 10))
        
        # Create scrolled text widget
        self.chat_display = scrolledtext.ScrolledText(
            chat_container,
            wrap='word',
            font=('Segoe UI', 10),
            bg='white',
            fg=self.colors['fg'],
            relief='solid',
            bd=1,
            padx=10,
            pady=10,
            height=20
        )
        self.chat_display.pack(fill='both', expand=True)
        
        # Configure tags
        self.chat_display.tag_config('my_message', background=self.colors['my_msg'], 
                                     lmargin1=10, lmargin2=10, rmargin=100)
        self.chat_display.tag_config('other_message', background=self.colors['other_msg'], 
                                     lmargin1=10, lmargin2=10, rmargin=100)
        self.chat_display.tag_config('system', background=self.colors['system'], 
                                     justify='center', font=('Segoe UI', 9, 'italic'))
        self.chat_display.tag_config('username', font=('Segoe UI', 10, 'bold'))
        self.chat_display.tag_config('timestamp', foreground='#999999', font=('Segoe UI', 8))
        
        # Initially editable for testing
        self.chat_display.insert('1.0', "Chat connected. Type a message below and press Enter to send.\n\n")
        self.chat_display.config(state='disabled')
        
        # Input area frame
        input_container = tk.Frame(main_container, bg=self.colors['bg'])
        input_container.pack(fill='x', pady=(0, 5))
        
        # Message input with frame
        input_frame = tk.Frame(input_container, bg=self.colors['bg'])
        input_frame.pack(fill='x')
        
        # Text input
        self.message_input = tk.Text(
            input_frame,
            height=3,
            font=('Segoe UI', 10),
            bg='white',
            fg=self.colors['fg'],
            relief='solid',
            bd=1,
            padx=10,
            pady=10,
            width=50
        )
        self.message_input.pack(side='left', fill='both', expand=True)
        
        # Send button
        self.send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            bg=self.colors['button'],
            fg=self.colors['button_text'],
            font=('Segoe UI', 10, 'bold'),
            padx=20,
            relief='flat',
            cursor='hand2',
            height=2
        )
        self.send_btn.pack(side='right', padx=(10, 0), fill='y')
        
        # Keyboard shortcuts info
        shortcut_label = tk.Label(
            main_container,
            text="Enter: Send message  |  Shift+Enter: New line  |  Ctrl+Q: Quit",
            font=('Segoe UI', 8),
            bg=self.colors['bg'],
            fg='#999999'
        )
        shortcut_label.pack()
        
        # Bind events
        self.message_input.bind('<Return>', self.handle_enter)
        self.message_input.bind('<KeyRelease>', self.check_input)
        self.root.bind('<Control-q>', lambda e: self.quit_app())
        
        # Focus on input
        self.message_input.focus_set()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Force update
        self.root.update_idletasks()
        
    def check_input(self, event=None):
        """Enable/disable send button based on input"""
        content = self.message_input.get('1.0', 'end-1c').strip()
        if content:
            self.send_btn.config(state='normal')
        else:
            self.send_btn.config(state='disabled')
            
    def handle_enter(self, event):
        """Handle Enter key press"""
        if event.state & 0x0001:  # Shift is pressed
            return  # Let default behavior add newline
        else:
            self.send_message()
            return 'break'  # Prevent default newline
            
    def send_message(self):
        """Send a message"""
        message = self.message_input.get('1.0', 'end-1c').strip()
        
        if not message:
            return
            
        if not self.connected or not self.socket:
            self.add_system_message("Not connected to server!")
            return
        
        try:
            # Send to server
            msg_data = {
                'type': 'message',
                'content': message
            }
            self.socket.send(json.dumps(msg_data).encode('utf-8'))
            
            # Clear input immediately
            self.message_input.delete('1.0', 'end')
            
            # Debug message
            print(f"Sent: {message}")
            
        except Exception as e:
            self.add_system_message(f"Failed to send: {str(e)}")
            print(f"Send error: {e}")
            
    def receive_messages(self):
        """Receive messages from server"""
        while self.connected:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                # Parse message
                message = json.loads(data)
                
                # Use GUI thread for updates
                self.root.after(0, self.handle_message, message)
                
            except json.JSONDecodeError as e:
                print(f"JSON error: {e}")
                continue
            except Exception as e:
                print(f"Receive error: {e}")
                break
        
        # Disconnected
        self.connected = False
        self.root.after(0, self.handle_disconnect)
        
    def handle_disconnect(self):
        """Handle disconnection in GUI thread"""
        self.add_system_message("Disconnected from server")
        if hasattr(self, 'status_label'):
            self.status_label.config(text=" • Disconnected", fg='#f44336')
        if hasattr(self, 'send_btn'):
            self.send_btn.config(state='disabled')
            
    def handle_message(self, message):
        """Handle received message in GUI thread"""
        msg_type = message.get('type')
        
        if msg_type == 'message':
            username = message.get('username')
            content = message.get('content')
            timestamp = message.get('timestamp')
            confirmed = message.get('confirmed', False)
            
            if confirmed:
                # Our message confirmed
                self.add_chat_message(username, content, timestamp, is_own=True)
            else:
                # Message from other user
                self.add_chat_message(username, content, timestamp, is_own=False)
                
        elif msg_type == 'system':
            self.add_system_message(message.get('message', ''))
            
            # Update users list
            users = message.get('users', [])
            if users:
                self.update_users(users)
                
        elif msg_type == 'user_joined':
            username = message.get('username')
            self.add_system_message(f"{username} joined the chat")
            
            users = message.get('users', [])
            if users:
                self.update_users(users)
                
        elif msg_type == 'user_left':
            username = message.get('username')
            self.add_system_message(f"{username} left the chat")
            
            users = message.get('users', [])
            if users:
                self.update_users(users)
                
        elif msg_type == 'error':
            self.add_system_message(f"Error: {message.get('message', 'Unknown error')}")
            
    def add_chat_message(self, username, content, timestamp, is_own=False):
        """Add a chat message to display"""
        if not hasattr(self, 'chat_display'):
            return
            
        self.chat_display.config(state='normal')
        
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime('%H:%M')
        except:
            time_str = datetime.now().strftime('%H:%M')
        
        # Add message with proper formatting
        if is_own:
            self.chat_display.insert('end', f"{username} ", ('username', 'my_message'))
            self.chat_display.insert('end', f"• {time_str}\n", ('timestamp', 'my_message'))
            self.chat_display.insert('end', f"{content}\n\n", 'my_message')
        else:
            self.chat_display.insert('end', f"{username} ", ('username', 'other_message'))
            self.chat_display.insert('end', f"• {time_str}\n", ('timestamp', 'other_message'))
            self.chat_display.insert('end', f"{content}\n\n", 'other_message')
        
        self.chat_display.config(state='disabled')
        self.chat_display.see('end')
        
    def add_system_message(self, message):
        """Add a system message"""
        if not hasattr(self, 'chat_display'):
            return
            
        self.chat_display.config(state='normal')
        self.chat_display.insert('end', f"— {message} —\n\n", 'system')
        self.chat_display.config(state='disabled')
        self.chat_display.see('end')
        
    def update_users(self, users):
        """Update the users list"""
        if not hasattr(self, 'users_label'):
            return
            
        if len(users) == 1:
            self.users_label.config(text=f"Users: {users[0]} (waiting for partner...)")
        else:
            self.users_label.config(text=f"Users: {', '.join(users)}")
            
    def on_closing(self):
        """Handle window closing"""
        self.quit_app()
        
    def quit_app(self):
        """Quit the application"""
        if self.connected and self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.root.quit()

def main():
    """Run the chat client"""
    root = tk.Tk()
    
    app = SimpleChatClient(root)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
        if ':' in server_ip:
            ip, port = server_ip.split(':')
            app.server_entry.delete(0, 'end')
            app.server_entry.insert(0, ip)
            app.port_entry.delete(0, 'end')
            app.port_entry.insert(0, port)
    
    root.mainloop()

if __name__ == "__main__":
    main()