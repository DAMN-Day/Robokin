"""
Widget de render 3D del simulador.

Usa `Figure` de Matplotlib directamente -no `pyplot`, que arrastra estado
global y puede chocar con el backend de Tk- embebida en un canvas de
Tkinter. Los artistas (lineas, marcadores, triedros) se crean una sola vez y
se actualizan con `set_data_3d` en cada cuadro: nunca se vuelve a llamar a
`ax.plot` durante la reproduccion, solo `canvas.draw_idle()`.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registra la proyeccion 3d)

from core.kinematics_fast import FastFrames
from core.robot import JointType, RobotModel
from gui.theme import color


class RenderWidget(ctk.CTkFrame):
    """Escena 3D del manipulador: esqueleto, triedros, piso y trazo del TCP."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color=color("bg_card"), **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._robot: Optional[RobotModel] = None
        self._triad_length = 0.1
        self._triads: List[Tuple] = []
        self._floor_lines: list = []

        self.fig = Figure(figsize=(6, 6), dpi=100, facecolor=color("bg_card"))
        self.ax = self.fig.add_subplot(111, projection="3d")
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self._skeleton = self.ax.plot(
            [], [], [], color=color("primary"), linewidth=2.5, solid_capstyle="round"
        )[0]
        self._prismatic_markers = self.ax.plot(
            [], [], [], linestyle="None", marker="s", markersize=7,
            markerfacecolor=color("warning"), markeredgecolor=color("warning"),
        )[0]
        self._trace = self.ax.plot(
            [], [], [], color=color("accent"), linewidth=1.5, alpha=0.85
        )[0]

    # ------------------------------------------------------------------ #
    def _style_axes(self) -> None:
        self.ax.set_facecolor(color("bg_card"))
        try:
            for eje in (self.ax.xaxis, self.ax.yaxis, self.ax.zaxis):
                eje.pane.set_facecolor(color("bg_matrix"))
                eje.pane.set_alpha(0.6)
                eje.line.set_color(color("border"))
        except AttributeError:  # cambia entre versiones de Matplotlib
            pass
        self.ax.tick_params(colors=color("text_faint"), labelsize=8)
        self.ax.grid(True, color=color("border"), linewidth=0.5)
        self.ax.set_xlabel("X", color=color("text_muted"))
        self.ax.set_ylabel("Y", color=color("text_muted"))
        self.ax.set_zlabel("Z", color=color("text_muted"))

    # ------------------------------------------------------------------ #
    def set_robot(self, robot: RobotModel) -> None:
        """Reconstruye un triedro por cada sistema de referencia (0..dof)."""
        self._robot = robot
        for lineas in self._triads:
            for linea in lineas:
                linea.remove()
        self._triads = []
        colores = (color("error"), color("success"), color("primary"))
        for _ in range(robot.dof + 1):
            lineas = tuple(
                self.ax.plot([], [], [], color=c, linewidth=1.2)[0] for c in colores
            )
            self._triads.append(lineas)

    def set_axis_limits(self, minimo: np.ndarray, maximo: np.ndarray) -> None:
        """Fija los limites de camara para toda la reproduccion (no saltan)."""
        self.ax.set_xlim(minimo[0], maximo[0])
        self.ax.set_ylim(minimo[1], maximo[1])
        self.ax.set_zlim(minimo[2], maximo[2])
        try:
            self.ax.set_box_aspect((1, 1, 1))
        except AttributeError:  # Matplotlib < 3.3
            pass
        self._triad_length = max((maximo - minimo).max() * 0.06, 1e-6)
        self._draw_floor(minimo, maximo)
        self.canvas.draw_idle()

    def _draw_floor(self, minimo: np.ndarray, maximo: np.ndarray, divisiones: int = 6) -> None:
        for linea in self._floor_lines:
            linea.remove()
        self._floor_lines = []
        z = minimo[2]
        for x in np.linspace(minimo[0], maximo[0], divisiones + 1):
            self._floor_lines.append(
                self.ax.plot([x, x], [minimo[1], maximo[1]], [z, z],
                              color=color("border"), linewidth=0.4)[0]
            )
        for y in np.linspace(minimo[1], maximo[1], divisiones + 1):
            self._floor_lines.append(
                self.ax.plot([minimo[0], maximo[0]], [y, y], [z, z],
                              color=color("border"), linewidth=0.4)[0]
            )

    # ------------------------------------------------------------------ #
    def render(self, frames: FastFrames) -> None:
        """Dibuja una configuracion concreta del robot (un cuadro)."""
        puntos = frames.skeleton_polyline()
        self._skeleton.set_data_3d(puntos[:, 0], puntos[:, 1], puntos[:, 2])

        if self._robot is not None:
            prismaticos = [
                frames.origins[i + 1]
                for i, joint in enumerate(self._robot.joints)
                if joint.joint_type is JointType.PRISMATIC
            ]
            if prismaticos:
                arreglo = np.array(prismaticos)
                self._prismatic_markers.set_data_3d(arreglo[:, 0], arreglo[:, 1], arreglo[:, 2])
            else:
                self._prismatic_markers.set_data_3d([], [], [])

        largo = self._triad_length
        for i, lineas in enumerate(self._triads):
            origen = frames.origins[i]
            rotacion = frames.rotations[i]
            for eje, linea in enumerate(lineas):
                punta = origen + largo * rotacion[:, eje]
                linea.set_data_3d([origen[0], punta[0]], [origen[1], punta[1]], [origen[2], punta[2]])

        self.canvas.draw_idle()

    def set_trace(self, puntos: Optional[np.ndarray]) -> None:
        if puntos is None or len(puntos) == 0:
            self._trace.set_data_3d([], [], [])
        else:
            self._trace.set_data_3d(puntos[:, 0], puntos[:, 1], puntos[:, 2])
        self.canvas.draw_idle()

    def close(self) -> None:
        """Libera la figura y el canvas al cerrar la ventana."""
        self.canvas.get_tk_widget().destroy()
        self.fig.clf()
