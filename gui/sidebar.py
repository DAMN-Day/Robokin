"""
Barra lateral de navegacion.

Cada elemento de `NAV_ITEMS` genera un boton; el activo se distingue por un
indicador vertical de acento y un fondo mas claro. La barra no conoce las
vistas: solo emite la clave seleccionada mediante `on_select`.
"""

from __future__ import annotations

from typing import Callable, Dict

import customtkinter as ctk

from config.settings import APP_NAME, APP_TAGLINE, APP_VERSION, NAV_ITEMS
from gui.theme import color, font, radius


class NavButton(ctk.CTkFrame):
    """Boton de navegacion con indicador de estado activo."""

    def __init__(self, master, key: str, label: str, caption: str, command: Callable[[str], None]):
        super().__init__(master, fg_color="transparent", corner_radius=radius("button"))
        self.key = key
        self._command = command
        self._active = False

        self.grid_columnconfigure(1, weight=1)

        # El indicador necesita un alto explicito: un CTkFrame sin alto conserva
        # los 200 px por defecto y, al estar anclado con sticky="ns", estiraria
        # todo el boton hasta sacar del panel a las ultimas pestanas.
        self._indicator = ctk.CTkFrame(
            self, width=3, height=30, fg_color="transparent", corner_radius=radius("pill")
        )
        self._indicator.grid(row=0, column=0, sticky="ns", padx=(0, 10), pady=8)

        textos = ctk.CTkFrame(self, fg_color="transparent")
        textos.grid(row=0, column=1, sticky="ew", pady=9)
        textos.grid_columnconfigure(0, weight=1)

        self._label = ctk.CTkLabel(
            textos,
            text=label,
            font=font(role="body", weight="bold"),
            text_color=color("text_muted"),
            anchor="w",
        )
        self._label.grid(row=0, column=0, sticky="w")

        self._caption = ctk.CTkLabel(
            textos,
            text=caption,
            font=font(role="tiny"),
            text_color=color("text_faint"),
            anchor="w",
        )
        self._caption.grid(row=1, column=0, sticky="w")

        for widget in (self, textos, self._label, self._caption):
            widget.bind("<Button-1>", self._click)
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)
            widget.configure(cursor="hand2")

    # ------------------------------------------------------------------ #
    def _click(self, _event=None) -> None:
        self._command(self.key)

    def _enter(self, _event=None) -> None:
        if not self._active:
            self.configure(fg_color=color("bg_card"))

    def _leave(self, _event=None) -> None:
        if not self._active:
            self.configure(fg_color="transparent")

    def set_active(self, active: bool) -> None:
        self._active = active
        self.configure(fg_color=color("bg_elevated") if active else "transparent")
        self._indicator.configure(fg_color=color("accent") if active else "transparent")
        self._label.configure(text_color=color("text") if active else color("text_muted"))


class Sidebar(ctk.CTkFrame):
    """Panel lateral izquierdo con la navegacion principal."""

    WIDTH = 246

    def __init__(self, master, on_select: Callable[[str], None]) -> None:
        super().__init__(
            master,
            width=self.WIDTH,
            fg_color=color("bg_sidebar"),
            corner_radius=0,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._on_select = on_select
        self._buttons: Dict[str, NavButton] = {}

        self._build_brand()
        self._build_nav()
        self._build_footer()

    # ------------------------------------------------------------------ #
    def _build_brand(self) -> None:
        marca = ctk.CTkFrame(self, fg_color="transparent")
        marca.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 18))
        marca.grid_columnconfigure(1, weight=1)

        ctk.CTkFrame(
            marca,
            width=10,
            height=34,
            fg_color=color("primary"),
            corner_radius=radius("pill"),
        ).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 12))

        ctk.CTkLabel(
            marca,
            text=APP_NAME,
            font=font(size=19, weight="bold"),
            text_color=color("text"),
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            marca,
            text=APP_TAGLINE,
            font=font(role="tiny"),
            text_color=color("text_faint"),
            anchor="w",
            wraplength=170,
            justify="left",
        ).grid(row=1, column=1, sticky="w")

    def _build_nav(self) -> None:
        ctk.CTkFrame(self, height=1, fg_color=color("border"), corner_radius=0).grid(
            row=1, column=0, sticky="ew", padx=16
        )

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.grid(row=2, column=0, sticky="new", padx=12, pady=16)
        contenedor.grid_columnconfigure(0, weight=1)

        for i, (clave, etiqueta, descripcion) in enumerate(NAV_ITEMS):
            boton = NavButton(contenedor, clave, etiqueta, descripcion, self._on_select)
            boton.grid(row=i, column=0, sticky="ew", pady=3)
            self._buttons[clave] = boton

    def _build_footer(self) -> None:
        pie = ctk.CTkFrame(self, fg_color="transparent")
        pie.grid(row=3, column=0, sticky="ew", padx=20, pady=18)
        pie.grid_columnconfigure(0, weight=1)

        ctk.CTkFrame(pie, height=1, fg_color=color("border"), corner_radius=0).grid(
            row=0, column=0, sticky="ew", pady=(0, 12)
        )
        ctk.CTkLabel(
            pie,
            text=f"Version {APP_VERSION}",
            font=font(role="tiny"),
            text_color=color("text_faint"),
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

    # ------------------------------------------------------------------ #
    def set_active(self, key: str) -> None:
        for clave, boton in self._buttons.items():
            boton.set_active(clave == key)
