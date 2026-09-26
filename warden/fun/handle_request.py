import re
import socket
import select
from typing import Set
from urllib.parse import urlsplit

HOP_BY_HOP = {
    "proxy-connection",
    "proxy-authorization",
    "connection",
    "keep-alive",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def read_headers(conn):
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = conn.recv(4096)
        if not chunk:
            return None
        buf += chunk
    header_part, _, rest = buf.partition(b"\r\n\r\n")
    return header_part, rest


def parse_headers(header_bytes):
    lines = header_bytes.split(b"\r\n")
    request_line = lines[0].decode("latin-1")
    headers = []
    for line in lines[1:]:
        if b":" in line:
            k, v = line.split(b":", 1)
            headers.append((k.decode("latin-1").strip(), v.decode("latin-1").strip()))
    return request_line, headers


def read_body(conn, headers, initial_body):
    length = 0
    for k, v in headers:
        if k.lower() == "content-length":
            try:
                length = int(v)
            except ValueError:
                length = 0
            break
    body = initial_body
    while len(body) < length:
        chunk = conn.recv(4096)
        if not chunk:
            break
        body += chunk
    return body


def pipe(a, b):
    try:
        while True:
            r, _, _ = select.select([a, b], [], [], 1)
            if not r:
                continue
            for s in r:
                data = s.recv(4096)
                if not data:
                    return
                other = b if s is a else a
                other.sendall(data)
    finally:
        try:
            a.close()
        except OSError:
            pass
        try:
            b.close()
        except OSError:
            pass

def parse_blocked_sites(blocked_sites_raw: str):
    patterns = []
    for line in blocked_sites_raw.splitlines():
        line = line.strip().lower()
        if not line or line.startswith("#"):
            continue
        patterns.append(re.compile(line))
    return patterns

def is_blocked(host, patterns):
    host = host.lower()
    return any(p.search(host) for p in patterns)

def handle_request(conn, addr, blocked_sites_raw: str):
    blocked_sites = parse_blocked_sites(blocked_sites_raw)
    
    try:
        result = read_headers(conn)
        if result is None:
            conn.close()
            return
        header_bytes, initial_body = result
        request_line, headers = parse_headers(header_bytes)

        print("Received request:", request_line)

        try:
            method, target, http_version = request_line.split()

            host = ""
            if method.upper() == "CONNECT":
                host = target.split(":")[0]
            else:
                host = urlsplit(target).hostname or ""

            if is_blocked(host, blocked_sites):
                body = b"<h1>Access denied</h1>"
                headers = (
                    f"{http_version} 403 Forbidden\r\n"
                    f"Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    f"Connection: close\r\n"
                    f"\r\n"
                )
                conn.sendall(headers.encode() + body)
                conn.close()
                return

            print(f'[{method}] {target} (v{http_version})')
        except ValueError:
            conn.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            conn.close()
            return

        print(f'[{method}] {target} (v{http_version})')

        if method.upper() == "CONNECT":
            if ":" in target:
                host, port_str = target.rsplit(":", 1)
                try:
                    port = int(port_str)
                except ValueError:
                    port = 443
            else:
                host, port = target, 443

            try:
                remote = socket.create_connection((host, port), timeout=10)
            except OSError as e:
                print(f"CONNECT failed: {e}")
                try:
                    conn.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                except OSError:
                    pass
                conn.close()
                return

            conn.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            if initial_body:
                remote.sendall(initial_body)
            pipe(conn, remote)
            return

        parts = urlsplit(target)
        if not parts.scheme or not parts.hostname:
            conn.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            conn.close()
            return

        host = parts.hostname
        port = parts.port or (443 if parts.scheme == "https" else 80)

        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query

        new_headers = []
        for k, v in headers:
            if k.lower() in HOP_BY_HOP:
                continue
            new_headers.append(f"{k}: {v}")
        new_headers.append("Connection: close")

        body = read_body(conn, headers, initial_body)

        out = f"{method} {path} {http_version}".encode("latin-1") + b"\r\n"
        out += b"\r\n".join(h.encode("latin-1") for h in new_headers)
        out += b"\r\n\r\n"
        out += body

        try:
            remote = socket.create_connection((host, port), timeout=10)
        except OSError as e:
            print(f"Connect failed: {e}")
            try:
                conn.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except OSError:
                pass
            conn.close()
            return

        remote.sendall(out)

        while True:
            data = remote.recv(4096)
            if not data:
                break
            conn.sendall(data)

        remote.close()
        conn.close()

    except Exception as e:
        print(f"\n************ EXCEPTION : {e} ***********\n")
        try:
            conn.sendall(b"HTTP/1.1 500 Internal Server Error\r\nConnection: close\r\n\r\n")
        except OSError:
            pass
        conn.close()