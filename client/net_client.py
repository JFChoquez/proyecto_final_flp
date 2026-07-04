import socket

from protocol import HOST, PORT, send_msg, recv_msg


def request(action, data=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect((HOST, PORT))
            send_msg(sock, {"action": action, "data": data or {}})
            response = recv_msg(sock)
            if response is None:
                return {"ok": False, "error": "Sin respuesta del servidor"}
            return response
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return {"ok": False, "error": f"No se pudo conectar al servidor: {e}"}