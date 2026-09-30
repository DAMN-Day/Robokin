"""Contenedores con bordes suaves reutilizados por todas las vistas."""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from gui.theme import color, font, radius


class Card(ctk.CTkFrame):
    """Panel redondeado con titulo opcional y area de contenido.

    El contenido se agrega dentro de `card.body`, nunca directamente sobre la
    tarjeta, para que el encabezado conserve su posicion.
    """

    def __init__(
        self,
        master,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        elevated: bool = False,
        padding: int = 16,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=color("bg_elevated" if elevated else "bg_card"),
            corner_radius=radius("card"),
            border_width=1,
            border_color=color("border"),
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        fila = 0
        if title:
            encabezado = ctk.CTkFrame(self, fg_color="transparent")
            encabezado.grid(row=0, column=0, sticky="ew", padx=padding, pady=(padding, 0))
            encabezado.grid_columnconfigure(0, weight=1)

            self.title_label = ctk.CTkLabel(
                encabezado,
                text=title,
                font=font(role="title", weight="bold"),
                text_color=color("text"),
                anchor="w",
            )
            self.title_label.grid(row=0, column=0, sticky="w")

            if caption:
                self.caption_label = ctk.CTkLabel(
                    encabezado,
                    text=caption,
                    font=font(role="small"),
                    text_color=color("text_muted"),
                    anchor="w",
                    justify="left",
                )
                self.caption_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
            fila = 1

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(
            row=fila,
            column=0,
            sticky="nsew",
            padx=padding,
            pady=(12 if title else padding, padding),
        )
        self.grid_rowconfigure(fila, weight=1)
        self.body.grid_columnconfigure(0, weight=1)


class Badge(ctk.CTkLabel):
    """Etiqueta compacta para estados: 'Listo', 'En desarrollo', 'Error'."""

    TONES = {
        "info": ("bg_elevated", "accent"),
        "success": ("bg_elevated", "success"),
        "warning": ("bg_elevated", "warning"),
        "error": ("bg_elevated", "error"),
        "neutral": ("bg_elevated", "text_muted"),
    }

    def __init__(self, master, text: str, tone: str = "info", **kwargs) -> None:
        fondo, texto = self.TONES.get(tone, self.TONES["info"])
        super().__init__(
            master,
            text=text,
            font=font(role="tiny", weight="bold"),
            text_color=color(texto),
            fg_color=color(fondo),
            corner_radius=radius("pill"),
            padx=12,
            pady=4,
            **kwargs,
        )


class Divider(ctk.CTkFrame):
    """Linea separadora de 1 px."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, height=1, fg_color=color("border"), corner_radius=0, **kwargs)


class KeyValue(ctk.CTkFrame):
    """Par etiqueta/valor alineado, usado en los resumenes de resultados."""

    def __init__(self, master, label: str, value: str = "-", mono: bool = False, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text=label,
            font=font(role="small"),
            text_color=color("text_muted"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=font(role="small", weight="bold", mono=mono),
            text_color=color("text"),
            anchor="e",
        )
        self.value_label.grid(row=0, column=1, sticky="e", padx=(12, 0))

    def set_value(self, value: str) -> None:
        self.value_label.configure(text=value)
