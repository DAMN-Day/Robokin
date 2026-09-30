"""Pestana de planeacion de trayectoria (reservada)."""

from __future__ import annotations

from gui.views.base_view import PlaceholderView


class TrajectoryPlanningView(PlaceholderView):
    TITLE = "Planeacion de trayectoria"
    SUBTITLE = "Perfiles de movimiento en espacio articular y cartesiano"
    ROADMAP = [
        "Interpolacion polinomial de 3er y 5to orden entre puntos",
        "Perfil trapezoidal de velocidad con limites de aceleracion",
        "Trayectorias cartesianas: segmentos rectos y arcos",
        "Graficas de posicion, velocidad y aceleracion por articulacion",
    ]
