"""Pestana de cinematica inversa (reservada)."""

from __future__ import annotations

from gui.views.base_view import PlaceholderView


class InverseKinematicsView(PlaceholderView):
    TITLE = "Cinematica inversa"
    SUBTITLE = "Obtener las variables articulares a partir de una pose deseada"
    ROADMAP = [
        "Solucion geometrica y algebraica para cadenas de 2 y 3 GDL",
        "Metodo numerico iterativo basado en la jacobiana (Newton-Raphson)",
        "Deteccion de multiples configuraciones: codo arriba / codo abajo",
        "Verificacion de alcanzabilidad y limites articulares",
    ]
