import re
import socket
from dnslib import DNSRecord, QTYPE, RR, A, RCODE

DNS_HOST = "127.0.0.1"
DNS_PORT = 53
FORWARDER = "192.168.1.1"

DOMAIN_MAP = {"ya.ru": "77.88.44.242"}

SINKHOLE_IP = "127.0.0.1"

BLOCKLIST = [
    r"^games\.yandex\.ru$",
    r"^games-sdk\.yandex\.ru$",
    r"^sse\.games\.yandex\.ru$",
    r"^([a-z0-9-]+\.)*games\.s3\.yandex\.net$",
]

BLOCK_PATTERNS = [re.compile(p, re.IGNORECASE) for p in BLOCKLIST]


def is_blocked(qname: str) -> bool:
    qname = qname.rstrip(".")
    return any(p.search(qname) for p in BLOCK_PATTERNS)


def handle_query(data, addr, sock):
    query = DNSRecord.parse(data)
    response = query.reply()

    for question in query.questions:
        qname = str(question.qname)
        qtype = QTYPE[question.qtype]
        print(f"Query for {qname}, Type: {qtype}")

        if is_blocked(qname):
            print(f"  -> BLOCKED, отдаём NXDOMAIN")
            response.header.rcode = RCODE.NXDOMAIN
            sock.sendto(response.pack(), addr)
            return

        if qname.rstrip(".") in DOMAIN_MAP and qtype == "A":
            print(f"  -> MAPPED, отдаём {DOMAIN_MAP[qname.rstrip('.')]}")
            response.add_answer(
                RR(qname, QTYPE.A, ttl=60, rdata=A(DOMAIN_MAP[qname.rstrip(".")]))
            )
            sock.sendto(response.pack(), addr)
            return

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as forward_sock:
            forward_sock.settimeout(3.0)
            forward_sock.sendto(data, (FORWARDER, DNS_PORT))
            try:
                forward_data, _ = forward_sock.recvfrom(512)
            except socket.timeout:
                print(f"  -> TIMEOUT при обращении к {FORWARDER}")
                response.header.rcode = RCODE.SERVFAIL
                sock.sendto(response.pack(), addr)
                return
        sock.sendto(forward_data, addr)
        return


with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.bind((DNS_HOST, DNS_PORT))
    sock.settimeout(1.0)
    print(f"DNS Server started on {DNS_HOST}:{DNS_PORT}")
    try:
        while True:
            try:
                data, addr = sock.recvfrom(512)
            except socket.timeout:
                continue
            handle_query(data, addr, sock)
    except KeyboardInterrupt:
        print("\nОстановка сервера (Ctrl+C)...")