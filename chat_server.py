"""
chat_server.py - COMPLETE VERSION WITH GROUP CHAT SUPPORT
Ready to copy and paste - no manual edits needed!
"""
import socket
import select
import json
from chat_utils import mysend, myrecv, CHAT_PORT
from chat_group import Group

class Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', CHAT_PORT))
        self.server_socket.listen(5)
        
        # Client tracking
        self.clients = {}  # {name: socket}
        self.logged_name2sock = {}  # name -> socket
        self.logged_sock2name = {}  # socket -> name
        
        # Group management
        self.group = Group()
        
        # Socket lists for select
        self.all_sockets = [self.server_socket]
        
        print(f"[SERVER] Started on port {CHAT_PORT}")
        print("[SERVER] Waiting for connections...")
    
    def run(self):
        """Main server loop"""
        while True:
            try:
                read_ready, _, _ = select.select(self.all_sockets, [], [], 1)
                
                for sock in read_ready:
                    if sock == self.server_socket:
                        # New connection
                        self.handle_new_connection()
                    else:
                        # Existing client message
                        self.handle_client_message(sock)
                        
            except KeyboardInterrupt:
                print("\n[SERVER] Shutting down...")
                break
            except Exception as e:
                print(f"[SERVER] Error: {e}")
        
        self.shutdown()
    
    def handle_new_connection(self):
        """Handle new client connection"""
        try:
            client_socket, address = self.server_socket.accept()
            self.all_sockets.append(client_socket)
            print(f"[SERVER] New connection from {address}")
        except Exception as e:
            print(f"[SERVER] Error accepting connection: {e}")
    
    def handle_client_message(self, sock):
        """Handle message from existing client"""
        try:
            msg = myrecv(sock)
            
            if not msg:
                # Client disconnected
                self.handle_disconnect(sock)
                return
            
            # Parse JSON message
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                # Handle legacy text commands
                self.handle_legacy_command(sock, msg)
                return
            
            action = data.get('action', '')
            
            # Route to appropriate handler
            if action == 'login':
                self.handle_login(sock, data)
            elif action == 'connect':
                self.handle_connect(sock, data)
            elif action == 'create_group':  # NEW: Group chat support
                self.handle_create_group(sock, data)
            elif action == 'exchange':
                self.handle_exchange(sock, data)
            elif action == 'disconnect':
                self.handle_disconnect_request(sock, data)
            elif action == 'who':
                self.handle_who(sock)
            elif action == 'quit':
                self.handle_disconnect(sock)
            else:
                print(f"[SERVER] Unknown action: {action}")
                
        except Exception as e:
            print(f"[SERVER] Error handling message: {e}")
            self.handle_disconnect(sock)
    
    def handle_login(self, sock, data):
        """Handle login request"""
        try:
            name = data.get('name', '').strip()
            
            if not name:
                self.send_json(sock, {
                    'action': 'login',
                    'status': 'error',
                    'message': 'Name cannot be empty'
                })
                return
            
            if name in self.clients:
                self.send_json(sock, {
                    'action': 'login',
                    'status': 'error',
                    'message': 'Name already taken'
                })
                return
            
            # Register client
            self.clients[name] = sock
            self.logged_name2sock[name] = sock
            self.logged_sock2name[sock] = name
            self.group.add_user(name)
            
            # Send success
            self.send_json(sock, {
                'action': 'login',
                'status': 'success',
                'message': f'Welcome {name}!'
            })
            
            print(f"[SERVER] {name} logged in")
            
        except Exception as e:
            print(f"[SERVER] Login error: {e}")
    
    def handle_connect(self, sock, data):
        """Handle connection request (2-person chat)"""
        try:
            from_name = self.logged_sock2name.get(sock)
            to_name = data.get('to', '')
            
            if not from_name:
                print(f"[DEBUG] from_name is None!") 
                return
            
            if to_name not in self.clients:
                print(f"[DEBUG] {to_name} not in clients!") 
                self.send_json(sock, {
                    'action': 'connect',
                    'status': 'error',
                    'message': f'{to_name} not found'
                })
                return
            print(f"[DEBUG] Calling group.connect({from_name}, {to_name})")
            # Create 2-person group
            result = self.group.connect(from_name, to_name)
            print(f"[DEBUG] group.connect returned: {result}")
            
            if not result:
                self.send_json(sock, {
                    'action': 'connect',
                    'status': 'error',
                    'message': 'Connection failed (user busy?)'
                })
                return
            
            # Notify both users
            self.send_json(sock, {
                'action': 'connect',
                'status': 'success',
                'message': f'Connected to {to_name}'
            })
            
            to_sock = self.clients.get(to_name)
            if to_sock:
                self.send_json(to_sock, {
                    'action': 'connect',
                    'status': 'success',
                    'message': f'Connected to {from_name}'
                })
            
            print(f"[SERVER] {from_name} ↔ {to_name}")
            
        except Exception as e:
            print(f"[SERVER] Connect error: {e}")
    
    def handle_create_group(self, sock, data):
        """
        NEW METHOD: Handle group creation (3+ people)
        
        Expected data:
        {
            'action': 'create_group',
            'members': ['alice', 'bob', 'charlie']
        }
        """
        try:
            creator = self.logged_sock2name.get(sock)
            members_list = data.get('members', [])
            
            if not creator:
                self.send_json(sock, {
                    'action': 'error',
                    'message': 'You must be logged in'
                })
                return
            
            # Add creator if not in list
            if creator not in members_list:
                members_list.insert(0, creator)
            
            # Validate all members exist
            invalid_members = [m for m in members_list if m not in self.clients]
            if invalid_members:
                self.send_json(sock, {
                    'action': 'error',
                    'message': f'Users not found: {", ".join(invalid_members)}'
                })
                return
            
            # Create group using enhanced Group class
            success, result = self.group.create_group(members_list)
            
            if not success:
                self.send_json(sock, {
                    'action': 'error',
                    'message': result
                })
                return
            
            group_id = result
            
            # Notify all members
            for member in members_list:
                member_socket = self.clients.get(member)
                if member_socket:
                    self.send_json(member_socket, {
                        'action': 'group_created',
                        'group_id': group_id,
                        'members': members_list,
                        'message': f'Group chat created: {", ".join(members_list)}'
                    })
            
            print(f"[SERVER] Group {group_id} created with: {members_list}")
            
        except Exception as e:
            print(f"[SERVER] Create group error: {e}")
    
    def handle_exchange(self, sock, data):
        """Handle message exchange (works for both 2-person and group chats)"""
        try:
            sender = self.logged_sock2name.get(sock)
            message = data.get('message', '')
            timestamp = data.get('timestamp', '')
            
            if not sender:
                return
            
            # Get sender's group
            group_id = self.group.get_user_group(sender)
            if not group_id:
                self.send_json(sock, {
                    'action': 'error',
                    'message': 'You are not in any chat'
                })
                return
            
            # Get all other members in group
            recipients = self.group.get_other_members(sender)
            
            # Send to all recipients
            for recipient in recipients:
                recipient_sock = self.clients.get(recipient)
                if recipient_sock:
                    self.send_json(recipient_sock, {
                        'action': 'incoming',
                        'from': sender,  # IMPORTANT: Include sender name
                        'message': message,
                        'timestamp': timestamp
                    })
            
            print(f"[SERVER] {sender} → {recipients}: {message[:50]}...")
            
        except Exception as e:
            print(f"[SERVER] Exchange error: {e}")
    
    def handle_disconnect_request(self, sock, data):
        """Handle explicit disconnect request"""
        self.handle_disconnect(sock)
    
    def handle_who(self, sock):
        """Handle 'who is online' request"""
        try:
            requester = self.logged_sock2name.get(sock)
            users = [name for name in self.clients.keys() if name != requester]
            
            self.send_json(sock, {
                'action': 'who',
                'users': users
            })
            
        except Exception as e:
            print(f"[SERVER] Who error: {e}")
    
    def handle_disconnect(self, sock):
        """Handle client disconnection"""
        try:
            name = self.logged_sock2name.get(sock)
            
            if name:
                # Get group info before disconnecting
                group_id, remaining = self.group.disconnect(name)
                
                # Notify remaining members
                if group_id and remaining:
                    for member in remaining:
                        member_sock = self.clients.get(member)
                        if member_sock:
                            self.send_json(member_sock, {
                                'action': 'disconnect',
                                'message': f'{name} left the chat'
                            })
                
                # Clean up
                del self.clients[name]
                del self.logged_name2sock[name]
                del self.logged_sock2name[sock]
                
                print(f"[SERVER] {name} disconnected")
            
            # Remove socket
            if sock in self.all_sockets:
                self.all_sockets.remove(sock)
            
            sock.close()
            
        except Exception as e:
            print(f"[SERVER] Disconnect error: {e}")
    
    def handle_legacy_command(self, sock, msg):
        """Handle old text-based commands for backward compatibility"""
        try:
            parts = msg.split()
            command = parts[0] if parts else ''
            
            if command == 'connect' and len(parts) >= 2:
                self.handle_connect(sock, {'to': parts[1]})
            elif command == 'who':
                self.handle_who(sock)
            elif command == 'q':
                self.handle_disconnect(sock)
            else:
                # Try to send as message
                self.handle_exchange(sock, {
                    'message': msg,
                    'timestamp': ''
                })
                
        except Exception as e:
            print(f"[SERVER] Legacy command error: {e}")
    
    def send_json(self, sock, data):
        """Helper: Send JSON message to socket"""
        try:
            json_str = json.dumps(data)
            mysend(sock, json_str)
        except Exception as e:
            print(f"[SERVER] Send error: {e}")
    
    def shutdown(self):
        """Shutdown server gracefully"""
        print("[SERVER] Closing all connections...")
        for sock in self.all_sockets:
            try:
                sock.close()
            except:
                pass
        print("[SERVER] Shutdown complete")

if __name__ == '__main__':
    server = Server()
    server.run()