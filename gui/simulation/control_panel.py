"""
Panel de controles del simulador.

Cada fila es un punto de la trayectoria (una configuracion articular
completa). La primera fila es "Inicio" y la ultima "Fin"; entre ambas se
pueden agregar puntos intermedios con "+ Agregar punto". Cada fila, salvo la
primera, tiene una duracion: el tiempo para llegar a ella desde la anterior.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import customtkinter as ctk

from core.robot import RobotModel
from gui.components.cards import Card
from gui.theme import color, font, radius

MIN_WAYPOINTS = 2
MAX_WAYPOINTS = 8
DEFAULT_DURATION = 1.5


class ControlPanelError(ValueError):
    """Error de captura con referencia a la fila responsable."""

    def __init__(self, message: str, row_index: int = 0) -> None:
        super().__init__(message)
        self.row_index = row_index


class ControlPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_animate: Callable[[], None],
        on_pause: Callable[[], None],
        on_reset: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_animate = on_animate
        self._on_pause = on_pause
        self._on_reset = on_reset

        self._robot: Optional[RobotModel] = None
        self._rows: List[Dict] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_rows_card()
        self._build_footer()

    # ------------------------------------------------------------------ #
    # Construccion
    # ------------------------------------------------------------------ #
    def _build_rows_card(self) -> None:
        tarjeta = Card(
            self,
            title="Puntos de la trayectoria",
            caption="Interpolacion lineal, en orden, entre puntos consecutivos.",
        )
        tarjeta.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        tarjeta.body.grid_rowconfigure(2, weight=1)

        barra = ctk.CTkFrame(tarjeta.body, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        barra.grid_columnconfigure(0, weight=1)
        self._add_button = ctk.CTkButton(
            barra, text="+ Agregar punto", width=140, height=30,
            corner_radius=radius("button"), fg_color=color("secondary"),
            hover_color=color("secondary_hover"), font=font(role="small"),
            command=self._add_waypoint,
        )
        self._add_button.grid(row=0, column=1, sticky="e")

        self._header_row = ctk.CTkFrame(tarjeta.body, fg_color="transparent")
        self._header_row.grid(row=1, column=0, sticky="ew")

        self._rows_container = ctk.CTkScrollableFrame(
            tarjeta.body, fg_color="transparent", height=240
        )
        self._rows_container.grid(row=2, column=0, sticky="nsew", pady=(4, 0))
        self._rows_container.grid_columnconfigure(0, weight=1)

    def _build_footer(self) -> None:
        tarjeta = Card(self, title="Reproduccion")
        tarjeta.grid(row=1, column=0, sticky="ew")
        tarjeta.body.grid_columnconfigure((0, 1, 2), weight=1)

        self.keep_trace_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            tarjeta.body, text="Conservar trazo entre simulaciones",
            variable=self.keep_trace_var, font=font(role="small"),
            text_color=color("text_muted"), fg_color=color("primary"),
            hover_color=color("primary_hover"), border_color=color("border"),
            checkbox_width=18, checkbox_height=18,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        self._btn_animar = ctk.CTkButton(
            tarjeta.body, text="Animar", height=38, corner_radius=radius("button"),
            fg_color=color("primary"), hover_color=color("primary_hover"),
            font=font(role="body", weight="bold"), command=self._on_animate,
        )
        self._btn_animar.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        self._btn_pausar = ctk.CTkButton(
            tarjeta.body, text="Pausar", height=38, corner_radius=radius("button"),
            fg_color=color("secondary"), hover_color=color("secondary_hover"),
            font=font(role="body"), state="disabled", command=self._on_pause,
        )
        self._btn_pausar.grid(row=1, column=1, sticky="ew", padx=6)

        self._btn_reiniciar = ctk.CTkButton(
            tarjeta.body, text="Reiniciar", height=38, corner_radius=radius("button"),
            fg_color=color("secondary"), hover_color=color("secondary_hover"),
            font=font(role="body"), state="disabled", command=self._on_reset,
        )
        self._btn_reiniciar.grid(row=1, column=2, sticky="ew", padx=(6, 0))

        self._status = ctk.CTkLabel(
            tarjeta.body, text="Define los puntos y presiona Animar.",
            font=font(role="small"), text_color=color("text_muted"), anchor="w",
        )
        self._status.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 0))

    # ------------------------------------------------------------------ #
    # Robot / columnas
    # ------------------------------------------------------------------ #
    def set_robot(self, robot: RobotModel) -> None:
        """Reconstruye columnas y filas para un robot (nuevo o releido de la tabla)."""
        self._robot = robot
        for widget in self._header_row.winfo_children():
            widget.destroy()
        self._build_column_headers()

        for fila in self._rows:
            fila["frame"].destroy()
        self._rows = []
        valores_actuales = [joint.q for joint in robot.joints]
        self._append_row("Inicio", valores_actuales, duration=None)
        self._append_row("Fin", list(valores_actuales), duration=DEFAULT_DURATION)

    def _build_column_headers(self) -> None:
        ctk.CTkLabel(self._header_row, text="", width=90).grid(row=0, column=0)
        for joint in self._robot.joints:
            unidad = "\u00b0" if joint.joint_type.is_revolute else "u"
            ctk.CTkLabel(
                self._header_row, text=f"q{joint.index} ({unidad})",
                font=font(role="tiny", weight="bold"), text_color=color("text_muted"),
            ).grid(row=0, column=joint.index, padx=4)
        ctk.CTkLabel(
            self._header_row, text="dur. (s)",
            font=font(role="tiny", weight="bold"), text_color=color("text_muted"),
        ).grid(row=0, column=len(self._robot.joints) + 1, padx=(10, 0))

    # ------------------------------------------------------------------ #
    # Filas
    # ------------------------------------------------------------------ #
    def _append_row(
        self, etiqueta: str, valores: List[float], duration: Optional[float],
        index: Optional[int] = None, removable: bool = False,
    ) -> Dict:
        contenedor = ctk.CTkFrame(
            self._rows_container, fg_color=color("bg_matrix"), corner_radius=radius("widget")
        )
        posicion = index if index is not None else len(self._rows)
        contenedor.grid(row=posicion, column=0, sticky="ew", pady=2)

        fila: Dict = {
            "frame": contenedor, "label_text": etiqueta, "entries": [],
            "duration_entry": None, "remove_button": None,
        }

        etiqueta_widget = ctk.CTkLabel(
            contenedor, text=etiqueta, width=80, font=font(role="small"),
            text_color=color("text"), anchor="w",
        )
        etiqueta_widget.grid(row=0, column=0, padx=4, pady=4)
        fila["label_widget"] = etiqueta_widget

        for i, valor in enumerate(valores):
            entrada = ctk.CTkEntry(
                contenedor, width=60, justify="center", fg_color=color("bg_input"),
                border_color=color("border"), border_width=1, corner_radius=radius("widget"),
                text_color=color("text"), font=font(role="small", mono=True),
            )
            entrada.insert(0, f"{valor:g}")
            entrada.grid(row=0, column=i + 1, padx=3, pady=4)
            fila["entries"].append(entrada)

        columna_duracion = len(valores) + 1
        if duration is not None:
            entrada_dur = ctk.CTkEntry(
                contenedor, width=54, justify="center", fg_color=color("bg_input"),
                border_color=color("border"), border_width=1, corner_radius=radius("widget"),
                text_color=color("text"), font=font(role="small", mono=True),
            )
            entrada_dur.insert(0, f"{duration:g}")
            entrada_dur.grid(row=0, column=columna_duracion, padx=(10, 3), pady=4)
            fila["duration_entry"] = entrada_dur
        else:
            ctk.CTkLabel(contenedor, text="\u2014", width=54, text_color=color("text_faint")).grid(
                row=0, column=columna_duracion, padx=(10, 3)
            )

        if removable:
            boton_quitar = ctk.CTkButton(
                contenedor, text="\u00d7", width=26, height=26, corner_radius=radius("widget"),
                fg_color="transparent", hover_color=color("bg_disabled"),
                text_color=color("text_faint"), font=font(size=14, weight="bold"),
                command=lambda f=fila: self._remove_row(f),
            )
            boton_quitar.grid(row=0, column=columna_duracion + 1, padx=(6, 4))
            fila["remove_button"] = boton_quitar

        if index is None:
            self._rows.append(fila)
        else:
            self._rows.insert(index, fila)
        return fila

    def _regrid_rows(self) -> None:
        for i, fila in enumerate(self._rows):
            fila["frame"].grid(row=i, column=0, sticky="ew", pady=2)

    def _add_waypoint(self) -> None:
        if self._robot is None or len(self._rows) >= MAX_WAYPOINTS:
            return
        anterior = self._rows[-2]  # el que sera el predecesor del nuevo punto
        valores = [self._parse(e.get(), 0.0) for e in anterior["entries"]]
        self._append_row(
            "Punto", valores, DEFAULT_DURATION, index=len(self._rows) - 1, removable=True
        )
        self._regrid_rows()
        self._relabel_rows()

    def _remove_row(self, fila: Dict) -> None:
        if fila not in self._rows or fila["remove_button"] is None:
            return
        fila["frame"].destroy()
        self._rows.remove(fila)
        self._regrid_rows()
        self._relabel_rows()

    def _relabel_rows(self) -> None:
        n = len(self._rows)
        for i, fila in enumerate(self._rows):
            if i == 0:
                texto = "Inicio"
            elif i == n - 1:
                texto = "Fin"
            else:
                texto = f"Punto {i + 1}"
            fila["label_text"] = texto
            fila["label_widget"].configure(text=texto)

    @staticmethod
    def _parse(texto: str, default: float) -> float:
        texto = texto.strip().replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            return default

    # ------------------------------------------------------------------ #
    # Lectura
    # ------------------------------------------------------------------ #
    def get_waypoints_and_durations(self):
        if not self._rows or self._robot is None:
            raise ControlPanelError("No hay una cadena cinematica cargada.")

        waypoints: List[List[float]] = []
        for row_index, fila in enumerate(self._rows):
            valores = []
            for col_index, entrada in enumerate(fila["entries"]):
                texto = entrada.get().strip().replace(",", ".")
                try:
                    valores.append(float(texto))
                except ValueError as exc:
                    raise ControlPanelError(
                        f"Valor invalido en '{fila['label_text']}', articulacion "
                        f"q{col_index + 1}: {texto!r}",
                        row_index=row_index,
                    ) from exc
            waypoints.append(valores)

        durations: List[float] = []
        for row_index, fila in enumerate(self._rows[1:], start=1):
            texto = fila["duration_entry"].get().strip().replace(",", ".")
            try:
                valor = float(texto)
            except ValueError as exc:
                raise ControlPanelError(
                    f"Duracion invalida en '{fila['label_text']}': {texto!r}", row_index=row_index
                ) from exc
            if valor <= 0:
                raise ControlPanelError(
                    f"La duracion en '{fila['label_text']}' debe ser mayor que cero.",
                    row_index=row_index,
                )
            durations.append(valor)

        return waypoints, durations

    # ------------------------------------------------------------------ #
    # Estado de la interfaz
    # ------------------------------------------------------------------ #
    def set_controls_state(
        self, animar_enabled: bool, pausar_enabled: bool, pausar_text: str, reiniciar_enabled: bool
    ) -> None:
        self._btn_animar.configure(state="normal" if animar_enabled else "disabled")
        self._btn_pausar.configure(
            state="normal" if pausar_enabled else "disabled", text=pausar_text
        )
        self._btn_reiniciar.configure(state="normal" if reiniciar_enabled else "disabled")

    def set_rows_locked(self, locked: bool) -> None:
        estado = "disabled" if locked else "normal"
        self._add_button.configure(state=estado)
        for fila in self._rows:
            for entrada in fila["entries"]:
                entrada.configure(state=estado)
            if fila["duration_entry"] is not None:
                fila["duration_entry"].configure(state=estado)
            if fila["remove_button"] is not None:
                fila["remove_button"].configure(state=estado)

    def set_status(self, mensaje: str, tono: str = "info") -> None:
        tonos = {"info": "text_muted", "ok": "success", "error": "error", "busy": "accent"}
        self._status.configure(text=mensaje, text_color=color(tonos.get(tono, "text_muted")))
