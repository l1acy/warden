"""Thanks github.com/dynstat/simplest-http-server-Py/tree/main for code"""

import socket
from socket import socket as Socket, _RetAddress
import threading

# Define the server address and port
SERVER_ADDRESS = ("localhost", 8000)

ALLOWED_ORIGINS = [
    "*",
    "http://localhost:8000",
    "null",
]  # Allow requests from file:// URLs and the same origin

def handle_request(conn: Socket, addr: _RetAddress):
    try:
        # Receive the HTTP request
        request_data = conn.recv(1024).decode()
        if not request_data:
            conn.close()
            return
        
        print("Received request:", request_data[0:14], '  ....')
        
        request_line = request_data.splitlines()[0]
        method, path, http_version = request_line.split()
        
        print(f'[{method}] {path} (v{http_version})')
        
        response_body = b'<h1>Hello, world!</h1>'
        content_length = len(response_body)
        
        response_headers = [
            f"{http_version} 200",
            f"Content-Type: text/plain",
            f"Content-Length: {content_length}",
            "Connection: close",
            "Access-Control-Allow-Origin: *",  # Allow all origins for simplicity
            "Access-Control-Allow-Methods: GET, POST, OPTIONS",
            "Access-Control-Allow-Headers: Content-Type",
        ]
        
        response_header_str = "\r\n".join(response_headers) + "\r\n\r\n"
        
        conn.sendall(response_header_str.encode() + response_body)
        conn.close()
    except Exception as e:
        print(f"\n************ EXCEPTION : {e} ***********\n")
        response_body = b"<h1>500 Internal Server Error</h1>"
        content_length = len(response_body)
        content_type = "text/html"
        # Use HTTP/1.1 as a fallback if an exception occurs before HTTP version is determined
        response_headers = [
            "HTTP/1.1 500 Internal Server Error",
            f"Content-Type: {content_type}",
            f"Content-Length: {content_length}",
            "Connection: close",
            f"Access-Control-Allow-Origin: {ALLOWED_ORIGINS[0]}",
            "Access-Control-Allow-Methods: GET, POST, OPTIONS",
            "Access-Control-Allow-Headers: Content-Type",
        ]
        response_header_str = "\r\n".join(response_headers) + "\r\n\r\n"
        conn.sendall(response_header_str.encode() + response_body)
        conn.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(5)
    print(f"Server listening on http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}")

    # Setting a timeout of 1 second on blocking socket operations (accept() call) to allow for keyboard interrupt (CTRL + c) recognition in the terminal.
    server_socket.settimeout(1)

    try:
        print("Waiting for a connection...")
        while True:
            try:
                # no more a infinitely blocking call, because of server_socket.settimeout(1)
                conn, addr = server_socket.accept()
                print(f"Connection from {addr}")

                # Handle the client request in a new thread
                client_thread = threading.Thread(
                    target=handle_request, args=(conn, addr), name=f"{addr[1]}"
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
    start_server()