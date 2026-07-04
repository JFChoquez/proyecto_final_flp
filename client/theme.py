from tkinter import ttk

BG = "#FFFFFF"
SURFACE = "#F5F6F8"
CARD_BG = "#FFFFFF"
PRIMARY = "#4285F4"
PRIMARY_DARK = "#3367D6"
ACCENT = "#34A853"
DANGER = "#EA4335"
TEXT = "#202124"
SUBTEXT = "#5F6368"
BORDER = "#E0E0E0"
STAR = "#FBBC05"

FONT_FAMILY = "Segoe UI"
FONT_H1 = (FONT_FAMILY, 20, "bold")
FONT_H2 = (FONT_FAMILY, 15, "bold")
FONT_BODY = (FONT_FAMILY, 11)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_BUTTON = (FONT_FAMILY, 11, "bold")

DISTRITOS = [
    "Ica", "Subtanjalla", "Parcona", "La Tinguiña", "San Juan Bautista",
    "Los Aquijes", "Pueblo Nuevo", "Salas", "Tate", "Yauca del Rosario",
]


def apply_style(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(bg=SURFACE)

    style.configure("TFrame", background=SURFACE)
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("Surface.TFrame", background=SURFACE)

    style.configure("TLabel", background=SURFACE, foreground=TEXT, font=FONT_BODY)
    style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT, font=FONT_BODY)
    style.configure("H1.TLabel", background=SURFACE, foreground=TEXT, font=FONT_H1)
    style.configure("H2.TLabel", background=SURFACE, foreground=TEXT, font=FONT_H2)
    style.configure("CardH2.TLabel", background=CARD_BG, foreground=TEXT, font=FONT_H2)
    style.configure("Sub.TLabel", background=SURFACE, foreground=SUBTEXT, font=FONT_SMALL)
    style.configure("CardSub.TLabel", background=CARD_BG, foreground=SUBTEXT, font=FONT_SMALL)
    style.configure("Nav.TLabel", background=PRIMARY, foreground="white", font=FONT_H2)
    style.configure("NavItem.TLabel", background=PRIMARY, foreground="white", font=FONT_BODY)
    style.configure("Error.TLabel", background=SURFACE, foreground=DANGER, font=FONT_SMALL)
    style.configure("Star.TLabel", background=CARD_BG, foreground=STAR, font=(FONT_FAMILY, 12))

    style.configure("Primary.TButton", background=PRIMARY, foreground="white",
                     font=FONT_BUTTON, borderwidth=0, padding=10)
    style.map("Primary.TButton", background=[("active", PRIMARY_DARK)])

    style.configure("Accent.TButton", background=ACCENT, foreground="white",
                     font=FONT_BUTTON, borderwidth=0, padding=8)
    style.map("Accent.TButton", background=[("active", "#2C8C46")])

    style.configure("Danger.TButton", background=DANGER, foreground="white",
                     font=FONT_BUTTON, borderwidth=0, padding=8)
    style.map("Danger.TButton", background=[("active", "#C5221F")])

    style.configure("Link.TButton", background=SURFACE, foreground=PRIMARY,
                     font=FONT_BODY, borderwidth=0)
    style.map("Link.TButton", background=[("active", SURFACE)])

    style.configure("Nav.TButton", background=PRIMARY, foreground="white",
                     font=FONT_BODY, borderwidth=0, padding=6)
    style.map("Nav.TButton", background=[("active", PRIMARY_DARK)])

    style.configure("TEntry", fieldbackground="white", padding=6, font=FONT_BODY)
    style.configure("TCombobox", fieldbackground="white", padding=6, font=FONT_BODY)
    style.configure("TRadiobutton", background=SURFACE, font=FONT_BODY)

    return style