import socket
import threading
import json
from chat_utils import *
from client_state_machine import ClientSM
from chat_gui import GUI

class Client:
    def __init__(self, args):
        self.peer = ''
        self.console_input = []
        self.state = S_OFFLINE
        self.system_args = args
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sm = ClientSM()
        
        # Initialize GUI passing self as reference
        self.gui = GUI(args, self)
        
        self.running = True

    def login(self, name):
        # Connect to server
        try:
            self.socket.connect(self.system_args)
            mysend(self.socket, json.dumps({"action": "login", "name": name}))
            response = json.loads(myrecv(self.socket))
            
            if response["status"] == "ok":
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)
                self.sm.socket = self.socket # Give SM access to socket
                
                # Start Receiving Thread
                self.recv_thread = threading.Thread(target=self.recv_loop)
                self.recv_thread.daemon = True
                self.recv_thread.start()
                return True
            else:
                return False
        except Exception as e:
            print(f"Login Error: {e}")
            return False

    def send_to_server(self, msg):
        # Pass user input to State Machine to handle logic/sending
        # We pass an empty string as 'peer_msg' because this is user input
        self.sm.proc(msg, "")

    def recv_loop(self):
        """
        Background thread that listens for socket messages
        and updates the GUI.
        """
        while self.running:
            try:
                msg = myrecv(self.socket)
                if len(msg) > 0:
                    # Pass incoming network msg to State Machine
                    # We pass empty string as 'my_msg'
                    output = self.sm.proc("", msg)
                    
                    # Update GUI
                    if output:
                        self.gui.process_incoming(output)
                else:
                    # Server closed connection
                    break
            except Exception as e:
                print(f"Connection error: {e}")
                break
                
    def quit(self):
        self.running = False
        self.socket.close()

    def start(self):
        self.gui.run()
