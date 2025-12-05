#!/usr/bin/env python3
"""
Simple Chat Server for Two-Person Real-Time Communication
Perfect for developers collaborating through GitHub
"""

import socket
import threading
import json
from datetime import datetime

class SimpleChatServer:
    def __init__(self, host='0.0.0.0', port=5555):
        """Initialize the chat server
        
        Args:
            host: Server host (0.0.0.0 allows external connections)
            port: Server port (default 5555)
        """
        self.host = host
        self.port = port
        self.clients = {}  # {client_socket: username}
        self.message_history = []  # Store last 50 messages
        
    def start(self):
        """Start the chat server"""
        # Create socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind and listen
        self.server.bind((self.host, self.port))
        self.server.listen(2)  # Max 2 connections for pair programming
        
        print(f"""
        ╔════════════════════════════════════════╗
        ║     SIMPLE CHAT SERVER STARTED        ║
        ╠════════════════════════════════════════╣
        ║  Server IP: {self.get_local_ip():20} ║
        ║  Port: {self.port:20}     ║
        ║  Max Users: 2                          ║
        ╚════════════════════════════════════════╝
        
        Share this IP with your partner: {self.get_local_ip()}:{self.port}
        """)
        
        # Accept connections
        self.accept_connections()
        
    def get_local_ip(self):
        """Get local IP address"""
        try:
            # Create a dummy socket to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def accept_connections(self):
        """Accept incoming connections"""
        while True:
            try:
                client_socket, address = self.server.accept()
                
                # Handle client in new thread
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                print(f"Error accepting connection: {e}")
                break
    
    def handle_client(self, client_socket, address):
        """Handle individual client connection"""
        username = None
        
        try:
            # Receive username
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                return
                
            message = json.loads(data)
            username = message.get('username', f'User_{address[0]}')
            
            # Check if room is full
            if len(self.clients) >= 2:
                error_msg = {
                    'type': 'error',
                    'message': 'Chat room is full (max 2 users)'
                }
                client_socket.send(json.dumps(error_msg).encode('utf-8'))
                client_socket.close()
                return
            
            # Add client
            self.clients[client_socket] = username
            print(f"✅ {username} connected from {address[0]}")
            
            # Send welcome message
            welcome = {
                'type': 'system',
                'message': f'Connected to chat server',
                'timestamp': datetime.now().isoformat(),
                'users': list(self.clients.values())
            }
            client_socket.send(json.dumps(welcome).encode('utf-8'))
            
            # Send message history
            for msg in self.message_history[-20:]:  # Last 20 messages
                client_socket.send(json.dumps(msg).encode('utf-8'))
            
            # Notify others
            self.broadcast({
                'type': 'user_joined',
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'users': list(self.clients.values())
            }, exclude=client_socket)
            
            # Handle messages
            while True:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                try:
                    message = json.loads(data)
                    message['username'] = username
                    message['timestamp'] = datetime.now().isoformat()
                    
                    # Add to history
                    if message['type'] == 'message':
                        self.message_history.append(message)
                        if len(self.message_history) > 50:
                            self.message_history = self.message_history[-50:]
                    
                    # Broadcast message
                    self.broadcast(message, exclude=client_socket)
                    
                    # Echo back to sender with confirmation
                    message['confirmed'] = True
                    client_socket.send(json.dumps(message).encode('utf-8'))
                    
                except json.JSONDecodeError:
                    print(f"Invalid message from {username}")
                    
        except Exception as e:
            print(f"Error handling {username or address}: {e}")
            
        finally:
            # Remove client
            if client_socket in self.clients:
                username = self.clients[client_socket]
                del self.clients[client_socket]
                print(f"❌ {username} disconnected")
                
                # Notify others
                self.broadcast({
                    'type': 'user_left',
                    'username': username,
                    'timestamp': datetime.now().isoformat(),
                    'users': list(self.clients.values())
                })
                
            client_socket.close()
    
    def broadcast(self, message, exclude=None):
        """Broadcast message to all clients except excluded one"""
        for client_socket in list(self.clients.keys()):
            if client_socket != exclude:
                try:
                    client_socket.send(json.dumps(message).encode('utf-8'))
                except:
                    # Remove dead connection
                    if client_socket in self.clients:
                        del self.clients[client_socket]

def main():
    """Run the server"""
    import sys
    
    # Get port from command line
    port = 5555
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            print("Invalid port number, using default 5555")
    
    # Start server
    server = SimpleChatServer(port=port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n\n🛑 Server shutting down...")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    main()