from chat_utils import *
import json

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        # Sends a connection request to the server
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        return True

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def chat(self, msg):
        """
        Called by the GUI to send a message or command.
        """
        # Allow commands (time, who, connect) even if just logged in
        if self.state == S_LOGGEDIN or self.state == S_CHATTING:
            if msg == 'time':
                mysend(self.s, json.dumps({"action":"time"}))
                return True
            elif msg == 'who':
                mysend(self.s, json.dumps({"action":"list"}))
                return True
            elif msg.startswith('c '):
                peer = msg[2:].strip()
                self.connect_to(peer)
                return True
            elif msg.startswith('p '):
                try:
                    target = msg[2:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target": target}))
                except: pass
                return True
            elif msg.startswith('? '):
                term = msg[2:].strip()
                mysend(self.s, json.dumps({"action":"search", "target": term}))
                return True

        # Send normal chat message only if chatting
        if self.state == S_CHATTING:
            if msg == 'bye':
                self.disconnect()
                self.state = S_LOGGEDIN
                self.peer = ''
            else:
                json_msg = json.dumps({
                    "action": "exchange",
                    "from": "[" + self.me + "]",
                    "message": msg
                })
                mysend(self.s, json_msg)
            return True
        
        return False

    def proc(self, my_msg, peer_msg):
        """
        Processes incoming messages from the server.
        """
        self.out_msg = ''
        
        if len(peer_msg) > 0:
            try:
                pm = json.loads(peer_msg)
                
                # 1. Connection updates
                if pm["action"] == "connect":
                    if "status" in pm:
                        if pm["status"] == "success":
                            self.state = S_CHATTING
                            self.out_msg += f"Connected to {self.peer}. Chat away!\n"
                        elif pm["status"] == "request":
                            self.peer = pm["from"]
                            self.out_msg += f"Request from {self.peer}\n"
                            self.out_msg += f"You are connected with {self.peer}. Chat away!\n"
                            self.state = S_CHATTING
                        else:
                            self.out_msg += f"Connection failed: {pm['status']}\n"
                            self.peer = ''
                
                # 2. Chat Exchange
                elif pm["action"] == "exchange":
                    self.out_msg += f"{pm['from']}: {pm['message']}"
                
                # 3. Disconnect
                elif pm["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                    self.out_msg += "Peer disconnected. You are alone.\n"
                    self.peer = ''
                
                # 4. System/Command Results
                elif "results" in pm:
                    self.out_msg += str(pm["results"])
                    
                # 5. Generic Messages
                elif "message" in pm and pm["action"] not in ["exchange", "connect"]:
                     self.out_msg += str(pm["message"])
                     
            except Exception as e:
                pass

        return self.out_msg