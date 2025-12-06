import socket
import json

# Configurations
CHUNK_SIZE = 1024
CHAT_PORT = 1112
SERVER = ("", CHAT_PORT) # Bind to all interfaces

# Message Protocol
# S_OFFLINE   = 0
# S_CONNECTED = 1
# S_LOGGEDIN  = 2
# S_CHATTING  = 3

def mysend(s, msg):
    """Sends a string message with a 5-byte length header."""
    try:
        if isinstance(msg, str):
            msg = msg.encode()
        
        # Prefix with length (5 chars, zero-padded)
        size_header = f"{len(msg):05d}".encode()
        s.sendall(size_header + msg)
    except Exception as e:
        print(f"Send Error: {e}")

def myrecv(s):
    """Receives a message by reading length header first."""
    try:
        # Read 5-byte size header
        size_header = s.recv(5)
        if not size_header or len(size_header) < 5:
            return ""
        
        try:
            msg_len = int(size_header.decode())
        except ValueError:
            return "" # Invalid header
            
        # Read the rest of the message
        data = b""
        while len(data) < msg_len:
            chunk = s.recv(min(msg_len - len(data), CHUNK_SIZE))
            if not chunk: break
            data += chunk
            
        return data.decode()
    except Exception as e:
        print(f"Recv Error: {e}")
        return ""