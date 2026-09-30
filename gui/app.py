"""
Ventana principal.

Mantiene el registro de vistas y el enrutamiento entre pestanas. Las vistas se
instancian de forma perezosa (solo al abrirlas por primera vez) y despues se
conservan en cache, de modo que el trabajo capturado no se pierde al navegar.

Para agregar una pestana nueva:
    1. Crear la vista en `gui/views/`.
    2. Registrarla en `VIEW_REGISTRY`.
    3. Anadir su clave a `NAV_ITEMS` en `config/settings.py`.
"""

from __future__ import annotations

from typing import Dict, Type

import customtkinter as ctk

from config.settings import APP_NAME, MIN_WINDOW_SIZE, NAV_ITEMS, WINDOW_SIZE
from core.warmup import warm_up_symbolic_engine
from gui import theme
from gui.sidebar import Sidebar
from gui.theme import color
from gui.views.base_view import BaseView
from gui.views.digital_twin_view import DigitalTwinView
from gui.views.forward_kinematics_view import ForwardKinematicsView
from gui.views.inverse_kinematics_view import InverseKinematicsView
from gui.views.trajectory_view import TrajectoryPlanningView

VIEW_REGISTRY: Dict[str, Type[BaseView]] = {
    "forward": ForwardKinematicsView,
    "inverse": InverseKinematicsView,
    "trajectory": TrajectoryPlanningView,
    "twin": DigitalTwinView,
}


class RoboKinApp(ctk.CTk):
    """Contenedor de la aplicacion: barra lateral + area de contenido."""

    def __init__(self) -> None:
        theme.initialize()
        super().__init__(fg_color=color("bg_app"))

        self.title(APP_NAME)
        self.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
        self.minsize(*MIN_WINDOW_SIZE)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._views: Dict[str, BaseView] = {}
        self._current: str = ""

        self.sidebar = Sidebar(self, on_select=self.show_view)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.content = ctk.CTkFrame(self, fg_color=color("bg_app"), corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.show_view(NAV_ITEMS[0][0])

        # Carga SymPy por completo en el hilo principal antes de que exista
        # cualquier hilo de calculo (ver core/warmup.py).
        self.after(120, warm_up_symbolic_engine)

    # ------------------------------------------------------------------ #
    def show_view(self, key: str) -> None:
        """Muestra la pestana `key`, creandola si es la primera vez."""
        if key not in VIEW_REGISTRY or key == self._current:
            self.sidebar.set_active(key)
            return

        if self._current:
            self._views[self._current].grid_forget()

        if key not in self._views:
            self._views[key] = VIEW_REGISTRY[key](self.content)

        vista = self._views[key]
        vista.grid(row=0, column=0, sticky="nsew")
        vista.on_show()

        self._current = key
        self.sidebar.set_active(key)
