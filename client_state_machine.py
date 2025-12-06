"""
client_state_machine.py - Client State Machine
Handles client states and message processing
"""

import json

# State constants
S_OFFLINE = 0
S_LOGGEDIN = 1
S_CHATTING = 2

class ClientStateMachine:
    """Manages client state and processes incoming messages"""
    
    def __init__(self, client_name):
        """
        Initialize state machine
        
        Args:
            client_name: The client's nickname
        """
        self.state = S_OFFLINE
        self.client_name = client_name
        self.peer_name = None
        self.gui = None  # Will be set by client class
    
    def set_state(self, new_state):
        """Change the client state"""
        old_state = self.state
        self.state = new_state
        print(f"State changed: {self._state_name(old_state)} -> {self._state_name(new_state)}")
    
    def _state_name(self, state):
        """Get human-readable state name"""
        if state == S_OFFLINE:
            return "OFFLINE"
        elif state == S_LOGGEDIN:
            return "LOGGED IN"
        elif state == S_CHATTING:
            return "CHATTING"
        return "UNKNOWN"
    
    def process_message(self, msg):
        """
        Process incoming message from server
        
        Args:
            msg: JSON message from server
        """
        try:
            if not msg:
                return
            
            # Parse JSON
            data = json.loads(msg)
            
            # Extract message action (server uses 'action' not 'type')
            action = data.get('action', '')
            
            if action == 'login':
                status = data.get('status', '')
                if status == 'ok':
                    self._handle_login_success()
                elif status == 'duplicate':
                    self._handle_error({'message': 'Nickname already in use'})
            
            elif action == 'connect':
                status = data.get('status', '')
                if status == 'success':
                    # We initiated connection
                    self._handle_connect_success(data)
                elif status == 'request':
                    # Someone is connecting to us
                    from_user = data.get('from', 'Unknown')
                    self.peer_name = from_user
                    self.set_state(S_CHATTING)
                    if self.gui:
                        self.gui.peer_name = from_user
                        self.gui.handle_system_message(f"{from_user} connected to you")
                        self.gui.update_status(f"Chatting with {from_user}")
                elif status == 'no-user':
                    self._handle_error({'message': 'User not found'})
            
            elif action == 'exchange':
                self._handle_incoming_message(data)
            
            elif action == 'list':
                self._handle_user_list(data)
            
            elif action == 'disconnect':
                self._handle_disconnect(data)
            
            else:
                print(f"Unknown message action: {action}")
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw message: {msg}")
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def _handle_login_success(self):
        """Handle successful login"""
        self.set_state(S_LOGGEDIN)
        if self.gui:
            self.gui.display_system_message("Successfully logged in!")
            self.gui.update_status("Logged In")
    
    def _handle_error(self, data):
        """Handle error message"""
        error_msg = data.get('message', 'Unknown error')
        print(f"Error from server: {error_msg}")
        
        if self.gui:
            self.gui.display_system_message(f"Error: {error_msg}")
    
    def _handle_incoming_message(self, data):
        """Handle incoming chat message"""
        sender = data.get('from', 'Unknown')
        message = data.get('message', '')
        
        # Filter out game messages from chat display
        if message.startswith("GAME_"):
            # Route to game window
            if self.gui and self.gui.game_window:
                self.gui.game_window.receive_move(message)
            return
        
        # Display regular message
        if self.gui:
            self.gui.handle_incoming_message(message, sender)
    
    def _handle_user_list(self, data):
        """Handle online user list"""
        results = data.get('results', '')
        
        # Parse the results string to extract usernames
        users = []
        if isinstance(results, str):
            # Server returns format: "Users: ----\n{'name1': 0, 'name2': 0}\n..."
            # Extract the dictionary part
            import re
            match = re.search(r'\{([^}]+)\}', results)
            if match:
                # Extract usernames from the dictionary
                user_dict_str = '{' + match.group(1) + '}'
                try:
                    # Parse it properly
                    for line in results.split('\n'):
                        if ':' in line and "'" in line:
                            # Extract username between quotes
                            parts = line.split("'")
                            for i in range(1, len(parts), 2):
                                if parts[i] and parts[i] != 'Users' and parts[i] != 'Groups':
                                    users.append(parts[i])
                except:
                    pass
        
        if self.gui:
            self.gui.handle_user_list(users)
    
    def _handle_connect_success(self, data):
        """Handle successful connection to peer"""
        # When we initiate connection, server sends back success
        # The actual peer connection happens when both sides are ready
        self.set_state(S_CHATTING)
        
        if self.gui:
            # Use the peer_name we stored when sending connect
            if self.peer_name:
                self.gui.handle_system_message(f"Connected to {self.peer_name}")
                self.gui.update_status(f"Chatting with {self.peer_name}")
            else:
                self.gui.handle_system_message(f"Connection established")
                self.gui.update_status(f"Chatting")
    
    def _handle_disconnect(self, data):
        """Handle disconnection from peer"""
        peer = data.get('peer', self.peer_name)
        reason = data.get('reason', 'Disconnected')
        
        self.peer_name = None
        self.set_state(S_LOGGEDIN)
        
        if self.gui:
            self.gui.peer_name = None
            self.gui.handle_system_message(f"{peer} {reason}")
            self.gui.update_status("Logged In")
    
    def _handle_system_message(self, data):
        """Handle system message"""
        message = data.get('message', '')
        
        if self.gui:
            self.gui.handle_system_message(message)
    
    def format_outgoing_message(self, message):
        """
        Format outgoing message as JSON
        
        Args:
            message: Message text
            
        Returns:
            JSON string
        """
        # Handle special commands
        if message.startswith('connect '):
            peer = message.split(' ', 1)[1].strip()
            self.peer_name = peer  # Store the peer we're connecting to
            return json.dumps({
                'action': 'connect',
                'target': peer
            })
        
        elif message == 'who':
            return json.dumps({
                'action': 'list'
            })
        
        elif message == 'q':
            return json.dumps({
                'action': 'disconnect'
            })
        
        elif message.startswith('disconnect'):
            return json.dumps({
                'action': 'disconnect'
            })
        
        # Game messages and regular chat messages
        else:
            return json.dumps({
                'action': 'exchange',
                'message': message
            })


class SimpleClientSM:
    """
    Simplified state machine for backward compatibility
    Delegates to ClientStateMachine
    """
    
    def __init__(self, s):
        """
        Initialize with socket
        
        Args:
            s: Socket object
        """
        self.s = s
        self.state = S_OFFLINE
        self.peer = None
        self.me = None
        self.out_msg = ''
        self.state_machine = None  # Will be set by client
    
    def set_state(self, state):
        """Set the current state"""
        self.state = state
        if self.state_machine:
            self.state_machine.set_state(state)
    
    def get_state(self):
        """Get the current state"""
        return self.state
    
    def set_myname(self, name):
        """Set client name"""
        self.me = name
    
    def get_myname(self):
        """Get client name"""
        return self.me
    
    def connect_to(self, peer_name):
        """Connect to a peer"""
        self.peer = peer_name
        msg = json.dumps({'type': 'connect', 'peer': peer_name})
        return msg
    
    def proc(self, msg):
        """Process incoming message"""
        if self.state_machine:
            self.state_machine.process_message(msg)
        return self.out_msg