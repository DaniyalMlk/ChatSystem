"""
chat_cmdl_client.py - Main Launcher Script
Entry point for the chat client application - Works with any server
"""

import sys
import os

def main():
    """Main function to launch the chat client"""
    
    print("=" * 50)
    print("ICS Chat Client")
    print("Distributed Client-Server Chat System")
    print("=" * 50)
    print()
    
    # Check if custom server address is provided
    server_ip = "127.0.0.1"  # Default to localhost
    server_port = 1112  # Default port
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            print("Usage:")
            print("  python3 chat_cmdl_client.py                    # Connect to localhost:1112")
            print("  python3 chat_cmdl_client.py <server_ip>        # Connect to server_ip:1112")
            print("  python3 chat_cmdl_client.py <server_ip> <port> # Connect to server_ip:port")
            print()
            print("Examples:")
            print("  python3 chat_cmdl_client.py                    # Local server")
            print("  python3 chat_cmdl_client.py 192.168.1.100      # LAN server")
            print("  python3 chat_cmdl_client.py 203.0.113.1 1112   # Internet server")
            return
        
        server_ip = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            server_port = int(sys.argv[2])
        except ValueError:
            print(f"✗ Invalid port number: {sys.argv[2]}")
            print("✓ Using default port 1112")
    
    print(f"Server: {server_ip}:{server_port}")
    print()
    
    # Import client (do this after argument parsing to show help faster)
    try:
        from chat_client_class import ChatClient
    except ImportError as e:
        print("✗ Error: Cannot import required modules")
        print(f"  Details: {e}")
        print()
        print("Make sure these files exist in the same directory:")
        print("  - chat_client_class.py")
        print("  - chat_gui.py")
        print("  - client_state_machine.py")
        print("  - game_client.py")
        print("  - feature_utils.py")
        print("  - chat_utils.py")
        return
    
    # Create and start client
    client = ChatClient(server_ip, server_port)
    
    try:
        print("Starting client...")
        client.start()
    except KeyboardInterrupt:
        print("\n\n✗ Shutting down client...")
        client.stop()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is the server running?")
        print("  2. Is the server IP correct?")
        print("  3. Is the port correct?")
        print("  4. Check firewall settings")
        print("  5. Try: python3 chat_cmdl_client.py 127.0.0.1 1112")
        client.stop()
    
    print("\nClient stopped. Goodbye!")


if __name__ == "__main__":
    main()