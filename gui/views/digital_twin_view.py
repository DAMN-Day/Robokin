"""Pestana de gemelo digital (reservada)."""

from __future__ import annotations

from gui.views.base_view import PlaceholderView


class DigitalTwinView(PlaceholderView):
    TITLE = "Gemelo digital"
    SUBTITLE = "Visualizacion 3D y sincronizacion con el robot fisico"
    ROADMAP = [
        "Render 3D del manipulador a partir de las matrices T\u2070\u1d62",
        "Animacion de trayectorias y espacio de trabajo alcanzable",
        "Enlace con hardware por puerto serie o MQTT",
        "Registro de telemetria y comparacion modelo contra planta",
    ]
