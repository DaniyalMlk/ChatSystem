#!/usr/bin/env python3
"""
Entry point – launches the new client.
"""
import os, sys, argparse
from chat_client_class import Client

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--server", default="127.0.0.1", help="server IP")
    parser.add_argument("-p", "--port", type=int, default=1112, help="server port")
    args = parser.parse_args()

    # pass address via env-vars so no hard-code inside client
    os.environ["CHAT_SERVER_HOST"] = args.server
    os.environ["CHAT_SERVER_PORT"] = str(args.port)

    Client().start()

if __name__ == "__main__":
    main()