"""
Ventana del simulador.

Une el widget de render, el panel de controles y el animador. Se mantiene
una sola instancia: `open_simulation_window` la crea la primera vez y luego
solo la trae al frente y la actualiza con el robot mas reciente.
"""

from __future__ import annotations

from typing import List, Optional

import customtkinter as ctk
import numpy as np

from config.settings import APP_NAME
from core.kinematics_fast import FastFrameSequence, solve_fast_from_robot, solve_fast_sequence
from core.robot import RobotModel
from core.trajectory import linear_joint_space
from gui.simulation.animator import Animator
from gui.simulation.control_panel import ControlPanel, ControlPanelError
from gui.simulation.render_widget import RenderWidget
from gui.theme import color

FPS = 30
TRACE_HISTORY_LIMIT = 6  # trazos de simulaciones previas que se conservan como maximo


class SimulationWindow(ctk.CTkToplevel):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.title(f"{APP_NAME} \u2014 Simulacion")
        self.geometry("1180x720")
        self.minsize(900, 560)
        self.configure(fg_color=color("bg_app"))

        self._robot: Optional[RobotModel] = None
        self._trace_history: List[np.ndarray] = []

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self.render_widget = RenderWidget(self)
        self.render_widget.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)

        self.control_panel = ControlPanel(
            self, on_animate=self._on_animate, on_pause=self._on_pause, on_reset=self._on_reset,
        )
        self.control_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

        self.animator = Animator(self, on_frame=self._on_frame, on_finished=self._on_finished)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ #
    def show_for_robot(self, robot: RobotModel) -> None:
        self._robot = robot
        self.animator.stop()
        self._trace_history = []

        self.render_widget.set_robot(robot)
        self.control_panel.set_robot(robot)

        estatico = solve_fast_from_robot(robot)
        self._fit_axes_to(estatico.origins)
        self.render_widget.render(estatico)
        self.render_widget.set_trace(None)

        self.control_panel.set_rows_locked(False)
        self.control_panel.set_controls_state(
            animar_enabled=True, pausar_enabled=False, pausar_text="Pausar", reiniciar_enabled=False,
        )
        self.control_panel.set_status("Define los puntos y presiona Animar.", "info")

        self.deiconify()
        self.lift()
        self.focus_force()

    # ------------------------------------------------------------------ #
    def _fit_axes_to(self, origenes: np.ndarray) -> None:
        """Limites de camara cubicos a partir de origenes reales (un cuadro o
        toda una secuencia ya aplanada); no saltan porque se fijan una sola
        vez antes de reproducir."""
        puntos = origenes.reshape(-1, 3)
        minimo, maximo = puntos.min(axis=0), puntos.max(axis=0)
        centro = (minimo + maximo) / 2
        media = max((maximo - minimo).max() / 2, 0.1)
        margen = media * 0.2 + 0.1
        self.render_widget.set_axis_limits(centro - media - margen, centro + media + margen)

    # ------------------------------------------------------------------ #
    def _on_animate(self) -> None:
        if self._robot is None:
            return
        if self.animator.is_loaded and not self.animator.is_playing and not self.animator.is_finished:
            self.animator.play()  # reanuda una pausa o repite tras "Reiniciar"
            self._sync_controls()
            return

        try:
            waypoints, durations = self.control_panel.get_waypoints_and_durations()
        except ControlPanelError as error:
            self.control_panel.set_status(str(error), "error")
            return

        trayectoria = linear_joint_space(waypoints, durations)
        tiempos, valores = trayectoria.sample_uniform(FPS)
        secuencia = solve_fast_sequence(self._robot, valores, tiempos)

        if not self.control_panel.keep_trace_var.get():
            self._trace_history = []

        self._fit_axes_to(secuencia.origins)
        self.animator.load(secuencia)
        self.control_panel.set_rows_locked(True)
        self.animator.play()
        self._sync_controls()
        self.control_panel.set_status(
            f"Reproduciendo {trayectoria.total_duration:.1f} s ({secuencia.num_frames} cuadros).",
            "busy",
        )

    def _on_pause(self) -> None:
        if self.animator.is_playing:
            self.animator.pause()
        else:
            self.animator.play()
        self._sync_controls()

    def _on_reset(self) -> None:
        self.animator.reset()
        self.control_panel.set_rows_locked(False)
        self._sync_controls()
        self.control_panel.set_status("Reiniciado. Ajusta los puntos y presiona Animar.", "info")

    def _sync_controls(self) -> None:
        reproduciendo = self.animator.is_playing
        activo = self.animator.is_loaded and not self.animator.is_finished
        self.control_panel.set_controls_state(
            animar_enabled=not reproduciendo,
            pausar_enabled=activo,
            pausar_text="Pausar" if reproduciendo else "Reanudar",
            reiniciar_enabled=self.animator.is_loaded,
        )

    # ------------------------------------------------------------------ #
    def _on_frame(self, secuencia: FastFrameSequence, indice: int) -> None:
        self.render_widget.render(secuencia.frame(indice))
        trazo_actual = secuencia.end_effector_trace()[: indice + 1]
        if self._trace_history:
            trazo = np.concatenate(self._trace_history + [trazo_actual], axis=0)
        else:
            trazo = trazo_actual
        self.render_widget.set_trace(trazo)

    def _on_finished(self) -> None:
        secuencia = self.animator.sequence
        if self.control_panel.keep_trace_var.get() and secuencia is not None:
            self._trace_history.append(secuencia.end_effector_trace())
            if len(self._trace_history) > TRACE_HISTORY_LIMIT:
                self._trace_history.pop(0)
        self.control_panel.set_rows_locked(False)
        self._sync_controls()
        self.control_panel.set_status("Simulacion completa.", "ok")

    # ------------------------------------------------------------------ #
    def _on_close(self) -> None:
        self.animator.cancel()
        self.render_widget.close()
        self.destroy()
        global _instance
        _instance = None


_instance: Optional[SimulationWindow] = None


def open_simulation_window(master, robot: RobotModel) -> SimulationWindow:
    """Crea la ventana de simulacion o la reutiliza si ya esta abierta."""
    global _instance
    if _instance is None or not _instance.winfo_exists():
        _instance = SimulationWindow(master)
    _instance.show_for_robot(robot)
    return _instance
