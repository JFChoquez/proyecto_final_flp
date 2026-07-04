import sqlite3
import threading
import os
import base64
import uuid
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "cuidadores.db")
STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage", "mascotas")

_lock = threading.Lock()
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row


def _add_column_if_missing(cur, table, column, coltype):
    """Agrega una columna nueva a una tabla ya existente sin romper bases de datos viejas."""
    cur.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cur.fetchall()}
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def init_db():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    with _lock:
        cur = _conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            distrito TEXT NOT NULL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Cuidadores_Perfiles (
            id_usuario INTEGER PRIMARY KEY,
            descripcion TEXT,
            experiencia_texto TEXT,
            tarifa_hora REAL,
            certificaciones TEXT,
            disponibilidad TEXT,
            zona_trabajo TEXT,
            FOREIGN KEY (id_usuario) REFERENCES Usuarios(id)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Mascotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_dueno INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            especie TEXT NOT NULL,
            raza TEXT,
            edad INTEGER,
            cuidados_especiales TEXT,
            consideraciones TEXT,
            foto_path TEXT,
            FOREIGN KEY (id_dueno) REFERENCES Usuarios(id)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Contratos_Servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_dueno INTEGER NOT NULL,
            id_cuidador INTEGER NOT NULL,
            id_mascota INTEGER,
            fecha_inicio TEXT,
            duracion_horas_dias TEXT,
            horario TEXT,
            ubicacion_servicio TEXT,
            presupuesto REAL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            calificacion_estrellas INTEGER,
            comentario TEXT,
            fecha_calificacion TEXT,
            FOREIGN KEY (id_dueno) REFERENCES Usuarios(id),
            FOREIGN KEY (id_cuidador) REFERENCES Usuarios(id),
            FOREIGN KEY (id_mascota) REFERENCES Mascotas(id)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Incidentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_contrato INTEGER NOT NULL,
            id_reportante INTEGER NOT NULL,
            descripcion TEXT NOT NULL,
            gravedad TEXT NOT NULL DEFAULT 'baja',
            fecha TEXT,
            FOREIGN KEY (id_contrato) REFERENCES Contratos_Servicios(id),
            FOREIGN KEY (id_reportante) REFERENCES Usuarios(id)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_contrato INTEGER NOT NULL,
            monto REAL,
            metodo TEXT,
            estado_pago TEXT NOT NULL DEFAULT 'pendiente',
            fecha TEXT,
            FOREIGN KEY (id_contrato) REFERENCES Contratos_Servicios(id)
        )""")

        # Compatibilidad con bases de datos creadas antes de estos campos.
        _add_column_if_missing(cur, "Cuidadores_Perfiles", "tarifa_hora", "REAL")
        _add_column_if_missing(cur, "Cuidadores_Perfiles", "certificaciones", "TEXT")
        _add_column_if_missing(cur, "Cuidadores_Perfiles", "disponibilidad", "TEXT")
        _add_column_if_missing(cur, "Cuidadores_Perfiles", "zona_trabajo", "TEXT")
        _add_column_if_missing(cur, "Contratos_Servicios", "horario", "TEXT")
        _add_column_if_missing(cur, "Contratos_Servicios", "ubicacion_servicio", "TEXT")
        _add_column_if_missing(cur, "Contratos_Servicios", "presupuesto", "REAL")
        _add_column_if_missing(cur, "Contratos_Servicios", "comentario", "TEXT")
        _add_column_if_missing(cur, "Contratos_Servicios", "fecha_calificacion", "TEXT")

        _conn.commit()


def register_user(nombre, telefono, email, password, rol, distrito):
    with _lock:
        cur = _conn.cursor()
        try:
            cur.execute(
                "INSERT INTO Usuarios (nombre, telefono, email, password, rol, distrito) VALUES (?,?,?,?,?,?)",
                (nombre, telefono, email, password, rol, distrito),
            )
            _conn.commit()
            user_id = cur.lastrowid
            if rol == "cuidador":
                cur.execute(
                    """INSERT INTO Cuidadores_Perfiles
                    (id_usuario, descripcion, experiencia_texto, tarifa_hora, certificaciones, disponibilidad, zona_trabajo)
                    VALUES (?,?,?,?,?,?,?)""",
                    (user_id, "", "", None, "", "", distrito),
                )
                _conn.commit()
            return user_id, None
        except sqlite3.IntegrityError:
            return None, "El correo ya está registrado"


def login_user(email, password):
    with _lock:
        cur = _conn.cursor()
        cur.execute("SELECT * FROM Usuarios WHERE email=? AND password=?", (email, password))
        row = cur.fetchone()
        return dict(row) if row else None


def get_user(user_id):
    with _lock:
        cur = _conn.cursor()
        cur.execute("SELECT * FROM Usuarios WHERE id=?", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def count_pets(id_dueno):
    with _lock:
        cur = _conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM Mascotas WHERE id_dueno=?", (id_dueno,))
        return cur.fetchone()["c"]


def save_image(foto_b64, foto_ext):
    if not foto_b64:
        return None
    filename = f"{uuid.uuid4().hex}.{foto_ext or 'png'}"
    full_path = os.path.join(STORAGE_DIR, filename)
    with open(full_path, "wb") as f:
        f.write(base64.b64decode(foto_b64))
    return os.path.join("storage", "mascotas", filename)


def create_pet(id_dueno, nombre, especie, raza, edad, cuidados_especiales, consideraciones, foto_b64, foto_ext):
    foto_path = save_image(foto_b64, foto_ext)
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            """INSERT INTO Mascotas
            (id_dueno, nombre, especie, raza, edad, cuidados_especiales, consideraciones, foto_path)
            VALUES (?,?,?,?,?,?,?,?)""",
            (id_dueno, nombre, especie, raza, edad, cuidados_especiales, consideraciones, foto_path),
        )
        _conn.commit()
        return cur.lastrowid


def get_pets_by_owner(id_dueno):
    with _lock:
        cur = _conn.cursor()
        cur.execute("SELECT * FROM Mascotas WHERE id_dueno=?", (id_dueno,))
        return [dict(r) for r in cur.fetchall()]


def get_pet(pet_id):
    with _lock:
        cur = _conn.cursor()
        cur.execute("SELECT * FROM Mascotas WHERE id=?", (pet_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def update_caregiver_profile(id_usuario, descripcion, experiencia_texto,
                              tarifa_hora=None, certificaciones=None,
                              disponibilidad=None, zona_trabajo=None):
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            """UPDATE Cuidadores_Perfiles
            SET descripcion=?, experiencia_texto=?, tarifa_hora=?, certificaciones=?,
                disponibilidad=?, zona_trabajo=?
            WHERE id_usuario=?""",
            (descripcion, experiencia_texto, tarifa_hora, certificaciones,
             disponibilidad, zona_trabajo, id_usuario),
        )
        _conn.commit()


def get_caregiver_profile(id_usuario):
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            """SELECT u.*, c.descripcion, c.experiencia_texto, c.tarifa_hora,
            c.certificaciones, c.disponibilidad, c.zona_trabajo
            FROM Usuarios u
            LEFT JOIN Cuidadores_Perfiles c ON u.id = c.id_usuario WHERE u.id=?""",
            (id_usuario,),
        )
        row = cur.fetchone()
        if not row:
            return None
        data = dict(row)
        cur.execute(
            "SELECT AVG(calificacion_estrellas) as prom, COUNT(*) as total FROM Contratos_Servicios WHERE id_cuidador=? AND calificacion_estrellas IS NOT NULL",
            (id_usuario,),
        )
        rating = cur.fetchone()
        data["rating_promedio"] = round(rating["prom"], 1) if rating["prom"] else 0
        data["rating_total"] = rating["total"]
        return data


def get_caregivers_by_district(distrito):
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            """SELECT u.*, c.descripcion, c.experiencia_texto, c.tarifa_hora,
            c.certificaciones, c.disponibilidad, c.zona_trabajo
            FROM Usuarios u
            LEFT JOIN Cuidadores_Perfiles c ON u.id = c.id_usuario
            WHERE u.rol='cuidador' AND (u.distrito=? OR c.zona_trabajo LIKE ?)""",
            (distrito, f"%{distrito}%"),
        )
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            cur.execute(
                "SELECT AVG(calificacion_estrellas) as prom, COUNT(*) as total FROM Contratos_Servicios WHERE id_cuidador=? AND calificacion_estrellas IS NOT NULL",
                (r["id"],),
            )
            rating = cur.fetchone()
            r["rating_promedio"] = round(rating["prom"], 1) if rating["prom"] else 0
            r["rating_total"] = rating["total"]
        # Ranking por confianza: mejor calificación promedio primero, luego más reseñas.
        rows.sort(key=lambda r: (r["rating_promedio"], r["rating_total"]), reverse=True)
        return rows


def create_contract(id_dueno, id_cuidador, id_mascota, fecha_inicio, duracion,
                     horario=None, ubicacion_servicio=None, presupuesto=None):
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            """INSERT INTO Contratos_Servicios
            (id_dueno, id_cuidador, id_mascota, fecha_inicio, duracion_horas_dias,
             horario, ubicacion_servicio, presupuesto, estado)
            VALUES (?,?,?,?,?,?,?,?, 'pendiente')""",
            (id_dueno, id_cuidador, id_mascota, fecha_inicio, duracion,
             horario, ubicacion_servicio, presupuesto),
        )
        _conn.commit()
        return cur.lastrowid


def update_contract_status(id_contrato, estado):
    with _lock:
        cur = _conn.cursor()
        cur.execute("UPDATE Contratos_Servicios SET estado=? WHERE id=?", (estado, id_contrato))
        _conn.commit()


def rate_contract(id_contrato, estrellas, comentario=None):
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            """UPDATE Contratos_Servicios
            SET calificacion_estrellas=?, comentario=?, estado='finalizado', fecha_calificacion=?
            WHERE id=?""",
            (estrellas, comentario, date.today().isoformat(), id_contrato),
        )
        _conn.commit()


def get_reviews_for_caregiver(id_cuidador):
    """Reseñas tipo tienda de apps: quién califica, estrellas, comentario y fecha."""
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            """SELECT cs.id, cs.calificacion_estrellas, cs.comentario, cs.fecha_calificacion,
            u.nombre as dueno_nombre, m.nombre as mascota_nombre
            FROM Contratos_Servicios cs
            JOIN Usuarios u ON cs.id_dueno = u.id
            LEFT JOIN Mascotas m ON cs.id_mascota = m.id
            WHERE cs.id_cuidador=? AND cs.calificacion_estrellas IS NOT NULL
            ORDER BY cs.id DESC""",
            (id_cuidador,),
        )
        return [dict(r) for r in cur.fetchall()]


def report_incident(id_contrato, id_reportante, descripcion, gravedad="baja"):
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            "INSERT INTO Incidentes (id_contrato, id_reportante, descripcion, gravedad, fecha) VALUES (?,?,?,?,?)",
            (id_contrato, id_reportante, descripcion, gravedad, date.today().isoformat()),
        )
        _conn.commit()
        return cur.lastrowid


def get_incidents_for_contract(id_contrato):
    with _lock:
        cur = _conn.cursor()
        cur.execute("SELECT * FROM Incidentes WHERE id_contrato=? ORDER BY id DESC", (id_contrato,))
        return [dict(r) for r in cur.fetchall()]


def register_payment(id_contrato, monto, metodo, estado_pago="pagado"):
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            "INSERT INTO Pagos (id_contrato, monto, metodo, estado_pago, fecha) VALUES (?,?,?,?,?)",
            (id_contrato, monto, metodo, estado_pago, date.today().isoformat()),
        )
        _conn.commit()
        return cur.lastrowid


def get_payments_for_contract(id_contrato):
    with _lock:
        cur = _conn.cursor()
        cur.execute("SELECT * FROM Pagos WHERE id_contrato=? ORDER BY id DESC", (id_contrato,))
        return [dict(r) for r in cur.fetchall()]


def get_contracts_for_owner(id_dueno):
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            """SELECT cs.*, u.nombre as cuidador_nombre, m.nombre as mascota_nombre
            FROM Contratos_Servicios cs
            JOIN Usuarios u ON cs.id_cuidador = u.id
            LEFT JOIN Mascotas m ON cs.id_mascota = m.id
            WHERE cs.id_dueno=? ORDER BY cs.id DESC""",
            (id_dueno,),
        )
        return [dict(r) for r in cur.fetchall()]


def get_contracts_for_caregiver(id_cuidador):
    with _lock:
        cur = _conn.cursor()
        cur.execute(
            """SELECT cs.*, u.nombre as dueno_nombre, u.telefono as dueno_telefono,
            m.nombre as mascota_nombre, m.especie, m.raza, m.edad,
            m.cuidados_especiales, m.consideraciones, m.foto_path
            FROM Contratos_Servicios cs
            JOIN Usuarios u ON cs.id_dueno = u.id
            LEFT JOIN Mascotas m ON cs.id_mascota = m.id
            WHERE cs.id_cuidador=? ORDER BY cs.id DESC""",
            (id_cuidador,),
        )
        return [dict(r) for r in cur.fetchall()]
