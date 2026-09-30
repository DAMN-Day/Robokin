"""
Tabla editable de parametros Denavit-Hartenberg.

Se reconstruye al cambiar el numero de articulaciones y ajusta el tamano de las
celdas (alto, ancho y tipografia) segun cuantas filas haya, de modo que un
robot de 2 GDL se vea comodo y uno de 10 GDL siga cabiendo en pantalla.

La columna variable se bloquea automaticamente segun el tipo de articulacion:
  * Revoluta  -> theta_i es la variable (se muestra q_i) y d_i es constante.
  * Prismatica -> d_i es la variable (se muestra q_i) y theta_i es constante.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import customtkinter as ctk

from config.settings import MAX_JOINTS, MIN_JOINTS
from core.robot import DHParameters, Joint, JointType, RobotModel
from gui.theme import color, font, radius


class TableValidationError(ValueError):
    """Error de captura con referencia a la celda responsable."""

    def __init__(self, message: str, row: int = 0, field: str = "") -> None:
        super().__init__(message)
        self.row = row
        self.field = field


class DHTable(ctk.CTkFrame):
    """Rejilla editable de parametros DH."""

    COLUMNS = [
        ("index", "Art."),
        ("type", "Tipo"),
        ("theta", "\u03b8\u1d62 (\u00b0)"),
        ("d", "d\u1d62"),
        ("a", "a\u1d62 (eslabon)"),
        ("alpha", "\u03b1\u1d62 (\u00b0)"),
        ("q", "q\u1d62 (\u00b0 / u)"),
    ]
    NUMERIC_FIELDS = ("theta", "d", "a", "alpha", "q")
    COLUMN_WEIGHTS = {"index": 0, "type": 3, "theta": 2, "d": 2, "a": 2, "alpha": 2, "q": 2}
    COLUMN_MINSIZE = {"index": 46, "type": 116, "theta": 66, "d": 66, "a": 66, "alpha": 66, "q": 66}

    def __init__(self, master, on_change: Optional[Callable[[int], None]] = None, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_change = on_change
        self._rows: List[Dict] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._header = ctk.CTkFrame(
            self, fg_color=color("bg_elevated"), corner_radius=radius("widget")
        )
        self._header.grid(row=0, column=0, sticky="ew")

        self._body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._body.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        self._build_header()
        self.set_joint_count(MIN_JOINTS)

    # ------------------------------------------------------------------ #
    # Construccion
    # ------------------------------------------------------------------ #
    def _configure_columns(self, contenedor) -> None:
        for indice, (clave, _) in enumerate(self.COLUMNS):
            contenedor.grid_columnconfigure(
                indice,
                weight=self.COLUMN_WEIGHTS[clave],
                minsize=self.COLUMN_MINSIZE[clave],
            )

    def _build_header(self) -> None:
        self._configure_columns(self._header)
        self._header_labels = []
        for indice, (_, etiqueta) in enumerate(self.COLUMNS):
            label = ctk.CTkLabel(
                self._header,
                text=etiqueta,
                font=font(role="small", weight="bold"),
                text_color=color("text_muted"),
            )
            label.grid(row=0, column=indice, padx=4, pady=9, sticky="ew")
            self._header_labels.append(label)

    def _make_entry(self, parent, valor: str) -> ctk.CTkEntry:
        entry = ctk.CTkEntry(
            parent,
            justify="center",
            fg_color=color("bg_input"),
            border_color=color("border"),
            border_width=1,
            corner_radius=radius("widget"),
            text_color=color("text"),
            font=font(role="small", mono=True),
        )
        entry.insert(0, valor)
        entry.bind("<FocusIn>", lambda e, w=entry: w.configure(border_color=color("border_focus")))
        entry.bind("<FocusOut>", lambda e, w=entry: w.configure(border_color=color("border")))
        return entry

    def _create_row(self, indice: int) -> Dict:
        contenedor = ctk.CTkFrame(
            self._body,
            fg_color=color("bg_card") if indice % 2 else color("bg_matrix"),
            corner_radius=radius("widget"),
        )
        contenedor.grid(row=indice - 1, column=0, sticky="ew", pady=3)
        self._body.grid_columnconfigure(0, weight=1)
        self._configure_columns(contenedor)

        fila: Dict = {"index": indice, "frame": contenedor, "entries": {}, "cache": {}}

        ctk.CTkLabel(
            contenedor,
            text=str(indice),
            font=font(role="small", weight="bold"),
            text_color=color("accent"),
        ).grid(row=0, column=0, padx=4, pady=6)

        selector = ctk.CTkOptionMenu(
            contenedor,
            values=[JointType.REVOLUTE.value, JointType.PRISMATIC.value],
            fg_color=color("secondary"),
            button_color=color("secondary"),
            button_hover_color=color("secondary_hover"),
            text_color=color("text"),
            corner_radius=radius("widget"),
            font=font(role="small"),
            command=lambda _v, r=fila: self._on_type_changed(r),
        )
        selector.set(JointType.REVOLUTE.value)
        selector.grid(row=0, column=1, padx=4, pady=6, sticky="ew")
        fila["type"] = selector

        for columna, (clave, _) in enumerate(self.COLUMNS):
            if clave in ("index", "type"):
                continue
            entry = self._make_entry(contenedor, "0")
            entry.grid(row=0, column=columna, padx=4, pady=6, sticky="ew")
            entry.bind("<KeyRelease>", lambda _e: self._notify())
            fila["entries"][clave] = entry

        self._apply_variable_lock(fila)
        return fila

    # ------------------------------------------------------------------ #
    # Tamano adaptativo de celdas
    # ------------------------------------------------------------------ #
    def _cell_metrics(self, n: int) -> Dict[str, int]:
        """Alto, ancho y tipografia en funcion del numero de articulaciones."""
        alto = max(26, 40 - 2 * max(0, n - 3))
        ancho = max(58, 98 - 4 * max(0, n - 3))
        tamano = 13 if n <= 5 else (12 if n <= 8 else 11)
        return {"height": alto, "width": ancho, "font_size": tamano}

    def _apply_cell_metrics(self) -> None:
        metricas = self._cell_metrics(len(self._rows))
        fuente = font(size=metricas["font_size"], mono=True)
        fuente_ui = font(size=metricas["font_size"])
        for etiqueta in self._header_labels:
            etiqueta.configure(font=font(size=metricas["font_size"], weight="bold"))
        for fila in self._rows:
            fila["type"].configure(
                height=metricas["height"],
                width=metricas["width"] + 40,
                font=fuente_ui,
            )
            for entry in fila["entries"].values():
                entry.configure(
                    height=metricas["height"], width=metricas["width"], font=fuente
                )

    # ------------------------------------------------------------------ #
    # Bloqueo de la variable articular
    # ------------------------------------------------------------------ #
    @staticmethod
    def _set_entry(entry: ctk.CTkEntry, texto: str, bloqueado: bool) -> None:
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, texto)
        if bloqueado:
            entry.configure(
                state="disabled",
                fg_color=color("bg_disabled"),
                text_color=color("text_faint"),
            )
        else:
            entry.configure(fg_color=color("bg_input"), text_color=color("text"))

    def _apply_variable_lock(self, fila: Dict) -> None:
        """Bloquea theta o d segun el tipo y coloca el simbolo q_i."""
        tipo = JointType.from_label(fila["type"].get())
        simbolo = f"q{fila['index']}"
        bloqueada = "theta" if tipo.is_revolute else "d"
        libre = "d" if tipo.is_revolute else "theta"

        entrada_bloqueada = fila["entries"][bloqueada]
        entrada_libre = fila["entries"][libre]

        texto_actual = entrada_bloqueada.get()
        if not texto_actual.startswith("q"):
            fila["cache"][bloqueada] = texto_actual
        self._set_entry(entrada_bloqueada, simbolo, bloqueado=True)

        if entrada_libre.cget("state") == "disabled" or entrada_libre.get().startswith("q"):
            self._set_entry(entrada_libre, fila["cache"].get(libre, "0"), bloqueado=False)

    def _on_type_changed(self, fila: Dict) -> None:
        self._apply_variable_lock(fila)
        self._notify()

    def _notify(self) -> None:
        """Avisa a la vista contenedora del cambio, enviando el numero de filas."""
        if self._on_change:
            self._on_change(len(self._rows))

    # ------------------------------------------------------------------ #
    # API publica
    # ------------------------------------------------------------------ #
    def set_joint_count(self, n: int) -> None:
        """Ajusta la tabla a `n` articulaciones conservando lo ya capturado."""
        n = max(MIN_JOINTS, min(MAX_JOINTS, int(n)))
        while len(self._rows) > n:
            self._rows.pop()["frame"].destroy()
        while len(self._rows) < n:
            self._rows.append(self._create_row(len(self._rows) + 1))
        self._apply_cell_metrics()
        self._notify()

    @property
    def joint_count(self) -> int:
        return len(self._rows)

    def get_robot(self, name: str = "Manipulador") -> RobotModel:
        """Lee la tabla y devuelve un modelo validado.

        Raises:
            TableValidationError: si alguna celda no contiene un numero.
        """
        articulaciones: List[Joint] = []
        for fila in self._rows:
            indice = fila["index"]
            tipo = JointType.from_label(fila["type"].get())
            valores = {}
            for clave in self.NUMERIC_FIELDS:
                entrada = fila["entries"][clave]
                texto = entrada.get().strip().replace(",", ".")
                if texto.startswith("q"):  # celda bloqueada: es la variable
                    valores[clave] = 0.0
                    continue
                if not texto:
                    valores[clave] = 0.0
                    continue
                try:
                    valores[clave] = float(texto)
                except ValueError as exc:
                    raise TableValidationError(
                        f"Valor invalido en la articulacion {indice}, columna "
                        f"'{dict(self.COLUMNS)[clave]}': {texto!r}",
                        row=indice,
                        field=clave,
                    ) from exc

            parametros = DHParameters(
                theta=valores["theta"],
                d=valores["d"],
                a=valores["a"],
                alpha=valores["alpha"],
            )
            articulaciones.append(Joint(indice, tipo, parametros, valores["q"]))

        return RobotModel(joints=articulaciones, name=name)

    def load_robot(self, robot: RobotModel) -> None:
        """Carga un modelo existente (por ejemplo, una configuracion de ejemplo)."""
        self.set_joint_count(robot.dof)
        for fila, articulacion in zip(self._rows, robot.joints):
            fila["type"].set(articulacion.joint_type.value)
            fila["cache"] = {
                "theta": f"{articulacion.dh.theta:g}",
                "d": f"{articulacion.dh.d:g}",
            }
            for clave, valor in (
                ("theta", articulacion.dh.theta),
                ("d", articulacion.dh.d),
                ("a", articulacion.dh.a),
                ("alpha", articulacion.dh.alpha),
                ("q", articulacion.q),
            ):
                self._set_entry(fila["entries"][clave], f"{valor:g}", bloqueado=False)
            self._apply_variable_lock(fila)
        self._apply_cell_metrics()
        self._notify()

    def highlight_error(self, row: int, field: str) -> None:
        """Marca en rojo la celda con el dato invalido."""
        for fila in self._rows:
            if fila["index"] != row:
                continue
            entrada = fila["entries"].get(field)
            if entrada is not None:
                entrada.configure(border_color=color("error"), border_width=2)
                entrada.focus_set()

    def clear_highlights(self) -> None:
        for fila in self._rows:
            for entrada in fila["entries"].values():
                entrada.configure(border_color=color("border"), border_width=1)

    def reset(self) -> None:
        for fila in self._rows:
            fila["type"].set(JointType.REVOLUTE.value)
            fila["cache"] = {}
            for clave in self.NUMERIC_FIELDS:
                self._set_entry(fila["entries"][clave], "0", bloqueado=False)
            self._apply_variable_lock(fila)
        self.clear_highlights()
        self._notify()
