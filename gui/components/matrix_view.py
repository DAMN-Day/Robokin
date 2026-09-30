"""
Widgets para mostrar matrices homogeneas.

`MatrixGrid`  -> rejilla 4x4 de valores numericos, con la columna de posicion
                 y la fila de escala diferenciadas por color.
`MatrixBlock` -> tarjeta con titulo que alterna entre valor numerico y
                 expresion simbolica.
`ResultsPanel`-> lista desplazable con el resumen y todas las matrices.
"""

from __future__ import annotations

from typing import List, Optional

import customtkinter as ctk
import numpy as np
import sympy as sp

from config.settings import DECIMALS
from core.kinematics import ForwardKinematicsResult
from gui.components.cards import Badge, KeyValue
from gui.theme import color, font, radius
from utils.formatting import matrix_rows, symbolic_to_text, vector_to_text


class MatrixGrid(ctk.CTkFrame):
    """Rejilla 4x4 con los valores de una matriz homogenea."""

    def __init__(self, master, matrix: np.ndarray, decimals: int = DECIMALS, **kwargs) -> None:
        super().__init__(
            master, fg_color=color("bg_matrix"), corner_radius=radius("widget"), **kwargs
        )
        for columna in range(4):
            self.grid_columnconfigure(columna, weight=1, uniform="matrix")

        for i, fila in enumerate(matrix_rows(matrix, decimals)):
            for j, valor in enumerate(fila):
                if i == 3:
                    tono = "text_faint"          # fila de perspectiva/escala
                elif j == 3:
                    tono = "accent"              # vector de posicion
                else:
                    tono = "text"                # submatriz de rotacion
                ctk.CTkLabel(
                    self,
                    text=valor,
                    font=font(role="small", mono=True),
                    text_color=color(tono),
                    anchor="e",
                ).grid(row=i, column=j, padx=8, pady=4, sticky="e")


