import socket

# ---------------------------------------------------
# NETWORK CONFIGURATION
# ---------------------------------------------------
# Zori's IP Address (The Host)
SERVER_IP = '10.209.64.148' 
SERVER_PORT = 12345

def mysend(s, msg):
    """
    Sends a string message with a 4-byte length header.
    This ensures the other side knows exactly how much to read.
    """
    try:
        msg_bytes = msg.encode('utf-8')
        msg_len = len(msg_bytes)
        # Send length (4 bytes big endian) + message content
        s.sendall(msg_len.to_bytes(4, 'big') + msg_bytes)
    except Exception as e:
        print(f"[!] Send error: {e}")

def myrecv(s):
    """
    Receives a string message handling the 4-byte length header.
    Includes a loop to ensure large messages (like images) are fully received.
    """
    try:
        # 1. Read the first 4 bytes to know how long the message is
        msg_len_bytes = s.recv(4)
        if not msg_len_bytes:
            return None
        
        msg_len = int.from_bytes(msg_len_bytes, 'big')
        
        # 2. Loop until we have read the entire message
        # (This is critical for AI images which create large text strings)
        chunks = []
        bytes_recd = 0
        while bytes_recd < msg_len:
            # Read up to 2048 bytes at a time
            chunk = s.recv(min(msg_len - bytes_recd, 2048))
            if not chunk:
                # Connection broke mid-message
                return None
            chunks.append(chunk)
            bytes_recd += len(chunk)
        
        # Join chunks and decode
        return b''.join(chunks).decode('utf-8')
        
    except Exception as e:
        # print(f"[!] Receive error: {e}") # Uncomment for debugging
        return None