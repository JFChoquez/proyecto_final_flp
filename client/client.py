import os
import re
import base64
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date

import net_client
from theme import (
    apply_style, BG, SURFACE, CARD_BG, PRIMARY, ACCENT, DANGER, TEXT, SUBTEXT,
    BORDER, STAR, FONT_H1, FONT_H2, FONT_BODY, FONT_SMALL, DISTRITOS,
)

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

BASE_DIR = os.path.dirname(__file__)


def load_thumbnail(rel_path, size=(90, 90)):
    if not rel_path or not HAS_PIL:
        return None
    full_path = os.path.join(BASE_DIR, rel_path)
    if not os.path.exists(full_path):
        return None
    try:
        img = Image.open(full_path)
        img.thumbnail(size)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def make_card(parent, **kwargs):
    frame = tk.Frame(parent, bg=CARD_BG, highlightbackground=BORDER,
                      highlightthickness=1, bd=0, **kwargs)
    return frame


def star_string(rating):
    full = int(round(rating))
    return "★" * full + "☆" * (5 - full)


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg=SURFACE):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", self._resize_inner)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _resize_inner(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Red Inteligente de Cuidadores de Mascotas")
        self.geometry("1000x680")
        self.minsize(900, 600)
        apply_style(self)
        self.current_user = None
        self._last_action = None
        self.container = tk.Frame(self, bg=SURFACE)
        self.container.pack(fill="both", expand=True)
        # F5 (o Ctrl+R) refresca la pantalla actual re-consultando al servidor.
        # Sirve para cuando la conexión se queda "colgada" o los datos no se actualizan solos.
        self.bind_all("<F5>", lambda e: self.refresh_current())
        self.bind_all("<Control-r>", lambda e: self.refresh_current())
        self.show_login()

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def refresh_current(self):
        """Vuelve a pedir los datos al servidor y redibuja la pantalla en la que estamos."""
        if self._last_action:
            self._last_action()

    def show_login(self):
        self._last_action = self.show_login
        self.clear_container()
        LoginScreen(self.container, self).pack(fill="both", expand=True)

    def show_register(self):
        self._last_action = self.show_register
        self.clear_container()
        RegisterScreen(self.container, self).pack(fill="both", expand=True)

    def show_pet_form(self, mandatory=False):
        self._last_action = lambda: self.show_pet_form(mandatory=mandatory)
        self.clear_container()
        PetFormScreen(self.container, self, mandatory=mandatory).pack(fill="both", expand=True)

    def show_owner_dashboard(self):
        self._last_action = self.show_owner_dashboard
        self.clear_container()
        OwnerDashboard(self.container, self).pack(fill="both", expand=True)

    def show_my_pets(self):
        self._last_action = self.show_my_pets
        self.clear_container()
        MyPetsScreen(self.container, self).pack(fill="both", expand=True)

    def show_my_requests_owner(self):
        self._last_action = self.show_my_requests_owner
        self.clear_container()
        OwnerRequestsScreen(self.container, self).pack(fill="both", expand=True)

    def show_caregiver_detail(self, caregiver):
        self._last_action = lambda: self.show_caregiver_detail(caregiver)
        self.clear_container()
        CaregiverDetailScreen(self.container, self, caregiver).pack(fill="both", expand=True)

    def show_caregiver_dashboard(self):
        self._last_action = self.show_caregiver_dashboard
        self.clear_container()
        CaregiverDashboard(self.container, self).pack(fill="both", expand=True)

    def show_caregiver_profile(self):
        self._last_action = self.show_caregiver_profile
        self.clear_container()
        CaregiverProfileScreen(self.container, self).pack(fill="both", expand=True)

    def show_my_profile(self):
        self._last_action = self.show_my_profile
        self.clear_container()
        ProfileScreen(self.container, self).pack(fill="both", expand=True)

    def logout(self):
        self.current_user = None
        self.show_login()

    def go_home(self):
        if not self.current_user:
            self.show_login()
        elif self.current_user["rol"] == "dueno":
            self.show_owner_dashboard()
        else:
            self.show_caregiver_dashboard()


class LoginScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=SURFACE)
        self.app = app
        wrapper = tk.Frame(self, bg=SURFACE)
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        card = make_card(wrapper, padx=40, pady=40)
        card.pack()

        tk.Label(card, text="🐾 Red de Cuidadores", font=FONT_H1, bg=CARD_BG, fg=TEXT).pack(pady=(0, 5))
        tk.Label(card, text="Ica y distritos aledaños", font=FONT_SMALL, bg=CARD_BG, fg=SUBTEXT).pack(pady=(0, 20))

        tk.Label(card, text="Correo electrónico", font=FONT_BODY, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        self.email_entry = ttk.Entry(card, width=32)
        self.email_entry.pack(pady=(2, 10))

        tk.Label(card, text="Contraseña", font=FONT_BODY, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        self.password_entry = ttk.Entry(card, width=32, show="*")
        self.password_entry.pack(pady=(2, 10))

        self.error_label = tk.Label(card, text="", font=FONT_SMALL, bg=CARD_BG, fg=DANGER)
        self.error_label.pack()

        ttk.Button(card, text="Iniciar sesión", style="Primary.TButton",
                   command=self.do_login).pack(fill="x", pady=(10, 5))
        ttk.Button(card, text="Crear una cuenta nueva", style="Link.TButton",
                   command=self.app.show_register).pack(fill="x")

    def do_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not email or not password:
            self.error_label.config(text="Completa todos los campos")
            return
        response = net_client.request("login", {"email": email, "password": password})
        if not response.get("ok"):
            self.error_label.config(text=response.get("error", "Error al iniciar sesión"))
            return
        user = response["user"]
        self.app.current_user = user
        if user["rol"] == "dueno" and not user.get("tiene_mascotas"):
            self.app.show_pet_form(mandatory=True)
        elif user["rol"] == "dueno":
            self.app.show_owner_dashboard()
        else:
            self.app.show_caregiver_dashboard()


class RegisterScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=SURFACE)
        self.app = app
        wrapper = tk.Frame(self, bg=SURFACE)
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        card = make_card(wrapper, padx=40, pady=30)
        card.pack()

        tk.Label(card, text="Crear cuenta", font=FONT_H1, bg=CARD_BG, fg=TEXT).pack(pady=(0, 15))

        form = tk.Frame(card, bg=CARD_BG)
        form.pack()

        self.nombre_entry = self._labeled_entry(form, "Nombre completo", 0)
        self.telefono_entry = self._labeled_entry(form, "Teléfono", 1)
        self.email_entry = self._labeled_entry(form, "Correo electrónico", 2)
        self.password_entry = self._labeled_entry(form, "Contraseña", 3, show="*")

        tk.Label(form, text="Distrito", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=4, column=0, sticky="w", pady=(6, 0))
        self.distrito_combo = ttk.Combobox(form, values=DISTRITOS, state="readonly", width=28)
        self.distrito_combo.current(0)
        self.distrito_combo.grid(row=4, column=1, pady=(6, 0), padx=(10, 0))

        tk.Label(form, text="Rol", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=5, column=0, sticky="w", pady=(10, 0))
        self.rol_var = tk.StringVar(value="dueno")
        roles_frame = tk.Frame(form, bg=CARD_BG)
        roles_frame.grid(row=5, column=1, sticky="w", pady=(10, 0), padx=(10, 0))
        ttk.Radiobutton(roles_frame, text="Dueño de mascota", variable=self.rol_var, value="dueno").pack(anchor="w")
        ttk.Radiobutton(roles_frame, text="Cuidador profesional", variable=self.rol_var, value="cuidador").pack(anchor="w")

        self.error_label = tk.Label(card, text="", font=FONT_SMALL, bg=CARD_BG, fg=DANGER)
        self.error_label.pack(pady=(10, 0))

        ttk.Button(card, text="Registrarme", style="Primary.TButton",
                   command=self.do_register).pack(fill="x", pady=(15, 5))
        ttk.Button(card, text="Ya tengo una cuenta", style="Link.TButton",
                   command=self.app.show_login).pack(fill="x")

    def _labeled_entry(self, parent, label, row, show=None):
        tk.Label(parent, text=label, font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, width=30, show=show) if show else ttk.Entry(parent, width=30)
        entry.grid(row=row, column=1, pady=4, padx=(10, 0))
        return entry

    def do_register(self):
        nombre = self.nombre_entry.get().strip()
        telefono = self.telefono_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        distrito = self.distrito_combo.get()
        rol = self.rol_var.get()

        if not all([nombre, telefono, email, password, distrito]):
            self.error_label.config(text="Completa todos los campos")
            return

        response = net_client.request("register", {
            "nombre": nombre, "telefono": telefono, "email": email,
            "password": password, "rol": rol, "distrito": distrito,
        })
        if not response.get("ok"):
            self.error_label.config(text=response.get("error", "Error al registrar"))
            return
        messagebox.showinfo("Registro exitoso", "Tu cuenta ha sido creada. Ahora inicia sesión.")
        self.app.show_login()


class PetFormScreen(tk.Frame):
    def __init__(self, parent, app, mandatory=False):
        super().__init__(parent, bg=SURFACE)
        self.app = app
        self.mandatory = mandatory
        self.foto_b64 = None
        self.foto_ext = None

        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill="x", padx=30, pady=(20, 10))
        title = "Registra a tu primera mascota" if mandatory else "Agregar nueva mascota"
        tk.Label(header, text=title, font=FONT_H1, bg=SURFACE, fg=TEXT).pack(anchor="w")
        if mandatory:
            tk.Label(header, text="Este paso es obligatorio antes de continuar",
                     font=FONT_SMALL, bg=SURFACE, fg=SUBTEXT).pack(anchor="w")

        card = make_card(self, padx=30, pady=20)
        card.pack(padx=30, pady=10, fill="x")

        form = tk.Frame(card, bg=CARD_BG)
        form.pack(fill="x")

        tk.Label(form, text="Nombre de la mascota", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=0, column=0, sticky="w", pady=5)
        self.nombre_entry = ttk.Entry(form, width=35)
        self.nombre_entry.grid(row=0, column=1, pady=5, padx=(10, 0))

        tk.Label(form, text="Especie", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=1, column=0, sticky="w", pady=5)
        self.especie_combo = ttk.Combobox(form, values=["Perro", "Gato", "Otros"], state="readonly", width=32)
        self.especie_combo.current(0)
        self.especie_combo.grid(row=1, column=1, pady=5, padx=(10, 0))

        tk.Label(form, text="Raza", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=2, column=0, sticky="w", pady=5)
        self.raza_entry = ttk.Entry(form, width=35)
        self.raza_entry.grid(row=2, column=1, pady=5, padx=(10, 0))

        tk.Label(form, text="Edad (años)", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=3, column=0, sticky="w", pady=5)
        self.edad_entry = ttk.Entry(form, width=35)
        self.edad_entry.grid(row=3, column=1, pady=5, padx=(10, 0))

        tk.Label(form, text="Cuidados especiales", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=4, column=0, sticky="nw", pady=5)
        self.cuidados_text = tk.Text(form, width=35, height=3, font=FONT_BODY)
        self.cuidados_text.grid(row=4, column=1, pady=5, padx=(10, 0))

        tk.Label(form, text="Consideraciones adicionales", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=5, column=0, sticky="nw", pady=5)
        self.consideraciones_text = tk.Text(form, width=35, height=3, font=FONT_BODY)
        self.consideraciones_text.grid(row=5, column=1, pady=5, padx=(10, 0))

        tk.Label(form, text="Foto de la mascota", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=6, column=0, sticky="w", pady=5)
        foto_frame = tk.Frame(form, bg=CARD_BG)
        foto_frame.grid(row=6, column=1, sticky="w", pady=5, padx=(10, 0))
        ttk.Button(foto_frame, text="Elegir imagen", command=self.choose_photo).pack(side="left")
        self.foto_label = tk.Label(foto_frame, text="Ningún archivo seleccionado", font=FONT_SMALL, bg=CARD_BG, fg=SUBTEXT)
        self.foto_label.pack(side="left", padx=10)

        self.error_label = tk.Label(card, text="", font=FONT_SMALL, bg=CARD_BG, fg=DANGER)
        self.error_label.pack(pady=(10, 0))

        buttons = tk.Frame(self, bg=SURFACE)
        buttons.pack(pady=15)
        ttk.Button(buttons, text="Guardar mascota", style="Primary.TButton",
                   command=self.save_pet).pack(side="left", padx=5)
        if not mandatory:
            ttk.Button(buttons, text="Cancelar", style="Link.TButton",
                       command=self.app.show_my_pets).pack(side="left", padx=5)

    def choose_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if not path:
            return
        with open(path, "rb") as f:
            self.foto_b64 = base64.b64encode(f.read()).decode("utf-8")
        self.foto_ext = os.path.splitext(path)[1].replace(".", "") or "png"
        self.foto_label.config(text=os.path.basename(path))

    def save_pet(self):
        nombre = self.nombre_entry.get().strip()
        raza = self.raza_entry.get().strip()
        edad = self.edad_entry.get().strip()
        especie = self.especie_combo.get()
        cuidados = self.cuidados_text.get("1.0", "end").strip()
        consideraciones = self.consideraciones_text.get("1.0", "end").strip()

        if not nombre or not especie:
            self.error_label.config(text="El nombre y la especie son obligatorios")
            return
        try:
            edad_val = int(edad) if edad else None
        except ValueError:
            self.error_label.config(text="La edad debe ser un número")
            return

        response = net_client.request("create_pet", {
            "id_dueno": self.app.current_user["id"], "nombre": nombre, "especie": especie,
            "raza": raza, "edad": edad_val, "cuidados_especiales": cuidados,
            "consideraciones": consideraciones, "foto_b64": self.foto_b64, "foto_ext": self.foto_ext,
        })
        if not response.get("ok"):
            self.error_label.config(text=response.get("error", "Error al guardar la mascota"))
            return
        self.app.current_user["tiene_mascotas"] = True
        if self.mandatory:
            self.app.show_owner_dashboard()
        else:
            self.app.show_my_pets()


