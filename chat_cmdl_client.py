import socket
import argparse
from chat_utils import *
import client_state_machine as csm
from chat_gui import GUI
from chat_client_class import Client

def main():
    parser = argparse.ArgumentParser(description='chat client argument')
    parser.add_argument('-d', type=str, default=None, help='server IP addr')
    args = parser.parse_args()

    client = Client(args)
    client.run_chat()

if __name__ == "__main__":
    main()