"""
chat_utils.py - Utility functions for chat system
FIXED VERSION - Correct port configuration
"""
import struct

# Network Configuration - FIXED PORT!
SERVER_IP = '127.0.0.1'  # localhost for local testing
SERVER_PORT = 1112  # FIXED: Was 12345, now 1112
CHAT_PORT = 1112
SERVER = (SERVER_IP, SERVER_PORT)
SIZE_SPEC = 'I'  # unsigned int for message length

def mysend(s, msg):
    """
    Send a message with a 4-byte length header
    
    Args:
        s: socket object
        msg: string or bytes to send
    """
    try:
        # Convert string to bytes if needed
        if isinstance(msg, str):
            msg_bytes = msg.encode('utf-8')
        else:
            msg_bytes = msg
        
        # Get length and create header
        length = len(msg_bytes)
        length_prefix = struct.pack(SIZE_SPEC, length)
        
        # Send length + message
        s.sendall(length_prefix + msg_bytes)
        
    except Exception as e:
        print(f"[ERROR] Send failed: {e}")
        raise

def myrecv(s):
    """
    Receive a message with a 4-byte length header
    
    Args:
        s: socket object
        
    Returns:
        Decoded string message or None if connection closed
    """
    try:
        # Read 4-byte length header
        length_bytes = b''
        while len(length_bytes) < 4:
            chunk = s.recv(4 - len(length_bytes))
            if not chunk:
                return None  # Connection closed
            length_bytes += chunk
        
        # Unpack length
        length = struct.unpack(SIZE_SPEC, length_bytes)[0]
        
        # Read message bytes
        msg_bytes = b''
        while len(msg_bytes) < length:
            chunk = s.recv(min(length - len(msg_bytes), 4096))
            if not chunk:
                return None  # Connection closed
            msg_bytes += chunk
        
        # Decode and return
        return msg_bytes.decode('utf-8')
        
    except Exception as e:
        print(f"[ERROR] Receive failed: {e}")
        return None