class NavBar(tk.Frame):
    def __init__(self, parent, app, title, items):
        super().__init__(parent, bg=PRIMARY, height=60)
        self.pack_propagate(False)
        tk.Label(self, text=title, font=FONT_H2, bg=PRIMARY, fg="white").pack(side="left", padx=20)
        right = tk.Frame(self, bg=PRIMARY)
        right.pack(side="right", padx=15)
        for label, command in items:
            ttk.Button(right, text=label, style="Nav.TButton", command=command).pack(side="left", padx=5)
        # Botón visible para refrescar la conexión/datos (equivale a presionar F5).
        # Si algo se queda "colgado" o no se ve actualizado, esto lo resuelve.
        ttk.Button(right, text="⟳ Actualizar (F5)", style="Nav.TButton",
                   command=app.refresh_current).pack(side="left", padx=5)


class OwnerDashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=SURFACE)
        self.app = app
        user = app.current_user

        NavBar(self, app, "Panel del Dueño", [
            ("Mis Mascotas", app.show_my_pets),
            ("Mis Solicitudes", app.show_my_requests_owner),
            ("Mi Perfil", app.show_my_profile),
            ("Cerrar Sesión", app.logout),
        ]).pack(fill="x")

        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=25, pady=15)

        tk.Label(body, text=f"Cuidadores disponibles en {user['distrito']}",
                 font=FONT_H1, bg=SURFACE, fg=TEXT).pack(anchor="w", pady=(0, 2))
        tk.Label(body, text="Ordenados por ranking de confianza (mejor calificación y más reseñas primero)",
                 font=FONT_SMALL, bg=SURFACE, fg=SUBTEXT).pack(anchor="w", pady=(0, 15))

        response = net_client.request("get_caregivers", {"distrito": user["distrito"], "exclude_id": user["id"]})
        caregivers = response.get("caregivers", []) if response.get("ok") else []

        if not response.get("ok"):
            tk.Label(body, text=response.get("error", "Error de conexión"), fg=DANGER, bg=SURFACE).pack()
            return

        if not caregivers:
            tk.Label(body, text="Aún no hay cuidadores registrados en tu distrito.",
                     font=FONT_BODY, bg=SURFACE, fg=SUBTEXT).pack()
            return

        scroll = ScrollableFrame(body)
        scroll.pack(fill="both", expand=True)

        cols = 3
        for index, caregiver in enumerate(caregivers):
            row, col = divmod(index, cols)
            self.build_caregiver_card(scroll.inner, caregiver, index + 1).grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    def build_caregiver_card(self, parent, caregiver, ranking=None):
        card = make_card(parent, padx=15, pady=15, width=260, height=225)
        card.pack_propagate(False)
        nombre_txt = f"#{ranking}  {caregiver['nombre']}" if ranking else caregiver["nombre"]
        tk.Label(card, text=nombre_txt, font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        tk.Label(card, text=caregiver["distrito"], font=FONT_SMALL, bg=CARD_BG, fg=SUBTEXT).pack(anchor="w")
        rating_text = f"{star_string(caregiver['rating_promedio'])} ({caregiver['rating_total']})"
        tk.Label(card, text=rating_text, font=FONT_BODY, bg=CARD_BG, fg=STAR).pack(anchor="w", pady=(5, 2))
        tarifa = caregiver.get("tarifa_hora")
        tarifa_txt = f"S/ {tarifa:.2f} / hora" if tarifa else "Tarifa no especificada"
        tk.Label(card, text=tarifa_txt, font=FONT_SMALL, bg=CARD_BG, fg=ACCENT).pack(anchor="w", pady=(0, 5))
        desc = caregiver.get("descripcion") or "Sin descripción disponible"
        tk.Label(card, text=desc[:90] + ("..." if len(desc) > 90 else ""), font=FONT_SMALL,
                 bg=CARD_BG, fg=TEXT, wraplength=220, justify="left").pack(anchor="w")
        ttk.Button(card, text="Ver perfil", style="Primary.TButton",
                   command=lambda: self.app.show_caregiver_detail(caregiver)).pack(side="bottom", fill="x", pady=(10, 0))
        return card


class MyPetsScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=SURFACE)
        self.app = app

        NavBar(self, app, "Mis Mascotas", [
            ("Volver", app.show_owner_dashboard),
            ("Cerrar Sesión", app.logout),
        ]).pack(fill="x")

        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=25, pady=15)

        top = tk.Frame(body, bg=SURFACE)
        top.pack(fill="x")
        tk.Label(top, text="Mascotas registradas", font=FONT_H1, bg=SURFACE, fg=TEXT).pack(side="left")
        ttk.Button(top, text="+ Agregar mascota", style="Accent.TButton",
                   command=lambda: app.show_pet_form(mandatory=False)).pack(side="right")

        response = net_client.request("get_pets", {"id_dueno": app.current_user["id"]})
        pets = response.get("pets", []) if response.get("ok") else []

        scroll = ScrollableFrame(body)
        scroll.pack(fill="both", expand=True, pady=10)

        cols = 3
        for index, pet in enumerate(pets):
            row, col = divmod(index, cols)
            self.build_pet_card(scroll.inner, pet).grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    def build_pet_card(self, parent, pet):
        card = make_card(parent, padx=15, pady=15, width=260, height=220)
        card.pack_propagate(False)
        thumb = load_thumbnail(pet.get("foto_path"))
        if thumb:
            img_label = tk.Label(card, image=thumb, bg=CARD_BG)
            img_label.image = thumb
            img_label.pack(pady=(0, 8))
        tk.Label(card, text=pet["nombre"], font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        tk.Label(card, text=f"{pet['especie']} · {pet.get('raza') or 'N/A'}", font=FONT_SMALL,
                 bg=CARD_BG, fg=SUBTEXT).pack(anchor="w")
        tk.Label(card, text=f"Edad: {pet.get('edad') or 'N/A'}", font=FONT_SMALL,
                 bg=CARD_BG, fg=SUBTEXT).pack(anchor="w")
        return card


class OwnerRequestsScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=SURFACE)
        self.app = app

        NavBar(self, app, "Mis Solicitudes", [
            ("Volver", app.show_owner_dashboard),
            ("Cerrar Sesión", app.logout),
        ]).pack(fill="x")

        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=25, pady=15)

        response = net_client.request("get_contracts_owner", {"id_dueno": app.current_user["id"]})
        contracts = response.get("contracts", []) if response.get("ok") else []

        if not contracts:
            tk.Label(body, text="No has contratado ningún servicio todavía.",
                     font=FONT_BODY, bg=SURFACE, fg=SUBTEXT).pack(pady=20)
            return

        scroll = ScrollableFrame(body)
        scroll.pack(fill="both", expand=True)

        for contract in contracts:
            self.build_contract_row(scroll.inner, contract).pack(fill="x", pady=6)

    def build_contract_row(self, parent, contract):
        card = make_card(parent, padx=15, pady=12)
        info = tk.Frame(card, bg=CARD_BG)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=f"{contract['mascota_nombre']} con {contract['cuidador_nombre']}",
                 font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        tk.Label(info, text=f"Inicio: {contract['fecha_inicio']}  ·  Horario: {contract.get('horario') or 'N/A'}  ·  Duración: {contract['duracion_horas_dias']}",
                 font=FONT_SMALL, bg=CARD_BG, fg=SUBTEXT).pack(anchor="w")
        tk.Label(info, text=f"Ubicación: {contract.get('ubicacion_servicio') or 'N/A'}  ·  Presupuesto: "
                             f"{('S/ ' + format(contract['presupuesto'], '.2f')) if contract.get('presupuesto') else 'N/A'}",
                 font=FONT_SMALL, bg=CARD_BG, fg=SUBTEXT).pack(anchor="w")
        estado = contract["estado"]
        color = {"pendiente": STAR, "aceptado": ACCENT, "finalizado": SUBTEXT,
                 "rechazado": DANGER, "cancelado": DANGER}.get(estado, TEXT)
        tk.Label(info, text=f"Estado: {estado}", font=FONT_SMALL, bg=CARD_BG, fg=color).pack(anchor="w", pady=(2, 0))
        if contract.get("calificacion_estrellas"):
            tk.Label(info, text=star_string(contract["calificacion_estrellas"]) +
                     (f"  —  \"{contract['comentario']}\"" if contract.get("comentario") else ""),
                     font=FONT_BODY, bg=CARD_BG, fg=STAR, wraplength=400, justify="left").pack(anchor="w")

        actions = tk.Frame(card, bg=CARD_BG)
        actions.pack(side="right")
        if estado == "aceptado":
            ttk.Button(actions, text="Finalizar y calificar", style="Accent.TButton",
                       command=lambda: self.open_rating_dialog(contract)).pack(pady=2, fill="x")
            ttk.Button(actions, text="Reportar incidente", style="Danger.TButton",
                       command=lambda: self.open_incident_dialog(contract)).pack(pady=2, fill="x")
            ttk.Button(actions, text="Cancelar", style="Link.TButton",
                       command=lambda: self.cancel_contract(contract)).pack(pady=2, fill="x")
        elif estado == "pendiente":
            ttk.Button(actions, text="Cancelar solicitud", style="Link.TButton",
                       command=lambda: self.cancel_contract(contract)).pack(pady=2, fill="x")
        return card

    def cancel_contract(self, contract):
        if not messagebox.askyesno("Cancelar", "¿Seguro que deseas cancelar este servicio?"):
            return
        net_client.request("update_contract_status", {"id_contrato": contract["id"], "estado": "cancelado"})
        self.app.show_my_requests_owner()

    def open_incident_dialog(self, contract):
        dialog = tk.Toplevel(self)
        dialog.title("Reportar incidente")
        dialog.configure(bg=SURFACE)
        dialog.geometry("360x300")
        tk.Label(dialog, text=f"Reportar incidente — {contract['cuidador_nombre']}", font=FONT_H2,
                 bg=SURFACE, fg=TEXT, wraplength=320).pack(pady=15)

        tk.Label(dialog, text="Gravedad", font=FONT_BODY, bg=SURFACE, fg=TEXT).pack(anchor="w", padx=20)
        gravedad_var = tk.StringVar(value="media")
        gravedad_frame = tk.Frame(dialog, bg=SURFACE)
        gravedad_frame.pack(anchor="w", padx=20, pady=(0, 10))
        for value in ["baja", "media", "alta"]:
            ttk.Radiobutton(gravedad_frame, text=value.capitalize(), variable=gravedad_var, value=value).pack(side="left", padx=5)

        tk.Label(dialog, text="Descripción del incidente", font=FONT_BODY, bg=SURFACE, fg=TEXT).pack(anchor="w", padx=20)
        desc_text = tk.Text(dialog, width=38, height=6, font=FONT_BODY)
        desc_text.pack(padx=20, pady=(0, 10))

        def confirm():
            descripcion = desc_text.get("1.0", "end").strip()
            if not descripcion:
                messagebox.showwarning("Falta descripción", "Describe brevemente lo ocurrido.")
                return
            net_client.request("report_incident", {
                "id_contrato": contract["id"], "id_reportante": self.app.current_user["id"],
                "descripcion": descripcion, "gravedad": gravedad_var.get(),
            })
            dialog.destroy()
            messagebox.showinfo("Incidente registrado", "El incidente ha sido registrado en el sistema.")

        ttk.Button(dialog, text="Reportar", style="Danger.TButton", command=confirm).pack(pady=5, padx=20, fill="x")

    def open_rating_dialog(self, contract):
        dialog = tk.Toplevel(self)
        dialog.title("Calificar servicio")
        dialog.configure(bg=SURFACE)
        dialog.geometry("340x360")
        tk.Label(dialog, text=f"Califica a {contract['cuidador_nombre']}", font=FONT_H2,
                 bg=SURFACE, fg=TEXT).pack(pady=15)
        stars_var = tk.IntVar(value=5)
        stars_frame = tk.Frame(dialog, bg=SURFACE)
        stars_frame.pack()
        for value in range(1, 6):
            ttk.Radiobutton(stars_frame, text=f"{value} ★", variable=stars_var, value=value).pack(side="left", padx=3)

        tk.Label(dialog, text="Comentario (opcional)", font=FONT_BODY, bg=SURFACE, fg=TEXT).pack(anchor="w", padx=20, pady=(15, 0))
        comment_text = tk.Text(dialog, width=32, height=6, font=FONT_BODY)
        comment_text.pack(padx=20, pady=(5, 0))

        def confirm():
            comentario = comment_text.get("1.0", "end").strip()
            net_client.request("rate_contract", {
                "id_contrato": contract["id"], "estrellas": stars_var.get(), "comentario": comentario,
            })
            # Registramos el pago automáticamente al finalizar el servicio, usando el presupuesto acordado.
            if contract.get("presupuesto"):
                net_client.request("register_payment", {
                    "id_contrato": contract["id"], "monto": contract["presupuesto"],
                    "metodo": "efectivo/transferencia", "estado_pago": "pagado",
                })
            dialog.destroy()
            self.app.show_my_requests_owner()

        ttk.Button(dialog, text="Confirmar calificación", style="Primary.TButton",
                   command=confirm).pack(pady=20, padx=20, fill="x")


