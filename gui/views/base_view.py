"""
Vista base de la que heredan todas las pestanas.

Aporta el encabezado (titulo + subtitulo + area de acciones) y delega el
contenido a `build_body`. Agregar una pestana nueva es crear una subclase,
implementar `build_body` y registrarla en `gui/app.py`.
"""

from __future__ import annotations

from typing import List, Optional

import customtkinter as ctk

from gui.components.cards import Badge
from gui.theme import color, font, radius


class BaseView(ctk.CTkFrame):
    TITLE: str = ""
    SUBTITLE: str = ""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color=color("bg_app"), corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        self.build_body(self.body)

    # ------------------------------------------------------------------ #
    def _build_header(self) -> None:
        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 18))
        encabezado.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            encabezado,
            text=self.TITLE,
            font=font(role="display", weight="bold"),
            text_color=color("text"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        if self.SUBTITLE:
            ctk.CTkLabel(
                encabezado,
                text=self.SUBTITLE,
                font=font(role="subtitle"),
                text_color=color("text_muted"),
                anchor="w",
            ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Un CTkFrame vacio conserva su tamano por defecto (200x200) y estiraria
        # el encabezado, asi que se crea con dimensiones nulas: crecera solo si
        # una vista le agrega contenido.
        self.header_actions = ctk.CTkFrame(
            encabezado, fg_color="transparent", width=0, height=0
        )
        self.header_actions.grid(row=0, column=1, rowspan=2, sticky="e")

    # ------------------------------------------------------------------ #
    def build_body(self, parent: ctk.CTkFrame) -> None:  # pragma: no cover
        raise NotImplementedError

    def on_show(self) -> None:
        """Se invoca cada vez que la vista pasa a primer plano."""


class PlaceholderView(BaseView):
    """Pestana reservada: describe el alcance previsto del modulo."""

    ROADMAP: List[str] = []

    def build_body(self, parent: ctk.CTkFrame) -> None:
        Badge(self.header_actions, "En desarrollo", tone="warning").grid(row=0, column=0)

        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        lienzo = ctk.CTkFrame(
            parent,
            fg_color=color("bg_card"),
            corner_radius=radius("panel"),
            border_width=1,
            border_color=color("border"),
        )
        lienzo.grid(row=0, column=0, sticky="nsew")
        lienzo.grid_columnconfigure(0, weight=1)
        lienzo.grid_rowconfigure(0, weight=1)
        lienzo.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            lienzo,
            text="Modulo aun sin implementar",
            font=font(role="title", weight="bold"),
            text_color=color("text"),
        ).grid(row=1, column=0, pady=(0, 8))

        if self.ROADMAP:
            lista = ctk.CTkFrame(lienzo, fg_color="transparent")
            lista.grid(row=2, column=0)
            for i, punto in enumerate(self.ROADMAP):
                ctk.CTkLabel(
                    lista,
                    text=f"\u2022  {punto}",
                    font=font(role="small"),
                    text_color=color("text_muted"),
                    anchor="w",
                ).grid(row=i, column=0, sticky="w", pady=2)
