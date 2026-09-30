"""
Configuracion global de la aplicacion.

Centraliza identidad visual y limites del modelo. Cambiar un color aqui se
propaga a toda la interfaz, sin tocar las vistas.
"""

from __future__ import annotations

APP_NAME = "RoboKin Studio"
APP_TAGLINE = "Analisis cinematico de manipuladores seriales"
APP_VERSION = "0.1.0"

WINDOW_SIZE = (1360, 820)
MIN_WINDOW_SIZE = (1120, 680)

# --------------------------------------------------------------------------- #
# Paleta (azules profundos + acento cian para datos calculados)
# --------------------------------------------------------------------------- #
PALETTE = {
    "bg_app": "#0A1524",
    "bg_sidebar": "#0E1D31",
    "bg_card": "#132741",
    "bg_elevated": "#18304F",
    "bg_input": "#0F2138",
    "bg_disabled": "#152A45",
    "bg_matrix": "#0D2039",
    "border": "#20395C",
    "border_focus": "#2D7FF9",
    "primary": "#2D7FF9",
    "primary_hover": "#1C64D1",
    "secondary": "#1B3557",
    "secondary_hover": "#234571",
    "accent": "#4FD1E0",
    "text": "#E6EEF9",
    "text_muted": "#8CA6C6",
    "text_faint": "#5C78A0",
    "success": "#3FC79A",
    "warning": "#E8B14C",
    "error": "#F2688A",
}

# --------------------------------------------------------------------------- #
# Geometria: bordes suaves en toda la interfaz
# --------------------------------------------------------------------------- #
RADIUS = {
    "card": 16,
    "panel": 20,
    "widget": 10,
    "button": 12,
    "pill": 999,
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 14,
    "lg": 20,
    "xl": 28,
}

# --------------------------------------------------------------------------- #
# Tipografia (familias candidatas; se resuelve la primera disponible)
# --------------------------------------------------------------------------- #
UI_FONT_CANDIDATES = ("Segoe UI", "Inter", "Ubuntu", "DejaVu Sans", "Helvetica")
MONO_FONT_CANDIDATES = ("Cascadia Mono", "Consolas", "JetBrains Mono", "DejaVu Sans Mono", "Courier New")

FONT_SIZES = {
    "display": 24,
    "title": 18,
    "subtitle": 13,
    "body": 13,
    "small": 12,
    "tiny": 11,
}

# --------------------------------------------------------------------------- #
# Limites del modelo
# --------------------------------------------------------------------------- #
MIN_JOINTS = 1
MAX_JOINTS = 10
DEFAULT_JOINTS = 3
DECIMALS = 4

# --------------------------------------------------------------------------- #
# Navegacion lateral: (clave, etiqueta, descripcion)
# --------------------------------------------------------------------------- #
NAV_ITEMS = [
    ("forward", "Cinematica directa", "Denavit-Hartenberg"),
    ("inverse", "Cinematica inversa", "Solucion de configuraciones"),
    ("trajectory", "Planeacion de trayectoria", "Perfiles y interpolacion"),
    ("twin", "Gemelo digital", "Simulacion en linea"),
]
