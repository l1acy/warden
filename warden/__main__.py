import os
import socket
import threading
import argparse

from warden.fun.handle_request import handle_request


def start_server(host, port, blocked_file):
    print('Try to read', blocked_file)
    with open(os.path.expanduser(blocked_file), mode='a+') as file:
        blocked_sites_raw = file.read()
    print('File read')
    
    server_address = (host, port)
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(server_address)
    server_socket.listen(50)
    print(f"Server listening on http://{server_address[0]}:{server_address[1]}")

    server_socket.settimeout(1)

    try:
        print("Waiting for a connection...")
        while True:
            try:
                conn, addr = server_socket.accept()
                print(f"Connection from {addr}")

                client_thread = threading.Thread(
                    target=handle_request, args=(conn, addr, blocked_sites_raw), name=f"{addr[1]}"
                )
                client_thread.start()
            except socket.timeout:
                pass
            except KeyboardInterrupt:
                try:
                    if conn:
                        conn.close()
                except:
                    pass
                break
    except KeyboardInterrupt:
        print("Server stopped")
        server_socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Warden',
        description='HTTP proxy for website filtering'
    )
    parser.add_argument('--host', default='127.0.0.1', type=str)
    parser.add_argument('--port', default=5678, type=int)
    parser.add_argument('--blocked-file', default='~/.config/warden/blocked.txt', type=str)
    
    args = parser.parse_args()
    
    start_server(args.host, args.port, args.blocked_file)