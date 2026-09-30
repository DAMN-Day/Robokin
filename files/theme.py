"""
Tema de la aplicacion.

Resuelve las familias tipograficas disponibles en el sistema, cachea objetos
`CTkFont` y expone atajos de color. Todas las vistas deben tomar colores desde
`color()` y fuentes desde `font()` para mantener una sola fuente de verdad.
"""

from __future__ import annotations

import tkinter.font as tkfont
from typing import Dict, Optional, Sequence, Tuple

import customtkinter as ctk

from config.settings import (
    FONT_SIZES,
    MONO_FONT_CANDIDATES,
    PALETTE,
    RADIUS,
    UI_FONT_CANDIDATES,
)

_FONT_CACHE: Dict[Tuple[str, int, str, bool], ctk.CTkFont] = {}
_FAMILIES: Dict[str, str] = {}


def initialize() -> None:
    """Configura el modo de apariencia y el tema base de CustomTkinter."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def _resolve_family(candidates: Sequence[str], fallback: str) -> str:
    try:
        disponibles = set(tkfont.families())
    except Exception:  # pragma: no cover - sin root aun
        return fallback
    for candidata in candidates:
        if candidata in disponibles:
            return candidata
    return fallback


def ui_family() -> str:
    if "ui" not in _FAMILIES:
        _FAMILIES["ui"] = _resolve_family(UI_FONT_CANDIDATES, "TkDefaultFont")
    return _FAMILIES["ui"]


def mono_family() -> str:
    if "mono" not in _FAMILIES:
        _FAMILIES["mono"] = _resolve_family(MONO_FONT_CANDIDATES, "TkFixedFont")
    return _FAMILIES["mono"]


def font(
    size: Optional[int] = None,
    weight: str = "normal",
    mono: bool = False,
    role: Optional[str] = None,
) -> ctk.CTkFont:
    """Devuelve (y cachea) una fuente del tema.

    Args:
        size: tamano explicito en puntos.
        weight: 'normal' o 'bold'.
        mono: usar familia monoespaciada (matrices, expresiones).
        role: alternativa a `size` usando las claves de FONT_SIZES.
    """
    if size is None:
        size = FONT_SIZES.get(role or "body", FONT_SIZES["body"])
    familia = mono_family() if mono else ui_family()
    clave = (familia, size, weight, mono)
    if clave not in _FONT_CACHE:
        _FONT_CACHE[clave] = ctk.CTkFont(family=familia, size=size, weight=weight)
    return _FONT_CACHE[clave]


def color(name: str) -> str:
    """Color del tema por nombre."""
    try:
        return PALETTE[name]
    except KeyError as exc:  # pragma: no cover
        raise KeyError(f"Color '{name}' no definido en la paleta.") from exc


def radius(name: str) -> int:
    return RADIUS[name]
