"""
chat_client_class.py - Chat Client Class
Manages socket connection and integrates GUI with state machine
"""

import socket
import threading
import sys
from chat_utils import mysend, myrecv, SERVER_IP, SERVER_PORT
from client_state_machine import ClientStateMachine, S_OFFLINE, S_LOGGEDIN
from chat_gui import ChatGUI, LoginWindow

class ChatClient:
    """Main chat client class"""
    
    def __init__(self, server_ip=SERVER_IP, server_port=SERVER_PORT):
        """
        Initialize chat client
        
        Args:
            server_ip: Server IP address
            server_port: Server port
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = None
        self.state_machine = None
        self.gui = None
        self.client_name = None
        self.running = False
        self.receive_thread = None
    
    def connect_to_server(self):
        """Establish connection to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            print(f"[✓] Connected to server at {self.server_ip}:{self.server_port}")
            return True
        except Exception as e:
            print(f"[✗] Failed to connect to server: {e}")
            return False
    
    def login(self, nickname):
        """
        Send login request to server
        
        Args:
            nickname: User's nickname
        """
        import json
        
        self.client_name = nickname
        
        # Initialize state machine (no arguments!)
        self.state_machine = ClientStateMachine()
        self.state_machine.my_name = nickname
        
        # Send login message
        login_msg = json.dumps({
            'action': 'login',
            'name': nickname
        })
        
        try:
            mysend(self.socket, login_msg)
            print(f"[✓] Login request sent for {nickname}")
            return True
        except Exception as e:
            print(f"[✗] Login failed: {e}")
            return False
    
    def send_message(self, message):

        try:
            import json
            print(f"[DEBUG] send_message called with: '{message}'") 
        # Check if it's a command
            if message.startswith('connect '):
            # Extract peer name
                peer_name = message.split(' ', 1)[1].strip()
                formatted_msg = json.dumps({
                    'action': 'connect',
                    'to': peer_name
                })
            elif 'who' in message.lower() or message.strip() == 'who':
                formatted_msg = json.dumps({
                    'action': 'who'
                })
                print(f"[DEBUG] Sending who request: {formatted_msg}")
            elif message.startswith('q'):
                formatted_msg = json.dumps({
                    'action': 'quit'
                })
            elif isinstance(message, str) and message.startswith('{'):
            # Already JSON (from Create Group button)
                formatted_msg = message
            else:
            # Regular message - format with timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("%I:%M %p")
                formatted_msg = json.dumps({
                    'action': 'exchange',
                    'message': message,
                    'timestamp': timestamp
                })
        
            mysend(self.socket, formatted_msg)
        
        except Exception as e:
            print(f"[✗] Error sending message: {e}")
            if self.gui:
                self.gui.display_system_message(f"Failed to send message: {e}")
    
    def receive_messages(self):
        """Receive messages from server (runs in separate thread)"""
        print("[DEBUG] Receive thread started")
        while self.running:
            try:
                msg = myrecv(self.socket)
                
                if not msg:
                    print("[!] Server closed connection")
                    self.running = False
                    if self.gui:
                        try:
                            self.gui.display_system_message("Server disconnected")
                        except:
                            pass
                    break
                
                print(f"[DEBUG] Received: {msg[:100]}")
                
                # Process message through state machine
                self.state_machine.process_message(msg)
                
            except Exception as e:
                if self.running:
                    print(f"[✗] Error receiving message: {e}")
                    import traceback
                    traceback.print_exc()
                    self.running = False
                break
        
        # Clean up
        try:
            self.socket.close()
        except:
            pass
        
        print("[!] Receive thread terminated")
    
    def start(self):
        """Start the client"""
        # Show login window
        login_window = LoginWindow(self._on_login)
        nickname = login_window.run()
        
        if not nickname:
            print("[!] Login cancelled")
            return
        
        # Connect to server
        if not self.connect_to_server():
            print("[✗] Failed to connect to server")
            return
        
        # Login
        if not self.login(nickname):
            print("[✗] Login failed")
            return
        
        # Start receiving thread
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        # Create and start GUI
        self.gui = ChatGUI(self.send_message, nickname)
        self.state_machine.gui = self.gui
        
        # Run GUI (blocks until window is closed)
        self.gui.run()
        
        # Cleanup
        self.running = False
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
    
    def _on_login(self, nickname):
        """Callback for login window"""
        pass
    
    def stop(self):
        """Stop the client"""
        self.running = False
        try:
            if self.socket:
                self.socket.close()
        except:
            pass


if __name__ == "__main__":
    # For testing
    client = ChatClient()
    try:
        client.start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
        client.stop()