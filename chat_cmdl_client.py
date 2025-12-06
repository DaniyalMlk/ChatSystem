"""
chat_cmdl_client.py - Main Launcher Script
Entry point for the chat client application
"""

import sys
import os
from chat_client_class import ChatClient

def main():
    """Main function to launch the chat client"""
    
    print("=" * 50)
    print("ICS Chat Client")
    print("Distributed Client-Server Chat System")
    print("=" * 50)
    print()
    
    # Check if custom server address is provided
    server_ip = "127.0.0.1"  # Default to localhost
    server_port = 9009  # Default port
    
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            server_port = int(sys.argv[2])
        except ValueError:
            print(f"Invalid port number: {sys.argv[2]}")
            print("Using default port 9009")
    
    print(f"Connecting to server at {server_ip}:{server_port}")
    print()
    
    # Create and start client
    client = ChatClient(server_ip, server_port)
    
    try:
        client.start()
    except KeyboardInterrupt:
        print("\n\nShutting down client...")
        client.stop()
    except Exception as e:
        print(f"\nError: {e}")
        client.stop()
    
    print("Client stopped. Goodbye!")


if __name__ == "__main__":
    main()