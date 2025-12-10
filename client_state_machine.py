"""
client_state_machine.py - COMPLETE VERSION WITH GROUP CHAT SUPPORT
Ready to copy and paste - no manual edits needed!
"""
import json

# States
S_OFFLINE = 0
S_LOGGEDIN = 1
S_CHATTING = 2

class ClientStateMachine:
    def __init__(self, gui=None):
        self.state = S_OFFLINE
        self.gui = gui
        self.peer_name = None
        self.my_name = None
    
    def set_state(self, new_state):
        """Change state"""
        self.state = new_state
    
    def get_state(self):
        """Get current state"""
        return self.state
    
    def process_message(self, msg):
        """
        Process incoming message from server
        Handles both 2-person and group chat messages
        """
        try:
            data = json.loads(msg)
        except (json.JSONDecodeError, ValueError):
            # Legacy text message
            if self.gui:
                self.gui.display_system_message(msg)
            return
        
        action = data.get('action', '')
        
        # Route to appropriate handler based on action
        if action == 'login':
            self.handle_login_response(data)
        
        elif action == 'connect':
            self.handle_connect_response(data)
        
        elif action == 'group_created':  # NEW: Handle group creation
            self.handle_group_created(data)
        
        elif action == 'incoming':
            self.handle_incoming_message(data)
        
        elif action == 'disconnect':
            self.handle_disconnect(data)
        
        elif action == 'who':
            self.handle_who_response(data)
        
        elif action == 'error':
            self.handle_error(data)
        
        else:
            print(f"[CLIENT] Unknown action: {action}")
    
    def handle_login_response(self, data):
        """Handle login response"""
        status = data.get('status')
        message = data.get('message', '')
        
        if self.gui:
            if status == 'success':
                self.gui.display_system_message(message)
                self.state = S_LOGGEDIN
            else:
                self.gui.display_system_message(f"Login failed: {message}")
    
    def handle_connect_response(self, data):
        """Handle connection response (2-person chat)"""
        status = data.get('status')
        message = data.get('message', '')
        
        if self.gui:
            if status == 'success':
                self.gui.handle_system_message(message)
                self.state = S_CHATTING
                
                # Extract peer name from message
                if 'Connected to' in message:
                    peer = message.replace('Connected to', '').strip()
                    self.peer_name = peer
            else:
                self.gui.display_system_message(f"Connection failed: {message}")
    
    def handle_group_created(self, data):
        """
        NEW METHOD: Handle group creation notification
        
        Expected data:
        {
            'action': 'group_created',
            'group_id': 'group_1',
            'members': ['alice', 'bob', 'charlie'],
            'message': 'Group chat created: alice, bob, charlie'
        }
        """
        if not self.gui:
            return
        
        members = data.get('members', [])
        message = data.get('message', 'Group created')
        group_id = data.get('group_id', '')
        
        # Update state to chatting
        self.state = S_CHATTING
        
        # Notify GUI to handle group creation
        self.gui.handle_group_created(data)
        
        print(f"[CLIENT] Joined group {group_id} with {len(members)} members")
    
    def handle_incoming_message(self, data):
        """
        Handle incoming message (works for both 2-person and group chat)
        
        Expected data:
        {
            'action': 'incoming',
            'from': 'alice',  # Sender name
            'message': 'Hello!',
            'timestamp': '08:30 PM'
        }
        """
        if not self.gui:
            return
        
        sender = data.get('from', 'Unknown')
        message = data.get('message', '')
        timestamp = data.get('timestamp', '')
        msg_id = data.get('msg_id')
        
        # Pass to GUI with sender name
        self.gui.handle_incoming_message(
            message,
            sender,  # NEW: Always pass sender name
            timestamp,
            msg_id
        )
        
        # Update state if needed
        if self.state == S_LOGGEDIN:
            self.state = S_CHATTING
    
    def handle_disconnect(self, data):
        """Handle disconnection notification"""
        message = data.get('message', 'Disconnected')
        
        if self.gui:
            self.gui.handle_system_message(message)
        
        # Update state
        self.state = S_LOGGEDIN
        self.peer_name = None
    
    def handle_who_response(self, data):
        """Handle 'who is online' response"""
        users = data.get('users', [])
        
        if self.gui:
            self.gui.handle_user_list(users)
    
    def handle_error(self, data):
        """Handle error message"""
        message = data.get('message', 'An error occurred')
        
        if self.gui:
            self.gui.display_system_message(f"❌ Error: {message}")
    
    def format_login(self, name):
        """Format login message"""
        self.my_name = name
        return json.dumps({
            'action': 'login',
            'name': name
        })
    
    def format_connect(self, peer_name):
        """Format connection request"""
        return json.dumps({
            'action': 'connect',
            'to': peer_name
        })
    
    def format_create_group(self, members):
        """
        NEW METHOD: Format group creation request
        
        Args:
            members: List of usernames ['alice', 'bob', 'charlie']
        """
        return json.dumps({
            'action': 'create_group',
            'members': members
        })
    
    def format_message(self, message, timestamp=''):
        """Format outgoing message"""
        return json.dumps({
            'action': 'exchange',
            'message': message,
            'timestamp': timestamp
        })
    
    def format_disconnect(self):
        """Format disconnect request"""
        return json.dumps({
            'action': 'disconnect'
        })
    
    def format_who(self):
        """Format 'who is online' request"""
        return json.dumps({
            'action': 'who'
        })
    
    def format_quit(self):
        """Format quit request"""
        return json.dumps({
            'action': 'quit'
        })
    
    # ============================================
    # COMPATIBILITY ALIASES
    # ============================================
    
    def format_outgoing_message(self, message, timestamp=''):
        """
        Alias for format_message - for compatibility
        Your client code calls this instead of format_message
        """
        return self.format_message(message, timestamp)
    
    def format_login_message(self, name):
        """Alias for format_login - for compatibility"""
        return self.format_login(name)
    
    def format_connect_message(self, peer_name):
        """Alias for format_connect - for compatibility"""
        return self.format_connect(peer_name)
    
    def format_disconnect_message(self):
        """Alias for format_disconnect - for compatibility"""
        return self.format_disconnect()
    
    def format_who_message(self):
        """Alias for format_who - for compatibility"""
        return self.format_who()
    
    def format_outgoing_message(self, message, timestamp=''):
        """
        Alias for format_message - for compatibility
        Some parts of the client might call this instead
        """
        return self.format_message(message, timestamp)