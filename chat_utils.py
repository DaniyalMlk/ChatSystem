import socket

# ---------------------------------------------------
# NETWORK CONFIGURATION
# ---------------------------------------------------
# Zori's IP Address
SERVER_IP = '10.209.64.148' 

# The code uses both names, so we define both to be safe:
SERVER_PORT = 12345
CHAT_PORT = 12345 

def mysend(s, msg):
    """
    Sends a string message with a 4-byte length header.
    """
    try:
        if isinstance(msg, str):
            msg_bytes = msg.encode('utf-8')
        else:
            msg_bytes = msg
            
        msg_len = len(msg_bytes)
        s.sendall(msg_len.to_bytes(4, 'big') + msg_bytes)
    except Exception as e:
        print(f"[!] Send error: {e}")

def myrecv(s):
    """
    Receives a string message handling the 4-byte length header.
    """
    try:
        msg_len_bytes = s.recv(4)
        if not msg_len_bytes:
            return None
        
        msg_len = int.from_bytes(msg_len_bytes, 'big')
        
        chunks = []
        bytes_recd = 0
        while bytes_recd < msg_len:
            chunk = s.recv(min(msg_len - bytes_recd, 4096))
            if not chunk:
                return None
            chunks.append(chunk)
            bytes_recd += len(chunk)
        
        return b''.join(chunks).decode('utf-8')
        
    except Exception as e:
        return None