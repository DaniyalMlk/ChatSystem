"""
chat_utils.py - Utility functions for chat system
Contains mysend, myrecv, and configuration constants
"""

import json

# Configuration
CLIENT_IP = '127.0.0.1'
SERVER_IP = '127.0.0.1'
SERVER_PORT = 1112  # Match your server's port
CHAT_PORT = 1112

# Server address tuple
SERVER = (SERVER_IP, SERVER_PORT)

# Message length prefix size
SIZE_SPEC = 'I'  # Unsigned int (4 bytes)

def mysend(s, msg):
    """
    Send a message with length prefix
    
    Args:
        s: Socket object
        msg: Message string to send
    """
    import struct
    
    # Encode message to bytes
    msg_bytes = msg.encode('utf-8')
    
    # Create length prefix (4 bytes, unsigned int)
    length = len(msg_bytes)
    length_prefix = struct.pack(SIZE_SPEC, length)
    
    # Send length + message
    s.sendall(length_prefix + msg_bytes)

def myrecv(s):
    """
    Receive a message with length prefix
    
    Args:
        s: Socket object
        
    Returns:
        Decoded message string
    """
    import struct
    
    # First receive the length prefix (4 bytes)
    length_bytes = b''
    while len(length_bytes) < 4:
        chunk = s.recv(4 - len(length_bytes))
        if not chunk:
            return None
        length_bytes += chunk
    
    # Unpack the length
    length = struct.unpack(SIZE_SPEC, length_bytes)[0]
    
    # Now receive the actual message
    msg_bytes = b''
    while len(msg_bytes) < length:
        chunk = s.recv(length - len(msg_bytes))
        if not chunk:
            return None
        msg_bytes += chunk
    
    # Decode and return
    return msg_bytes.decode('utf-8')