import socket
import select
import json
import chat_group as grp
from chat_utils import *

class Server:
    def __init__(self):
        self.new_clients = [] 
        self.logged_name2sock = {} 
        self.logged_sock2name = {} 
        self.all_sockets = []
        self.group = grp.Group()
        
        # Start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        print(f"Server started on port {CHAT_PORT}...")

    def new_client(self, sock):
        print('New client connected...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        try:
            msg = json.loads(myrecv(sock))
            if len(msg) > 0 and msg['action'] == 'login':
                name = msg['name']
                if self.group.is_member(name): # Duplicate Check
                    mysend(sock, json.dumps({"action":"login", "status":"duplicate"}))
                    print(name + ' duplicate login attempt')
                else:
                    self.group.join(name)
                    self.logged_name2sock[name] = sock
                    self.logged_sock2name[sock] = name
                    self.new_clients.remove(sock)
                    mysend(sock, json.dumps({"action":"login", "status":"ok"}))
                    print(name + ' logged in')
        except:
            pass

    def logout(self, sock):
        if sock in self.logged_sock2name:
            name = self.logged_sock2name[sock]
            self.group.leave(name)
            del self.logged_name2sock[name]
            del self.logged_sock2name[sock]
            self.all_sockets.remove(sock)
            sock.close()
            print(name + ' logged out')

    def handle_msg(self, from_sock):
        try:
            msg = myrecv(from_sock)
            if len(msg) > 0:
                msg = json.loads(msg)
                
                # 1. Connect Request
                if msg['action'] == 'connect':
                    to_name = msg['target']
                    from_name = self.logged_sock2name[from_sock]
                    
                    if not self.group.is_member(to_name):
                        mysend(from_sock, json.dumps({"action":"connect", "status":"no-user"}))
                    elif self.group.is_member(to_name):
                        self.group.connect(from_name, to_name)
                        mysend(from_sock, json.dumps({"action":"connect", "status":"success"}))
                        
                        # Notify the other person
                        to_sock = self.logged_name2sock[to_name]
                        mysend(to_sock, json.dumps({"action":"connect", "status":"request", "from":from_name}))

                # 2. Exchange (Chat / Game Moves)
                elif msg['action'] == 'exchange':
                    from_name = self.logged_sock2name[from_sock]
                    # Get everyone in the group (the peer)
                    peers = self.group.list_me(from_name)
                    
                    for peer in peers:
                        if peer != from_name:
                            to_sock = self.logged_name2sock[peer]
                            # Forward the message exactly as is
                            mysend(to_sock, json.dumps({
                                "action":"exchange", 
                                "from": from_name, 
                                "message": msg['message']
                            }))

                # 3. Disconnect
                elif msg['action'] == 'disconnect':
                    from_name = self.logged_sock2name[from_sock]
                    peers = self.group.list_me(from_name)
                    self.group.disconnect(from_name)
                    
                    # Notify others
                    for peer in peers:
                        if peer != from_name:
                            to_sock = self.logged_name2sock[peer]
                            mysend(to_sock, json.dumps({"action":"disconnect"}))

                # 4. List Users (Who)
                elif msg['action'] == 'list':
                    from_name = self.logged_sock2name[from_sock]
                    msg = self.group.list_all(from_name)
                    mysend(from_sock, json.dumps({"action":"list", "results":msg}))

            else:
                self.logout(from_sock)
        except:
            self.logout(from_sock)

    def run(self):
        while True:
            read, _, _ = select.select(self.all_sockets, [], [])
            for sock in read:
                if sock == self.server:
                    newsock, _ = self.server.accept()
                    self.new_client(newsock)
                elif sock in self.new_clients:
                    self.login(sock)
                elif sock in self.logged_sock2name:
                    self.handle_msg(sock)

if __name__ == '__main__':
    server = Server()
    server.run()