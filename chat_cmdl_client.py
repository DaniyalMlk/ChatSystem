from chat_client_class import Client
import argparse

def main():
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('host', type=str, help='Server IP', default='localhost', nargs='?')
    parser.add_argument('port', type=int, help='Server Port', default=8888, nargs='?')
    args = parser.parse_args()

    client = Client((args.host, args.port))
    client.start()

if __name__ == "__main__":
    main()