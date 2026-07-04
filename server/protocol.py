import json
import struct

HOST = "0.0.0.0"
PORT = 55000


def send_msg(sock, data):
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    sock.sendall(struct.pack(">I", len(payload)) + payload)


def recv_exact(sock, size):
    buf = b""
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def recv_msg(sock):
    header = recv_exact(sock, 4)
    if header is None:
        return None
    (size,) = struct.unpack(">I", header)
    payload = recv_exact(sock, size)
    if payload is None:
        return None
    return json.loads(payload.decode("utf-8"))