class MatrixBlock(ctk.CTkFrame):
    """Tarjeta con una matriz en modo numerico o simbolico."""

    def __init__(
        self,
        master,
        title: str,
        caption: str = "",
        numeric: Optional[np.ndarray] = None,
        symbolic: Optional[sp.Matrix] = None,
        mode: str = "numeric",
        highlight: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=color("bg_card"),
            corner_radius=radius("card"),
            border_width=2 if highlight else 1,
            border_color=color("primary" if highlight else "border"),
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 0))
        encabezado.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            encabezado,
            text=title,
            font=font(role="body", weight="bold"),
            text_color=color("primary" if highlight else "text"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        if caption:
            ctk.CTkLabel(
                encabezado,
                text=caption,
                font=font(role="tiny"),
                text_color=color("text_muted"),
                anchor="w",
            ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.grid(row=1, column=0, sticky="nsew", padx=14, pady=(10, 14))
        contenido.grid_columnconfigure(0, weight=1)

        if mode == "symbolic" and symbolic is not None:
            texto = symbolic_to_text(symbolic)
            # +24 px para la barra de desplazamiento horizontal, que de otro
            # modo tapa la ultima fila de la matriz.
            lineas = texto.count("\n") + 1
            caja = ctk.CTkTextbox(
                contenido,
                height=min(300, max(110, lineas * 20 + 24)),
                wrap="none",
                fg_color=color("bg_matrix"),
                border_width=0,
                corner_radius=radius("widget"),
                text_color=color("text"),
                font=font(role="tiny", mono=True),
            )
            caja.grid(row=0, column=0, sticky="nsew")
            caja.insert("1.0", texto)
            caja.configure(state="disabled")
        elif numeric is not None:
            MatrixGrid(contenido, numeric).grid(row=0, column=0, sticky="ew")


class ResultsPanel(ctk.CTkScrollableFrame):
    """Panel desplazable con el resumen y todas las matrices calculadas."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._result: Optional[ForwardKinematicsResult] = None
        self._mode = "numeric"
        self.show_placeholder()

    # ------------------------------------------------------------------ #
    def _clear(self) -> None:
        for hijo in self.winfo_children():
            hijo.destroy()

    def show_placeholder(
        self,
        title: str = "Sin resultados todavia",
        message: str = (
            "Captura los parametros DH y presiona Calcular para obtener las "
            "matrices de transformacion."
        ),
    ) -> None:
        self._clear()
        marco = ctk.CTkFrame(
            self,
            fg_color=color("bg_card"),
            corner_radius=radius("card"),
            border_width=1,
            border_color=color("border"),
        )
        marco.grid(row=0, column=0, sticky="ew", pady=4)
        marco.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            marco,
            text=title,
            font=font(role="body", weight="bold"),
            text_color=color("text"),
        ).grid(row=0, column=0, padx=20, pady=(22, 4))
        ctk.CTkLabel(
            marco,
            text=message,
            font=font(role="small"),
            text_color=color("text_muted"),
            wraplength=320,
            justify="center",
        ).grid(row=1, column=0, padx=20, pady=(0, 24))

    def show_error(self, message: str) -> None:
        self._clear()
        marco = ctk.CTkFrame(
            self,
            fg_color=color("bg_card"),
            corner_radius=radius("card"),
            border_width=1,
            border_color=color("error"),
        )
        marco.grid(row=0, column=0, sticky="ew", pady=4)
        marco.grid_columnconfigure(0, weight=1)
        Badge(marco, "Revisa los datos", tone="error").grid(row=0, column=0, pady=(18, 8))
        ctk.CTkLabel(
            marco,
            text=message,
            font=font(role="small"),
            text_color=color("text"),
            wraplength=320,
            justify="left",
        ).grid(row=1, column=0, padx=20, pady=(0, 20))

    # ------------------------------------------------------------------ #
    def set_mode(self, mode: str) -> None:
        self._mode = "symbolic" if mode.lower().startswith("simb") else "numeric"
        if self._result is not None:
            self.show_results(self._result)

    def show_results(self, result: ForwardKinematicsResult) -> None:
        self._result = result
        self._clear()
        fila = 0

        fila = self._build_summary(result, fila)

        MatrixBlock(
            self,
            title=f"Matriz final  T\u2070\u2099  (0 \u2192 {result.dof})",
            caption="Pose del efector final respecto a la base",
            numeric=result.numeric_total,
            symbolic=result.symbolic_total,
            mode=self._mode,
            highlight=True,
        ).grid(row=fila, column=0, sticky="ew", pady=(4, 12))
        fila += 1

        fila = self._section_title("Matrices por eslabon  A\u1d62", fila)
        for i, (numerica, simbolica) in enumerate(
            zip(result.numeric_links, result.symbolic_links), start=1
        ):
            MatrixBlock(
                self,
                title=f"A{i}   ({i - 1} \u2192 {i})",
                caption=f"Transformacion del eslabon {i}",
                numeric=numerica,
                symbolic=simbolica,
                mode=self._mode,
            ).grid(row=fila, column=0, sticky="ew", pady=4)
            fila += 1

        fila = self._section_title("Transformaciones acumuladas  T\u2070\u1d62", fila)
        for i, (numerica, simbolica) in enumerate(
            zip(result.numeric_chain, result.symbolic_chain), start=1
        ):
            MatrixBlock(
                self,
                title=f"T\u2070{i}   (0 \u2192 {i})",
                caption=f"Sistema {i} respecto a la base",
                numeric=numerica,
                symbolic=simbolica,
                mode=self._mode,
            ).grid(row=fila, column=0, sticky="ew", pady=4)
            fila += 1

    # ------------------------------------------------------------------ #
    def _section_title(self, text: str, row: int) -> int:
        ctk.CTkLabel(
            self,
            text=text,
            font=font(role="small", weight="bold"),
            text_color=color("text_muted"),
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=(14, 6), padx=4)
        return row + 1

    def _build_summary(self, result: ForwardKinematicsResult, row: int) -> int:
        marco = ctk.CTkFrame(
            self,
            fg_color=color("bg_elevated"),
            corner_radius=radius("card"),
            border_width=1,
            border_color=color("border"),
        )
        marco.grid(row=row, column=0, sticky="ew", pady=(0, 4))
        marco.grid_columnconfigure(0, weight=1)

        cabecera = ctk.CTkFrame(marco, fg_color="transparent")
        cabecera.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        cabecera.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            cabecera,
            text="Pose del efector final",
            font=font(role="body", weight="bold"),
            text_color=color("text"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        Badge(
            cabecera,
            f"{result.elapsed_seconds * 1000:.0f} ms",
            tone="success",
        ).grid(row=0, column=1, sticky="e")

        detalles: List[tuple] = [
            ("Grados de libertad", str(result.dof)),
            ("Posicion (x, y, z)", vector_to_text(result.position)),
            ("Roll, Pitch, Yaw (\u00b0)", vector_to_text(result.rpy_degrees, decimals=2)),
            ("Alcance desde la base", f"{float(np.linalg.norm(result.position)):.4f}"),
            (
                "Variables articulares",
                ", ".join(str(s) for s in result.joint_symbols),
            ),
        ]
        for i, (etiqueta, valor) in enumerate(detalles):
            KeyValue(marco, etiqueta, valor, mono=True).grid(
                row=i + 1, column=0, sticky="ew", padx=16, pady=3
            )
        ctk.CTkFrame(marco, height=6, fg_color="transparent").grid(row=len(detalles) + 1, column=0)
        return row + 1
