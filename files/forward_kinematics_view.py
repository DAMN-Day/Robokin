"""
Pestana de cinematica directa (Denavit-Hartenberg).

Flujo:
  1. El usuario define el numero de articulaciones y su tipo.
  2. Captura los parametros DH en la tabla (las celdas se redimensionan solas).
  3. Presiona Calcular: la vista arma un `RobotModel` y llama al solver de
     `core.kinematics` en un hilo aparte para no congelar la interfaz.
  4. El resultado se dibuja en el panel derecho, en modo numerico o simbolico.
"""

from __future__ import annotations

import gc
import queue
import threading
from typing import Optional

import customtkinter as ctk

from config.settings import DEFAULT_JOINTS, MAX_JOINTS, MIN_JOINTS
from core import presets
from core.kinematics import ForwardKinematicsResult, ForwardKinematicsSolver
from core.robot import ModelError
from gui.components.cards import Card
from gui.components.dh_table import DHTable, TableValidationError
from gui.components.matrix_view import ResultsPanel
from gui.theme import color, font, radius
from gui.views.base_view import BaseView


class ForwardKinematicsView(BaseView):
    TITLE = "Cinematica directa"
    SUBTITLE = "Convencion de Denavit-Hartenberg estandar: A\u1d62 = Rot_z(\u03b8) \u00b7 Trans_z(d) \u00b7 Trans_x(a) \u00b7 Rot_x(\u03b1)"

    POLL_MS = 60  # frecuencia de sondeo del hilo de calculo

    def __init__(self, master, **kwargs) -> None:
        self._calculating = False
        self._last_result: Optional[ForwardKinematicsResult] = None
        self._queue: "queue.Queue[tuple]" = queue.Queue()
        super().__init__(master, **kwargs)

    # ------------------------------------------------------------------ #
    # Construccion
    # ------------------------------------------------------------------ #
    def build_body(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=5, uniform="fk")
        parent.grid_columnconfigure(1, weight=3, uniform="fk")
        parent.grid_rowconfigure(1, weight=1)

        self._build_config_card(parent)
        self._build_table_card(parent)
        self._build_results_card(parent)

        self.dh_table.set_joint_count(DEFAULT_JOINTS)

    # -- configuracion ---------------------------------------------------- #
    def _build_config_card(self, parent: ctk.CTkFrame) -> None:
        """Fila superior: cadena cinematica, opciones de calculo y acciones.

        El cuerpo se organiza en dos filas para que ningun control quede
        comprimido cuando la ventana esta en su ancho minimo.
        """
        tarjeta = Card(
            parent,
            title="Configuracion del robot",
            caption="Define la cadena cinematica antes de capturar los parametros.",
        )
        tarjeta.grid(row=0, column=0, sticky="ew", padx=(0, 14), pady=(0, 14))

        cuerpo = tarjeta.body
        cuerpo.grid_columnconfigure(0, minsize=150)
        cuerpo.grid_columnconfigure(1, minsize=200)
        cuerpo.grid_columnconfigure(2, weight=1)

        self._field_label(cuerpo, "Numero de articulaciones", row=0, column=0)
        self._field_label(cuerpo, "Cargar ejemplo", row=0, column=1, padx=(18, 0))

        # -- contador de articulaciones
        contador = ctk.CTkFrame(
            cuerpo, fg_color=color("bg_input"), corner_radius=radius("widget")
        )
        contador.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self._btn_menos = self._step_button(contador, "\u2212", -1)
        self._btn_menos.grid(row=0, column=0, padx=(4, 0), pady=4)

        self._joint_label = ctk.CTkLabel(
            contador,
            text=str(DEFAULT_JOINTS),
            width=44,
            font=font(size=16, weight="bold"),
            text_color=color("text"),
        )
        self._joint_label.grid(row=0, column=1)

        self._btn_mas = self._step_button(contador, "+", 1)
        self._btn_mas.grid(row=0, column=2, padx=(0, 4), pady=4)

        # -- configuraciones de ejemplo
        self._preset_menu = ctk.CTkOptionMenu(
            cuerpo,
            values=presets.preset_names(),
            width=186,
            height=40,
            corner_radius=radius("widget"),
            fg_color=color("bg_input"),
            button_color=color("secondary"),
            button_hover_color=color("secondary_hover"),
            text_color=color("text"),
            font=font(role="small"),
            command=self._load_preset,
        )
        self._preset_menu.set(presets.preset_names()[0])
        self._preset_menu.grid(row=1, column=1, sticky="w", padx=(18, 0), pady=(6, 0))

        # -- opciones de calculo y acciones (segunda fila)
        opciones = ctk.CTkFrame(cuerpo, fg_color="transparent")
        opciones.grid(row=2, column=0, columnspan=2, sticky="w", pady=(16, 0))

        self._var_simplify = ctk.BooleanVar(value=False)
        self._var_symbolic_lengths = ctk.BooleanVar(value=False)

        self._option_box(
            opciones, "Simplificar expresiones", self._var_simplify
        ).grid(row=0, column=0, sticky="w")
        self._option_box(
            opciones, "Longitudes simbolicas (a\u1d62, d\u1d62)", self._var_symbolic_lengths
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        acciones = ctk.CTkFrame(cuerpo, fg_color="transparent")
        acciones.grid(row=2, column=2, sticky="se", pady=(16, 0))

        self._btn_reset = ctk.CTkButton(
            acciones,
            text="Limpiar",
            width=96,
            height=40,
            corner_radius=radius("button"),
            fg_color=color("secondary"),
            hover_color=color("secondary_hover"),
            font=font(role="body"),
            command=self._reset,
        )
        self._btn_reset.grid(row=0, column=0, padx=(0, 10))

        self._btn_calcular = ctk.CTkButton(
            acciones,
            text="Calcular",
            width=150,
            height=40,
            corner_radius=radius("button"),
            fg_color=color("primary"),
            hover_color=color("primary_hover"),
            font=font(role="body", weight="bold"),
            command=self._calculate,
        )
        self._btn_calcular.grid(row=0, column=1)

        # -- linea de estado
        self._status = ctk.CTkLabel(
            cuerpo,
            text="Listo para capturar parametros.",
            font=font(role="small"),
            text_color=color("text_muted"),
            anchor="w",
        )
        self._status.grid(row=3, column=0, columnspan=3, sticky="w", pady=(14, 0))

    # -- fabricas de widgets ------------------------------------------------ #
    @staticmethod
    def _field_label(parent, texto: str, row: int, column: int, padx=(0, 0)) -> None:
        ctk.CTkLabel(
            parent,
            text=texto,
            font=font(role="small"),
            text_color=color("text_muted"),
            anchor="w",
        ).grid(row=row, column=column, sticky="w", padx=padx)

    def _step_button(self, parent, simbolo: str, delta: int) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=simbolo,
            width=34,
            height=32,
            corner_radius=radius("widget"),
            fg_color=color("secondary"),
            hover_color=color("secondary_hover"),
            font=font(size=16, weight="bold"),
            command=lambda: self._step_joints(delta),
        )

    @staticmethod
    def _option_box(parent, texto: str, variable) -> ctk.CTkCheckBox:
        return ctk.CTkCheckBox(
            parent,
            text=texto,
            variable=variable,
            font=font(role="small"),
            text_color=color("text_muted"),
            fg_color=color("primary"),
            hover_color=color("primary_hover"),
            border_color=color("border"),
            corner_radius=6,
            checkbox_width=18,
            checkbox_height=18,
        )

    # -- tabla ------------------------------------------------------------ #
    def _build_table_card(self, parent: ctk.CTkFrame) -> None:
        tarjeta = Card(
            parent,
            title="Parametros de Denavit-Hartenberg",
            caption=(
                "La variable articular se bloquea segun el tipo: en una revoluta "
                "\u03b8\u1d62 = q\u1d62; en una prismatica d\u1d62 = q\u1d62."
            ),
        )
        tarjeta.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        tarjeta.body.grid_rowconfigure(0, weight=1)

        self.dh_table = DHTable(tarjeta.body, on_change=self._on_table_changed)
        self.dh_table.grid(row=0, column=0, sticky="nsew")

    # -- resultados -------------------------------------------------------- #
    def _build_results_card(self, parent: ctk.CTkFrame) -> None:
        tarjeta = ctk.CTkFrame(
            parent,
            fg_color=color("bg_sidebar"),
            corner_radius=radius("panel"),
            border_width=1,
            border_color=color("border"),
        )
        tarjeta.grid(row=0, column=1, rowspan=2, sticky="nsew")
        tarjeta.grid_columnconfigure(0, weight=1)
        tarjeta.grid_rowconfigure(1, weight=1)

        encabezado = ctk.CTkFrame(tarjeta, fg_color="transparent")
        encabezado.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        encabezado.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            encabezado,
            text="Matrices de transformacion",
            font=font(role="title", weight="bold"),
            text_color=color("text"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._mode_switch = ctk.CTkSegmentedButton(
            encabezado,
            values=["Numerico", "Simbolico"],
            font=font(role="small"),
            corner_radius=radius("button"),
            fg_color=color("bg_input"),
            selected_color=color("primary"),
            selected_hover_color=color("primary_hover"),
            unselected_color=color("bg_input"),
            unselected_hover_color=color("secondary_hover"),
            text_color=color("text"),
            command=self._on_mode_changed,
        )
        self._mode_switch.set("Numerico")
        self._mode_switch.grid(row=1, column=0, sticky="w", pady=(10, 0))

        self.results = ResultsPanel(tarjeta)
        self.results.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 14))

    # ------------------------------------------------------------------ #
    # Interaccion
    # ------------------------------------------------------------------ #
    def _step_joints(self, delta: int) -> None:
        nuevo = max(MIN_JOINTS, min(MAX_JOINTS, self.dh_table.joint_count + delta))
        self.dh_table.set_joint_count(nuevo)
        self._joint_label.configure(text=str(nuevo))

    def _on_table_changed(self, count: int) -> None:
        """Sincroniza el contador del encabezado con el estado real de la tabla."""
        if hasattr(self, "_joint_label"):
            self._joint_label.configure(text=str(count))

    def _load_preset(self, nombre: str) -> None:
        modelo = presets.load_preset(nombre)
        self._preset_menu.set(nombre)  # mantiene el menu sincronizado
        self.dh_table.load_robot(modelo)
        self._joint_label.configure(text=str(modelo.dof))
        self._set_status(f"Configuracion '{nombre}' cargada. Presiona Calcular.", "info")

    def _reset(self) -> None:
        self.dh_table.reset()
        self._last_result = None
        self.results.show_placeholder()
        self._set_status("Tabla reiniciada.", "info")

    def _on_mode_changed(self, valor: str) -> None:
        self.results.set_mode(valor)

    def _set_status(self, mensaje: str, tono: str = "info") -> None:
        tonos = {"info": "text_muted", "ok": "success", "error": "error", "busy": "accent"}
        self._status.configure(text=mensaje, text_color=color(tonos.get(tono, "text_muted")))

    # ------------------------------------------------------------------ #
    # Calculo
    # ------------------------------------------------------------------ #
    def _calculate(self) -> None:
        if self._calculating:
            return

        self.dh_table.clear_highlights()
        try:
            robot = self.dh_table.get_robot(name="Robot capturado")
            robot.validate()
        except TableValidationError as error:
            self.dh_table.highlight_error(error.row, error.field)
            self._set_status(str(error), "error")
            self.results.show_error(str(error))
            return
        except ModelError as error:
            self._set_status(str(error), "error")
            self.results.show_error(str(error))
            return

        self._calculating = True
        self._btn_calcular.configure(state="disabled", text="Calculando...")
        self._set_status(f"Resolviendo {robot.summary()}", "busy")

        solver = ForwardKinematicsSolver(
            robot,
            symbolic_lengths=self._var_symbolic_lengths.get(),
            simplify=self._var_simplify.get(),
        )

        def tarea() -> None:
            """Se ejecuta fuera del hilo de la interfaz.

            Tkinter no es seguro entre hilos, asi que el worker solo deposita el
            resultado en la cola y el hilo principal lo recoge en `_poll_worker`.
            """
            try:
                self._queue.put(("ok", solver.solve()))
            except Exception as error:  # noqa: BLE001 - se reporta en la interfaz
                self._queue.put(("error", error))

        # Tkinter solo puede tocarse desde el hilo principal. Si el recolector
        # de basura corre dentro del hilo de calculo y libera un objeto de
        # Tkinter (por ejemplo una fuente de una fila borrada), su finalizador
        # llamaria a Tcl desde ese hilo y la aplicacion se bloquearia. Por eso
        # se vacia la basura pendiente aqui y se apaga el recolector mientras
        # dura el calculo; se reactiva en `_finish`.
        gc.collect()
        gc.disable()

        threading.Thread(target=tarea, daemon=True).start()
        self._poll_worker()

    def _poll_worker(self) -> None:
        """Revisa la cola de resultados sin bloquear la interfaz."""
        try:
            estado, carga = self._queue.get_nowait()
        except queue.Empty:
            if self._calculating:
                self.after(self.POLL_MS, self._poll_worker)
            return

        self._finish()
        if estado == "ok":
            self._on_success(carga)
        else:
            self._on_failure(carga)

    def _finish(self) -> None:
        """Restaura el estado de la interfaz al terminar un calculo."""
        self._calculating = False
        if not gc.isenabled():
            gc.enable()
        self._btn_calcular.configure(state="normal", text="Calcular")

    def _on_success(self, resultado: ForwardKinematicsResult) -> None:
        self._last_result = resultado
        self.results.set_mode(self._mode_switch.get())
        self.results.show_results(resultado)
        self._set_status(
            f"Calculo completado en {resultado.elapsed_seconds * 1000:.0f} ms "
            f"({resultado.dof} matrices de eslabon + matriz final).",
            "ok",
        )

    def _on_failure(self, error: Exception) -> None:
        mensaje = f"No se pudo completar el calculo: {error}"
        self._set_status(mensaje, "error")
        self.results.show_error(mensaje)
