import socket
import sys
from chat_utils import *
import client_state_machine as csm
from chat_gui import GUI 

class Client:
    def __init__(self, args):
        self.peer = ''
        self.console_input = []
        self.state = S_OFFLINE
        self.args = args

    def quit(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def init_chat(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
        svr = SERVER if self.args.d == None else (self.args.d, CHAT_PORT)
        self.socket.connect(svr)
        self.sm = csm.ClientSM(self.socket)
        
        # Start the GUI
        # We pass the send/recv functions so the GUI can use the socket safely
        self.gui = GUI(self.send, self.recv, self.sm, self.socket)

    def send(self, msg):
        mysend(self.socket, msg)

    def recv(self):
        return myrecv(self.socket)

    def run_chat(self):
        self.init_chat()
        # This starts the GUI loop. The code waits here until the window closes.
        # Note: We do NOT use the old while loop here anymore.
        print("Starting GUI...")
        self.quit()