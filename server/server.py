import socket
import threading

import database
from protocol import HOST, PORT, send_msg, recv_msg


def handle_register(data):
    user_id, error = database.register_user(
        data.get("nombre"), data.get("telefono"), data.get("email"),
        data.get("password"), data.get("rol"), data.get("distrito"),
    )
    if error:
        return {"ok": False, "error": error}
    return {"ok": True, "user_id": user_id}


def handle_login(data):
    user = database.login_user(data.get("email"), data.get("password"))
    if not user:
        return {"ok": False, "error": "Credenciales incorrectas"}
    user.pop("password", None)
    user["tiene_mascotas"] = database.count_pets(user["id"]) > 0 if user["rol"] == "dueno" else True
    return {"ok": True, "user": user}


def handle_create_pet(data):
    pet_id = database.create_pet(
        data.get("id_dueno"), data.get("nombre"), data.get("especie"),
        data.get("raza"), data.get("edad"), data.get("cuidados_especiales"),
        data.get("consideraciones"), data.get("foto_b64"), data.get("foto_ext"),
    )
    return {"ok": True, "pet_id": pet_id}


def handle_get_pets(data):
    return {"ok": True, "pets": database.get_pets_by_owner(data.get("id_dueno"))}


def handle_get_caregivers(data):
    caregivers = database.get_caregivers_by_district(data.get("distrito"))
    caregivers = [c for c in caregivers if c["id"] != data.get("exclude_id")]
    for c in caregivers:
        c.pop("password", None)
    return {"ok": True, "caregivers": caregivers}


def handle_get_caregiver_profile(data):
    profile = database.get_caregiver_profile(data.get("id_usuario"))
    if profile:
        profile.pop("password", None)
    return {"ok": True, "profile": profile}


def handle_update_caregiver_profile(data):
    database.update_caregiver_profile(
        data.get("id_usuario"), data.get("descripcion"), data.get("experiencia_texto"),
        data.get("tarifa_hora"), data.get("certificaciones"),
        data.get("disponibilidad"), data.get("zona_trabajo"),
    )
    return {"ok": True}


def handle_create_contract(data):
    contract_id = database.create_contract(
        data.get("id_dueno"), data.get("id_cuidador"), data.get("id_mascota"),
        data.get("fecha_inicio"), data.get("duracion"),
        data.get("horario"), data.get("ubicacion_servicio"), data.get("presupuesto"),
    )
    return {"ok": True, "contract_id": contract_id}


def handle_update_contract_status(data):
    database.update_contract_status(data.get("id_contrato"), data.get("estado"))
    return {"ok": True}


def handle_rate_contract(data):
    database.rate_contract(data.get("id_contrato"), data.get("estrellas"), data.get("comentario"))
    return {"ok": True}


def handle_get_contracts_owner(data):
    return {"ok": True, "contracts": database.get_contracts_for_owner(data.get("id_dueno"))}


def handle_get_contracts_caregiver(data):
    return {"ok": True, "contracts": database.get_contracts_for_caregiver(data.get("id_cuidador"))}


def handle_get_caregiver_reviews(data):
    return {"ok": True, "reviews": database.get_reviews_for_caregiver(data.get("id_cuidador"))}


def handle_report_incident(data):
    incident_id = database.report_incident(
        data.get("id_contrato"), data.get("id_reportante"),
        data.get("descripcion"), data.get("gravedad", "baja"),
    )
    return {"ok": True, "incident_id": incident_id}


def handle_register_payment(data):
    payment_id = database.register_payment(
        data.get("id_contrato"), data.get("monto"), data.get("metodo"),
        data.get("estado_pago", "pagado"),
    )
    return {"ok": True, "payment_id": payment_id}


def handle_get_payments(data):
    return {"ok": True, "payments": database.get_payments_for_contract(data.get("id_contrato"))}


ACTIONS = {
    "register": handle_register,
    "login": handle_login,
    "create_pet": handle_create_pet,
    "get_pets": handle_get_pets,
    "get_caregivers": handle_get_caregivers,
    "get_caregiver_profile": handle_get_caregiver_profile,
    "update_caregiver_profile": handle_update_caregiver_profile,
    "create_contract": handle_create_contract,
    "update_contract_status": handle_update_contract_status,
    "rate_contract": handle_rate_contract,
    "get_contracts_owner": handle_get_contracts_owner,
    "get_contracts_caregiver": handle_get_contracts_caregiver,
    "get_caregiver_reviews": handle_get_caregiver_reviews,
    "report_incident": handle_report_incident,
    "register_payment": handle_register_payment,
    "get_payments": handle_get_payments,
}


def client_thread(conn, addr):
    print(f"Conexión desde {addr}")
    try:
        while True:
            request = recv_msg(conn)
            if request is None:
                break
            action = request.get("action")
            handler = ACTIONS.get(action)
            if handler:
                try:
                    response = handler(request.get("data", {}))
                except Exception as e:
                    response = {"ok": False, "error": str(e)}
            else:
                response = {"ok": False, "error": f"Acción desconocida: {action}"}
            send_msg(conn, response)
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        conn.close()
        print(f"Desconexión de {addr}")


def main():
    database.init_db()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print(f"Servidor escuchando en {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=client_thread, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Servidor detenido")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()