import json
from chat_utils import *

class ClientSM:
    def __init__(self):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.pnum = 0

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action": "connect", "target": peer})
        mysend(self.socket, msg)
        response = json.loads(myrecv(self.socket))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += f"Connected to {peer}\n"
            return True
        else:
            self.out_msg += "Connection failed\n"
            return False

    def disconnect(self):
        msg = json.dumps({"action": "disconnect"})
        mysend(self.socket, msg)
        self.out_msg += "Disconnected from " + self.peer + "\n"
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        """
        Core Logic Processor.
        my_msg: Input from the GUI (what I typed).
        peer_msg: Input from the Socket (what came from server).
        """
        self.out_msg = ''
        
        # ---------------------------------------------------------
        # STATE: CHATTING
        # ---------------------------------------------------------
        if self.state == S_CHATTING:
            # 1. Handle Incoming Messages (peer_msg)
            if len(peer_msg) > 0:
                try:
                    peer_msg = json.loads(peer_msg)
                except:
                    # If it's not JSON, it might be raw text or server error
                    pass
                
                if isinstance(peer_msg, dict) and "action" in peer_msg:
                    # Protocol handling (exchange, disconnect, etc)
                    if peer_msg["action"] == "disconnect":
                        self.state = S_LOGGEDIN
                        self.peer = ''
                        self.out_msg += "Peer disconnected.\n"
                    elif peer_msg["action"] == "exchange":
                        # This is a standard chat message
                        from_user = peer_msg["from"]
                        text = peer_msg["message"]
                        
                        # --- GAME LOGIC INTERCEPTION ---
                        if text.startswith("GAME_MOVE:"):
                            # Do NOT add to out_msg. The GUI class will 
                            # read a special flag or we handle it here.
                            # We will return a special tuple to the GUI
                            return ("GAME", text) 
                        # -------------------------------
                        
                        self.out_msg += f"[{from_user}] {text}\n"
                
            # 2. Handle Outgoing Messages (my_msg)
            if len(my_msg) > 0:
                # --- GAME LOGIC OUTGOING ---
                if my_msg.startswith("GAME_MOVE:"):
                    mysend(self.socket, json.dumps({"action": "exchange", "from": self.me, "message": my_msg}))
                    return ("GAME", "SENT") # Don't print move to chat
                # ---------------------------

                if my_msg == 'disconnect':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                else:
                    mysend(self.socket, json.dumps({"action": "exchange", "from": self.me, "message": my_msg}))
                    # Usually we don't print our own msg here, the GUI adds it directly
            
            return self.out_msg

        # ---------------------------------------------------------
        # STATE: LOGGED IN (Waiting to connect)
        # ---------------------------------------------------------
        elif self.state == S_LOGGEDIN:
            if len(my_msg) > 0:
                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE
                elif my_msg == 'time':
                    mysend(self.socket, json.dumps({"action": "time"}))
                    svr_msg = json.loads(myrecv(self.socket))
                    self.out_msg += "Time is: " + svr_msg["results"]
                elif my_msg == 'who':
                    mysend(self.socket, json.dumps({"action": "list"}))
                    svr_msg = json.loads(myrecv(self.socket))
                    self.out_msg += "Listing all: " + svr_msg["results"]
                elif my_msg.startswith('c '):
                    peer = my_msg[2:]
                    peer = peer.strip()
                    if self.connect_to(peer):
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection failed\n'
                elif my_msg.startswith('?'):
                    term = my_msg[1:].strip()
                    mysend(self.socket, json.dumps({"action":"search", "target":term}))
                    svr_msg = json.loads(myrecv(self.socket))
                    self.out_msg += "Search result:\n" + svr_msg["results"] + "\n"

            if len(peer_msg) > 0:
                try:
                    peer_msg = json.loads(peer_msg)
                except: pass
                
                if isinstance(peer_msg, dict) and peer_msg["action"] == "connect":
                     self.peer = peer_msg["from"]
                     self.out_msg += "Request from " + self.peer + "\n"
                     self.out_msg += "You are connected with " + self.peer + ". Chat away!\n"
                     self.out_msg += "-----------------------------------\n"
                     self.state = S_CHATTING

            return self.out_msg

        return self.out_msg