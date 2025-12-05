import socket
import threading

# Connection Data
HOST = '0.0.0.0'  # Listens to all incoming connections
PORT = 12345

# Lists to keep track of connected users
clients = []
nicknames = []

def broadcast(message, _sender_client=None):
    """
    Sends a message to all clients.
    If _sender_client is provided, we can choose NOT to send it back to the sender
    (so they don't see their own message twice), or send it to everyone.
    For this simple version, we send to everyone except the sender.
    """
    for client in clients:
        if client != _sender_client:
            try:
                client.send(message)
            except:
                # If link is broken, remove client
                client.close()
                if client in clients:
                    clients.remove(client)

def handle_client(client):
    """Handles the connection for a single client."""
    while True:
        try:
            # Receive message from client
            message = client.recv(1024)
            # Broadcast it to everyone else
            broadcast(message, _sender_client=client)
        except:
            # Clean up if they disconnect
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                print(f"{nickname} disconnected.")
                broadcast(f"{nickname} left the chat!".encode('utf-8'))
                nicknames.remove(nickname)
                break

def receive():
    """Main loop to accept new connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server is listening on port {PORT}...")

    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        # Request Nickname
        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        
        nicknames.append(nickname)
        clients.append(client)

        print(f"Nickname is {nickname}")
        
        # Announce arrival
        broadcast(f"{nickname} joined the chat!".encode('utf-8'))
        client.send('Connected to server!'.encode('utf-8'))

        # Start handling thread
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

if __name__ == "__main__":
    receive()