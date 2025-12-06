"""
chat_server.py - Complete Working Chat Server
Supports connections from anywhere (LAN or Internet)
"""

import socket
import select
import json
import sys

# Import your existing modules
try:
    import chat_group as grp
    from chat_utils import mysend, myrecv, CHAT_PORT
except ImportError:
    print("Error: Missing chat_group.py or chat_utils.py")
    print("Make sure these files are in the same directory!")
    sys.exit(1)

class Server:
    def __init__(self, host='0.0.0.0', port=None):
        """
        Initialize server
        
        Args:
            host: IP to bind to ('0.0.0.0' = all interfaces, allows external connections)
            port: Port number (default from chat_utils.py)
        """
        self.new_clients = [] 
        self.logged_name2sock = {} 
        self.logged_sock2name = {} 
        self.all_sockets = []
        self.group = grp.Group()
        
        # Use port from chat_utils or parameter
        self.port = port if port else CHAT_PORT
        self.host = host
        
        # Start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            self.all_sockets.append(self.server)
            
            print("=" * 60)
            print(f"✓ Server started successfully!")
            print(f"✓ Listening on: {self.host}:{self.port}")
            print("=" * 60)
            
            # Show local IP addresses
            self.show_connection_info()
            
        except Exception as e:
            print(f"✗ Failed to start server: {e}")
            sys.exit(1)

    def show_connection_info(self):
        """Display connection information for clients"""
        import subprocess
        
        print("\nConnection Information:")
        print("-" * 60)
        
        try:
            # Get local IP addresses
            if sys.platform == 'darwin':  # macOS
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                
                ips = []
                for i, line in enumerate(lines):
                    if 'inet ' in line and '127.0.0.1' not in line:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            ip = parts[1]
                            ips.append(ip)
                
                if ips:
                    print("Local Network IPs:")
                    for ip in ips:
                        print(f"  • {ip}:{self.port}")
                else:
                    print("  • No local network IP found")
                    
            else:  # Linux/Windows
                print(f"  • Use 'ifconfig' or 'ipconfig' to find your local IP")
        except:
            pass
        
        print(f"\nLocal clients use: 127.0.0.1:{self.port}")
        print(f"LAN clients use: <YOUR_LOCAL_IP>:{self.port}")
        print(f"Internet clients use: <YOUR_PUBLIC_IP>:{self.port}")
        print("-" * 60)
        print("\nWaiting for connections...\n")

    def new_client(self, sock):
        """Handle new client connection"""
        try:
            client_addr = sock.getpeername()
            print(f'[+] New client connected from {client_addr[0]}:{client_addr[1]}')
        except:
            print('[+] New client connected')
        
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        """Handle client login"""
        try:
            msg = json.loads(myrecv(sock))
            if len(msg) > 0 and msg.get('action') == 'login':
                name = msg.get('name', '')
                
                if not name:
                    mysend(sock, json.dumps({"action":"login", "status":"error"}))
                    return
                
                if self.group.is_member(name):  # Duplicate Check
                    mysend(sock, json.dumps({"action":"login", "status":"duplicate"}))
                    print(f'[!] {name} - duplicate login attempt')
                else:
                    self.group.join(name)
                    self.logged_name2sock[name] = sock
                    self.logged_sock2name[sock] = name
                    self.new_clients.remove(sock)
                    mysend(sock, json.dumps({"action":"login", "status":"ok"}))
                    print(f'[✓] {name} logged in')
        except Exception as e:
            print(f'[!] Login error: {e}')
            pass

    def logout(self, sock):
        """Handle client logout"""
        if sock in self.logged_sock2name:
            name = self.logged_sock2name[sock]
            
            # Disconnect from any active chats
            try:
                peers = self.group.list_me(name)
                if peers:
                    self.group.disconnect(name)
                    # Notify peers
                    for peer in peers:
                        if peer != name and peer in self.logged_name2sock:
                            peer_sock = self.logged_name2sock[peer]
                            try:
                                mysend(peer_sock, json.dumps({
                                    "action": "disconnect",
                                    "message": f"{name} disconnected"
                                }))
                            except:
                                pass
            except:
                pass
            
            # Remove from group and mappings
            self.group.leave(name)
            del self.logged_name2sock[name]
            del self.logged_sock2name[sock]
            self.all_sockets.remove(sock)
            
            try:
                sock.close()
            except:
                pass
            
            print(f'[-] {name} logged out')

    def handle_msg(self, from_sock):
        """Handle incoming messages from clients"""
        try:
            msg = myrecv(from_sock)
            if not msg or len(msg) == 0:
                self.logout(from_sock)
                return
                
            msg = json.loads(msg)
            action = msg.get('action', '')
            
            # 1. Connect Request
            if action == 'connect':
                to_name = msg.get('target', '')
                from_name = self.logged_sock2name.get(from_sock, '')
                
                if not from_name:
                    return
                
                if not self.group.is_member(to_name):
                    mysend(from_sock, json.dumps({"action":"connect", "status":"no-user"}))
                    print(f'[!] {from_name} tried to connect to non-existent user: {to_name}')
                else:
                    self.group.connect(from_name, to_name)
                    mysend(from_sock, json.dumps({"action":"connect", "status":"success"}))
                    print(f'[✓] {from_name} connected to {to_name}')
                    
                    # Notify the other person
                    to_sock = self.logged_name2sock[to_name]
                    mysend(to_sock, json.dumps({
                        "action":"connect", 
                        "status":"request", 
                        "from":from_name
                    }))

            # 2. Exchange (Chat / Game Moves)
            elif action == 'exchange':
                from_name = self.logged_sock2name.get(from_sock, '')
                if not from_name:
                    return
                
                # Get everyone in the group (the peer)
                peers = self.group.list_me(from_name)
                message = msg.get('message', '')
                
                # Log message (but not game moves)
                if not message.startswith('GAME_'):
                    print(f'[MSG] {from_name}: {message[:50]}...' if len(message) > 50 else f'[MSG] {from_name}: {message}')
                
                for peer in peers:
                    if peer != from_name:
                        to_sock = self.logged_name2sock.get(peer)
                        if to_sock:
                            # Forward the message exactly as is
                            mysend(to_sock, json.dumps({
                                "action":"exchange", 
                                "from": from_name, 
                                "message": message
                            }))

            # 3. Disconnect
            elif action == 'disconnect':
                from_name = self.logged_sock2name.get(from_sock, '')
                if not from_name:
                    return
                    
                peers = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                print(f'[-] {from_name} disconnected from chat')
                
                # Notify others
                for peer in peers:
                    if peer != from_name and peer in self.logged_name2sock:
                        to_sock = self.logged_name2sock[peer]
                        try:
                            mysend(to_sock, json.dumps({
                                "action":"disconnect",
                                "message": f"{from_name} disconnected"
                            }))
                        except:
                            pass

            # 4. List Users (Who)
            elif action == 'list':
                from_name = self.logged_sock2name.get(from_sock, '')
                if not from_name:
                    return
                    
                user_list = self.group.list_all(from_name)
                mysend(from_sock, json.dumps({
                    "action":"list", 
                    "results":user_list
                }))

        except Exception as e:
            print(f'[!] Error handling message: {e}')
            self.logout(from_sock)

    def run(self):
        """Main server loop"""
        print("Server is running. Press Ctrl+C to stop.\n")
        
        try:
            while True:
                read, _, _ = select.select(self.all_sockets, [], [])
                for sock in read:
                    if sock == self.server:
                        newsock, addr = self.server.accept()
                        self.new_client(newsock)
                    elif sock in self.new_clients:
                        self.login(sock)
                    elif sock in self.logged_sock2name:
                        self.handle_msg(sock)
        except KeyboardInterrupt:
            print("\n\n[!] Server shutting down...")
            self.shutdown()
        except Exception as e:
            print(f"\n[!] Server error: {e}")
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown"""
        print("[!] Closing all connections...")
        
        # Close all client sockets
        for sock in list(self.all_sockets):
            if sock != self.server:
                try:
                    sock.close()
                except:
                    pass
        
        # Close server socket
        try:
            self.server.close()
        except:
            pass
        
        print("[✓] Server stopped")

if __name__ == '__main__':
    # Allow custom port from command line
    port = None
    host = '0.0.0.0'  # Listen on all interfaces
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            print("Usage: python3 chat_server.py [port]")
            sys.exit(1)
    
    server = Server(host=host, port=port)
    server.run()