class CaregiverDetailScreen(tk.Frame):
    def __init__(self, parent, app, caregiver):
        super().__init__(parent, bg=SURFACE)
        self.app = app
        self.caregiver = caregiver

        NavBar(self, app, "Perfil del Cuidador", [
            ("Volver", app.show_owner_dashboard),
            ("Cerrar Sesión", app.logout),
        ]).pack(fill="x")

        profile_resp = net_client.request("get_caregiver_profile", {"id_usuario": caregiver["id"]})
        profile = profile_resp.get("profile", caregiver) if profile_resp.get("ok") else caregiver
        self.profile = profile

        reviews_resp = net_client.request("get_caregiver_reviews", {"id_cuidador": caregiver["id"]})
        reviews = reviews_resp.get("reviews", []) if reviews_resp.get("ok") else []

        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=30, pady=20)

        scroll = ScrollableFrame(body)
        scroll.pack(fill="both", expand=True)
        outer = scroll.inner

        # --- Encabezado / resumen ---
        card = make_card(outer, padx=25, pady=25)
        card.pack(fill="x")

        tk.Label(card, text=profile["nombre"], font=FONT_H1, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        tk.Label(card, text=f"{profile['distrito']}  ·  {profile.get('telefono', '')}",
                 font=FONT_SMALL, bg=CARD_BG, fg=SUBTEXT).pack(anchor="w", pady=(2, 8))
        tk.Label(card, text=star_string(profile.get("rating_promedio", 0)) + f"  {profile.get('rating_promedio', 0)}  ·  ({profile.get('rating_total', 0)} reseñas)",
                 font=FONT_H2, bg=CARD_BG, fg=STAR).pack(anchor="w", pady=(0, 10))

        # --- Datos clave: tarifa, disponibilidad, zona, certificaciones ---
        datos_frame = tk.Frame(card, bg=CARD_BG)
        datos_frame.pack(anchor="w", fill="x", pady=(0, 10))
        tarifa_txt = f"S/ {profile.get('tarifa_hora'):.2f} / hora" if profile.get("tarifa_hora") else "No especificada"
        datos = [
            ("Tarifa", tarifa_txt),
            ("Disponibilidad", profile.get("disponibilidad") or "No especificada"),
            ("Zona de trabajo", profile.get("zona_trabajo") or profile.get("distrito") or "No especificada"),
        ]
        for i, (label, value) in enumerate(datos):
            row = tk.Frame(datos_frame, bg=CARD_BG)
            row.pack(anchor="w", pady=2)
            tk.Label(row, text=f"{label}: ", font=(FONT_BODY[0], FONT_BODY[1], "bold"),
                     bg=CARD_BG, fg=TEXT).pack(side="left")
            tk.Label(row, text=value, font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                     wraplength=450, justify="left").pack(side="left")

        tk.Label(card, text="Certificaciones", font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(8, 0))
        tk.Label(card, text=profile.get("certificaciones") or "Sin certificaciones registradas", font=FONT_BODY,
                 bg=CARD_BG, fg=TEXT, wraplength=500, justify="left").pack(anchor="w", pady=(2, 10))

        tk.Label(card, text="Descripción", font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        tk.Label(card, text=profile.get("descripcion") or "Sin descripción", font=FONT_BODY,
                 bg=CARD_BG, fg=TEXT, wraplength=500, justify="left").pack(anchor="w", pady=(2, 10))

        tk.Label(card, text="Experiencia", font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        tk.Label(card, text=profile.get("experiencia_texto") or "Sin experiencia registrada", font=FONT_BODY,
                 bg=CARD_BG, fg=TEXT, wraplength=500, justify="left").pack(anchor="w", pady=(2, 5))

        # --- Reseñas y comentarios, tipo tienda de apps ---
        reviews_card = make_card(outer, padx=25, pady=20)
        reviews_card.pack(fill="x", pady=(15, 0))
        tk.Label(reviews_card, text=f"Reseñas y comentarios ({len(reviews)})", font=FONT_H2,
                 bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(0, 10))

        if not reviews:
            tk.Label(reviews_card, text="Este cuidador todavía no tiene reseñas.", font=FONT_BODY,
                     bg=CARD_BG, fg=SUBTEXT).pack(anchor="w")
        else:
            for review in reviews:
                self.build_review_row(reviews_card, review).pack(fill="x", pady=6)

        # --- Formulario de contratación ---
        contract_card = make_card(outer, padx=25, pady=20)
        contract_card.pack(fill="x", pady=(15, 0))
        tk.Label(contract_card, text="Contratar servicio", font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(0, 10))

        pets_resp = net_client.request("get_pets", {"id_dueno": app.current_user["id"]})
        pets = pets_resp.get("pets", []) if pets_resp.get("ok") else []
        pet_names = [f"{p['nombre']} (id {p['id']})" for p in pets]

        form = tk.Frame(contract_card, bg=CARD_BG)
        form.pack(anchor="w")

        tk.Label(form, text="Mascota", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=0, column=0, sticky="w", pady=5)
        self.pet_combo = ttk.Combobox(form, values=pet_names, state="readonly", width=30)
        if pet_names:
            self.pet_combo.current(0)
        self.pet_combo.grid(row=0, column=1, padx=(10, 0))

        tk.Label(form, text="Fecha de inicio (AAAA-MM-DD)", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=1, column=0, sticky="w", pady=5)
        self.fecha_entry = ttk.Entry(form, width=32)
        self.fecha_entry.insert(0, date.today().isoformat())
        self.fecha_entry.grid(row=1, column=1, padx=(10, 0))

        tk.Label(form, text="Horario (ej. 8:00am - 12:00pm)", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=2, column=0, sticky="w", pady=5)
        self.horario_entry = ttk.Entry(form, width=32)
        self.horario_entry.grid(row=2, column=1, padx=(10, 0))

        tk.Label(form, text="Duración (ej. 4 horas / 2 días)", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=3, column=0, sticky="w", pady=5)
        self.duracion_entry = ttk.Entry(form, width=32)
        self.duracion_entry.grid(row=3, column=1, padx=(10, 0))
        self.duracion_entry.bind("<KeyRelease>", lambda e: self.update_price_estimate())

        tk.Label(form, text="Ubicación del servicio", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=4, column=0, sticky="w", pady=5)
        self.ubicacion_entry = ttk.Entry(form, width=32)
        self.ubicacion_entry.insert(0, app.current_user.get("distrito", ""))
        self.ubicacion_entry.grid(row=4, column=1, padx=(10, 0))

        tk.Label(form, text="Presupuesto (S/, opcional)", font=FONT_BODY, bg=CARD_BG, fg=TEXT).grid(row=5, column=0, sticky="w", pady=5)
        self.presupuesto_entry = ttk.Entry(form, width=32)
        self.presupuesto_entry.grid(row=5, column=1, padx=(10, 0))

        self.pets = pets
        self.precio_label = tk.Label(contract_card, text="", font=FONT_SMALL, bg=CARD_BG, fg=SUBTEXT)
        self.precio_label.pack(anchor="w", pady=(8, 0))
        self.update_price_estimate()

        self.msg_label = tk.Label(contract_card, text="", font=FONT_SMALL, bg=CARD_BG, fg=ACCENT)
        self.msg_label.pack(anchor="w", pady=(4, 0))

        ttk.Button(contract_card, text="Contratar", style="Primary.TButton",
                   command=self.do_contract).pack(anchor="w", pady=(10, 0))

    def build_review_row(self, parent, review):
        row = make_card(parent, padx=15, pady=10)
        header = tk.Frame(row, bg=CARD_BG)
        header.pack(fill="x")
        tk.Label(header, text=review.get("dueno_nombre", "Usuario"), font=(FONT_BODY[0], FONT_BODY[1], "bold"),
                 bg=CARD_BG, fg=TEXT).pack(side="left")
        tk.Label(header, text=review.get("fecha_calificacion") or "", font=FONT_SMALL,
                 bg=CARD_BG, fg=SUBTEXT).pack(side="right")
        tk.Label(row, text=star_string(review.get("calificacion_estrellas", 0)), font=FONT_BODY,
                 bg=CARD_BG, fg=STAR).pack(anchor="w", pady=(2, 2))
        if review.get("mascota_nombre"):
            tk.Label(row, text=f"Servicio para: {review['mascota_nombre']}", font=FONT_SMALL,
                     bg=CARD_BG, fg=SUBTEXT).pack(anchor="w")
        tk.Label(row, text=review.get("comentario") or "Sin comentario adicional.", font=FONT_BODY,
                 bg=CARD_BG, fg=TEXT, wraplength=520, justify="left").pack(anchor="w", pady=(2, 0))
        return row

    def update_price_estimate(self):
        tarifa = self.profile.get("tarifa_hora")
        duracion = self.duracion_entry.get().strip()
        if not tarifa:
            self.precio_label.config(text="Precio estimado: el cuidador no registró una tarifa por hora.")
            return
        match = re.search(r"(\d+(?:\.\d+)?)", duracion)
        if match and "hora" in duracion.lower():
            horas = float(match.group(1))
            self.precio_label.config(text=f"Precio estimado: S/ {tarifa * horas:.2f} (según tarifa por hora)")
        elif match and "d" in duracion.lower():
            dias = float(match.group(1))
            self.precio_label.config(text=f"Precio estimado: S/ {tarifa * 8 * dias:.2f} (asumiendo 8h/día)")
        else:
            self.precio_label.config(text=f"Tarifa de referencia: S/ {tarifa:.2f} / hora")

    def do_contract(self):
        if not self.pets:
            messagebox.showwarning("Sin mascotas", "Registra una mascota antes de contratar un servicio.")
            return
        pet = self.pets[self.pet_combo.current()]
        fecha = self.fecha_entry.get().strip()
        duracion = self.duracion_entry.get().strip()
        horario = self.horario_entry.get().strip()
        ubicacion = self.ubicacion_entry.get().strip()
        presupuesto_raw = self.presupuesto_entry.get().strip()
        if not fecha or not duracion:
            self.msg_label.config(text="Completa la fecha y la duración", fg=DANGER)
            return
        if not ubicacion:
            self.msg_label.config(text="Indica la ubicación del servicio", fg=DANGER)
            return
        presupuesto = None
        if presupuesto_raw:
            try:
                presupuesto = float(presupuesto_raw)
            except ValueError:
                self.msg_label.config(text="El presupuesto debe ser un número", fg=DANGER)
                return
        response = net_client.request("create_contract", {
            "id_dueno": self.app.current_user["id"], "id_cuidador": self.caregiver["id"],
            "id_mascota": pet["id"], "fecha_inicio": fecha, "duracion": duracion,
            "horario": horario, "ubicacion_servicio": ubicacion, "presupuesto": presupuesto,
        })
        if response.get("ok"):
            self.msg_label.config(text="Solicitud enviada correctamente. Confirmación: contrato #" +
                                        str(response.get("contract_id")), fg=ACCENT)
        else:
            self.msg_label.config(text=response.get("error", "Error al contratar"), fg=DANGER)


class CaregiverDashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=SURFACE)
        self.app = app

        NavBar(self, app, "Panel del Cuidador", [
            ("Mi Perfil", app.show_my_profile),
            ("Experiencia", app.show_caregiver_profile),
            ("Cerrar Sesión", app.logout),
        ]).pack(fill="x")

        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=25, pady=15)

        tk.Label(body, text="Solicitudes de cuidado", font=FONT_H1, bg=SURFACE, fg=TEXT).pack(anchor="w", pady=(0, 15))

        response = net_client.request("get_contracts_caregiver", {"id_cuidador": app.current_user["id"]})
        contracts = response.get("contracts", []) if response.get("ok") else []

        if not contracts:
            tk.Label(body, text="No tienes solicitudes por el momento.", font=FONT_BODY,
                     bg=SURFACE, fg=SUBTEXT).pack()
            return

        scroll = ScrollableFrame(body)
        scroll.pack(fill="both", expand=True)

        for contract in contracts:
            self.build_request_card(scroll.inner, contract).pack(fill="x", pady=6)

    def build_request_card(self, parent, contract):
        card = make_card(parent, padx=15, pady=12)
        thumb = load_thumbnail(contract.get("foto_path"), size=(60, 60))
        if thumb:
            img_label = tk.Label(card, image=thumb, bg=CARD_BG)
            img_label.image = thumb
            img_label.pack(side="left", padx=(0, 15))

        info = tk.Frame(card, bg=CARD_BG)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=f"{contract['mascota_nombre']} ({contract.get('especie', '')})",
                 font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        tk.Label(info, text=f"Dueño: {contract['dueno_nombre']}  ·  Tel: {contract.get('dueno_telefono', '')}",
                 font=FONT_SMALL, bg=CARD_BG, fg=SUBTEXT).pack(anchor="w")
        tk.Label(info, text=f"Inicio: {contract['fecha_inicio']}  ·  Horario: {contract.get('horario') or 'N/A'}  ·  Duración: {contract['duracion_horas_dias']}",
                 font=FONT_SMALL, bg=CARD_BG, fg=SUBTEXT).pack(anchor="w")
        tk.Label(info, text=f"Ubicación: {contract.get('ubicacion_servicio') or 'N/A'}  ·  Presupuesto: "
                             f"{('S/ ' + format(contract['presupuesto'], '.2f')) if contract.get('presupuesto') else 'N/A'}",
                 font=FONT_SMALL, bg=CARD_BG, fg=SUBTEXT).pack(anchor="w")
        if contract.get("cuidados_especiales"):
            tk.Label(info, text=f"Cuidados especiales: {contract['cuidados_especiales']}", font=FONT_SMALL,
                     bg=CARD_BG, fg=TEXT, wraplength=400, justify="left").pack(anchor="w")
        estado = contract["estado"]
        color = {"pendiente": STAR, "aceptado": ACCENT, "finalizado": SUBTEXT,
                 "rechazado": DANGER, "cancelado": DANGER}.get(estado, TEXT)
        tk.Label(info, text=f"Estado: {estado}", font=FONT_SMALL, bg=CARD_BG, fg=color).pack(anchor="w", pady=(4, 0))
        if contract.get("calificacion_estrellas"):
            tk.Label(info, text=star_string(contract["calificacion_estrellas"]) +
                     (f"  —  \"{contract['comentario']}\"" if contract.get("comentario") else ""),
                     font=FONT_BODY, bg=CARD_BG, fg=STAR, wraplength=380, justify="left").pack(anchor="w")

        actions = tk.Frame(card, bg=CARD_BG)
        actions.pack(side="right")
        if estado == "pendiente":
            ttk.Button(actions, text="Aceptar", style="Accent.TButton",
                       command=lambda: self.respond(contract["id"], "aceptado")).pack(pady=2, fill="x")
            ttk.Button(actions, text="Rechazar", style="Danger.TButton",
                       command=lambda: self.respond(contract["id"], "rechazado")).pack(pady=2, fill="x")
        elif estado == "aceptado":
            ttk.Button(actions, text="Reportar incidente", style="Danger.TButton",
                       command=lambda: self.open_incident_dialog(contract)).pack(pady=2, fill="x")
        return card

    def respond(self, contract_id, estado):
        net_client.request("update_contract_status", {"id_contrato": contract_id, "estado": estado})
        self.app.show_caregiver_dashboard()

    def open_incident_dialog(self, contract):
        dialog = tk.Toplevel(self)
        dialog.title("Reportar incidente")
        dialog.configure(bg=SURFACE)
        dialog.geometry("360x300")
        tk.Label(dialog, text=f"Reportar incidente — {contract['dueno_nombre']}", font=FONT_H2,
                 bg=SURFACE, fg=TEXT, wraplength=320).pack(pady=15)

        tk.Label(dialog, text="Gravedad", font=FONT_BODY, bg=SURFACE, fg=TEXT).pack(anchor="w", padx=20)
        gravedad_var = tk.StringVar(value="media")
        gravedad_frame = tk.Frame(dialog, bg=SURFACE)
        gravedad_frame.pack(anchor="w", padx=20, pady=(0, 10))
        for value in ["baja", "media", "alta"]:
            ttk.Radiobutton(gravedad_frame, text=value.capitalize(), variable=gravedad_var, value=value).pack(side="left", padx=5)

        tk.Label(dialog, text="Descripción del incidente", font=FONT_BODY, bg=SURFACE, fg=TEXT).pack(anchor="w", padx=20)
        desc_text = tk.Text(dialog, width=38, height=6, font=FONT_BODY)
        desc_text.pack(padx=20, pady=(0, 10))

        def confirm():
            descripcion = desc_text.get("1.0", "end").strip()
            if not descripcion:
                messagebox.showwarning("Falta descripción", "Describe brevemente lo ocurrido.")
                return
            net_client.request("report_incident", {
                "id_contrato": contract["id"], "id_reportante": self.app.current_user["id"],
                "descripcion": descripcion, "gravedad": gravedad_var.get(),
            })
            dialog.destroy()
            messagebox.showinfo("Incidente registrado", "El incidente ha sido registrado en el sistema.")

        ttk.Button(dialog, text="Reportar", style="Danger.TButton", command=confirm).pack(pady=5, padx=20, fill="x")


class CaregiverProfileScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=SURFACE)
        self.app = app

        NavBar(self, app, "Mi Experiencia", [
            ("Volver", app.show_caregiver_dashboard),
            ("Cerrar Sesión", app.logout),
        ]).pack(fill="x")

        response = net_client.request("get_caregiver_profile", {"id_usuario": app.current_user["id"]})
        profile = response.get("profile", {}) if response.get("ok") else {}
        self.profile = profile

        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=30, pady=20)

        scroll = ScrollableFrame(body)
        scroll.pack(fill="both", expand=True)

        card = make_card(scroll.inner, padx=25, pady=25)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Descripción personal", font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        self.desc_text = tk.Text(card, width=70, height=4, font=FONT_BODY)
        self.desc_text.insert("1.0", profile.get("descripcion") or "")
        self.desc_text.pack(anchor="w", pady=(5, 15))

        tk.Label(card, text="Experiencia y trabajos anteriores", font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        self.exp_text = tk.Text(card, width=70, height=6, font=FONT_BODY)
        self.exp_text.insert("1.0", profile.get("experiencia_texto") or "")
        self.exp_text.pack(anchor="w", pady=(5, 15))

        tk.Label(card, text="Certificaciones (ej. veterinaria, adiestramiento, primeros auxilios)",
                 font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        self.cert_text = tk.Text(card, width=70, height=3, font=FONT_BODY)
        self.cert_text.insert("1.0", profile.get("certificaciones") or "")
        self.cert_text.pack(anchor="w", pady=(5, 15))

        tarifa_frame = tk.Frame(card, bg=CARD_BG)
        tarifa_frame.pack(anchor="w", fill="x", pady=(0, 15))
        tk.Label(tarifa_frame, text="Tarifa por hora (S/)", font=FONT_H2, bg=CARD_BG, fg=TEXT).grid(
            row=0, column=0, sticky="w")
        self.tarifa_entry = ttk.Entry(tarifa_frame, width=15)
        self.tarifa_entry.insert(0, str(profile.get("tarifa_hora") or ""))
        self.tarifa_entry.grid(row=0, column=1, padx=(10, 0))

        tk.Label(card, text="Disponibilidad (ej. Lunes a Viernes 8am - 6pm, fines de semana bajo cita)",
                 font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        self.disp_entry = ttk.Entry(card, width=70)
        self.disp_entry.insert(0, profile.get("disponibilidad") or "")
        self.disp_entry.pack(anchor="w", pady=(5, 15))

        tk.Label(card, text="Zona(s) de trabajo", font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(0, 5))
        zonas_actuales = {z.strip() for z in (profile.get("zona_trabajo") or "").split(",") if z.strip()}
        zonas_frame = tk.Frame(card, bg=CARD_BG)
        zonas_frame.pack(anchor="w", fill="x", pady=(0, 15))
        self.zona_vars = {}
        for i, distrito in enumerate(DISTRITOS):
            var = tk.BooleanVar(value=distrito in zonas_actuales)
            self.zona_vars[distrito] = var
            ttk.Checkbutton(zonas_frame, text=distrito, variable=var).grid(
                row=i // 3, column=i % 3, sticky="w", padx=5, pady=2)

        self.msg_label = tk.Label(card, text="", font=FONT_SMALL, bg=CARD_BG, fg=ACCENT)
        self.msg_label.pack(anchor="w")

        ttk.Button(card, text="Guardar cambios", style="Primary.TButton",
                   command=self.save).pack(anchor="w", pady=(10, 0))

    def save(self):
        descripcion = self.desc_text.get("1.0", "end").strip()
        experiencia = self.exp_text.get("1.0", "end").strip()
        certificaciones = self.cert_text.get("1.0", "end").strip()
        disponibilidad = self.disp_entry.get().strip()
        zona_trabajo = ",".join(d for d, var in self.zona_vars.items() if var.get())
        tarifa_raw = self.tarifa_entry.get().strip()
        try:
            tarifa_hora = float(tarifa_raw) if tarifa_raw else None
        except ValueError:
            self.msg_label.config(text="La tarifa debe ser un número", fg=DANGER)
            return
        net_client.request("update_caregiver_profile", {
            "id_usuario": self.app.current_user["id"], "descripcion": descripcion,
            "experiencia_texto": experiencia, "tarifa_hora": tarifa_hora,
            "certificaciones": certificaciones, "disponibilidad": disponibilidad,
            "zona_trabajo": zona_trabajo,
        })
        self.msg_label.config(text="Perfil actualizado correctamente", fg=ACCENT)


class ProfileScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=SURFACE)
        self.app = app
        user = app.current_user

        NavBar(self, app, "Mi Perfil", [
            ("Volver", app.go_home),
            ("Cerrar Sesión", app.logout),
        ]).pack(fill="x")

        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=30, pady=20)

        scroll = ScrollableFrame(body)
        scroll.pack(fill="both", expand=True)

        card = make_card(scroll.inner, padx=25, pady=25)
        card.pack(fill="x")

        tk.Label(card, text=user["nombre"], font=FONT_H1, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        rol_label = "Dueño de mascota" if user["rol"] == "dueno" else "Cuidador profesional"
        tk.Label(card, text=rol_label, font=FONT_BODY, bg=CARD_BG, fg=SUBTEXT).pack(anchor="w", pady=(0, 15))

        for label, value in [
            ("Correo", user.get("email")),
            ("Teléfono (contacto)", user.get("telefono")),
            ("Distrito (ubicación)", user.get("distrito")),
        ]:
            row = tk.Frame(card, bg=CARD_BG)
            row.pack(anchor="w", pady=3)
            tk.Label(row, text=f"{label}: ", font=FONT_BODY, bg=CARD_BG, fg=SUBTEXT).pack(side="left")
            tk.Label(row, text=value, font=FONT_BODY, bg=CARD_BG, fg=TEXT).pack(side="left")

        if user["rol"] == "dueno":
            pets_resp = net_client.request("get_pets", {"id_dueno": user["id"]})
            pets = pets_resp.get("pets", []) if pets_resp.get("ok") else []
            contracts_resp = net_client.request("get_contracts_owner", {"id_dueno": user["id"]})
            contracts = contracts_resp.get("contracts", []) if contracts_resp.get("ok") else []
            activos = [c for c in contracts if c["estado"] in ("pendiente", "aceptado")]
            finalizados = [c for c in contracts if c["estado"] == "finalizado"]

            tk.Label(card, text="Resumen de actividad", font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(15, 5))
            for label, value in [
                ("Mascotas registradas", len(pets)),
                ("Servicios activos/pendientes", len(activos)),
                ("Servicios finalizados", len(finalizados)),
            ]:
                row = tk.Frame(card, bg=CARD_BG)
                row.pack(anchor="w", pady=2)
                tk.Label(row, text=f"{label}: ", font=FONT_BODY, bg=CARD_BG, fg=SUBTEXT).pack(side="left")
                tk.Label(row, text=str(value), font=FONT_BODY, bg=CARD_BG, fg=TEXT).pack(side="left")

            buttons = tk.Frame(card, bg=CARD_BG)
            buttons.pack(anchor="w", pady=(15, 0))
            ttk.Button(buttons, text="Ver mis mascotas", style="Primary.TButton",
                       command=app.show_my_pets).pack(side="left", padx=(0, 8))
            ttk.Button(buttons, text="Ver mis solicitudes", style="Primary.TButton",
                       command=app.show_my_requests_owner).pack(side="left")
        else:
            profile_resp = net_client.request("get_caregiver_profile", {"id_usuario": user["id"]})
            profile = profile_resp.get("profile", {}) if profile_resp.get("ok") else {}

            tk.Label(card, text="Resumen profesional", font=FONT_H2, bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(15, 5))
            tarifa = profile.get("tarifa_hora")
            tarifa_txt = f"S/ {tarifa:.2f} / hora" if tarifa else "No especificada"
            for label, value in [
                ("Tarifa", tarifa_txt),
                ("Disponibilidad", profile.get("disponibilidad") or "No especificada"),
                ("Zona(s) de trabajo", profile.get("zona_trabajo") or profile.get("distrito") or "No especificada"),
                ("Certificaciones", profile.get("certificaciones") or "Ninguna registrada"),
            ]:
                row = tk.Frame(card, bg=CARD_BG)
                row.pack(anchor="w", pady=2)
                tk.Label(row, text=f"{label}: ", font=FONT_BODY, bg=CARD_BG, fg=SUBTEXT).pack(side="left")
                tk.Label(row, text=str(value), font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                         wraplength=450, justify="left").pack(side="left")

            tk.Label(card, text=star_string(profile.get("rating_promedio", 0)) +
                     f"  {profile.get('rating_promedio', 0)}  ·  ({profile.get('rating_total', 0)} reseñas)",
                     font=FONT_H2, bg=CARD_BG, fg=STAR).pack(anchor="w", pady=(10, 0))

            ttk.Button(card, text="Editar mi experiencia y tarifas", style="Primary.TButton",
                       command=app.show_caregiver_profile).pack(anchor="w", pady=(15, 0))


if __name__ == "__main__":
    app = App()
    app.mainloop()