"""
Generador de trayectorias en el espacio articular.

La animacion solo consume una `JointSpaceTrajectory` a traves de `.sample()`
o `.sample_uniform()`: no le importa si vino de una interpolacion lineal
simple o, mas adelante, de un perfil trapezoidal u otro metodo que aporte la
pestana de planeacion de trayectoria.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np


@dataclass
class JointSpaceTrajectory:
    """Secuencia de configuraciones articulares con tiempos de paso.

    `waypoints[0]` es el punto de partida; `durations[i]` es el tiempo, en
    segundos, para ir de `waypoints[i]` a `waypoints[i + 1]`. Admite dos
    puntos (inicio/fin) o una lista mas larga de configuraciones consecutivas.
    """

    waypoints: List[np.ndarray]
    durations: List[float]

    def __post_init__(self) -> None:
        if len(self.waypoints) < 2:
            raise ValueError("Se necesitan al menos dos configuraciones (inicio y fin).")
        if len(self.durations) != len(self.waypoints) - 1:
            raise ValueError("Debe haber una duracion por cada tramo entre puntos.")
        if any(duracion <= 0 for duracion in self.durations):
            raise ValueError("Las duraciones deben ser mayores que cero.")
        n = len(self.waypoints[0])
        if any(len(p) != n for p in self.waypoints):
            raise ValueError("Todas las configuraciones deben tener el mismo numero de articulaciones.")

    @property
    def dof(self) -> int:
        return len(self.waypoints[0])

    @property
    def total_duration(self) -> float:
        return float(sum(self.durations))

    @property
    def cumulative_times(self) -> np.ndarray:
        """Tiempo acumulado al llegar a cada waypoint: [0, d0, d0+d1, ...]."""
        return np.concatenate(([0.0], np.cumsum(self.durations)))

    def sample(self, t: float) -> np.ndarray:
        """Configuracion articular interpolada linealmente en el tiempo `t`."""
        limites = self.cumulative_times
        t = max(0.0, min(t, limites[-1]))
        segmento = int(np.searchsorted(limites, t, side="right") - 1)
        segmento = max(0, min(segmento, len(self.durations) - 1))

        t0, t1 = limites[segmento], limites[segmento + 1]
        proporcion = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
        q0, q1 = self.waypoints[segmento], self.waypoints[segmento + 1]
        return q0 + proporcion * (q1 - q0)

    def sample_uniform(self, fps: int) -> Tuple[np.ndarray, np.ndarray]:
        """Precalcula toda la trayectoria a una tasa de cuadros fija.

        Devuelve `(tiempos, valores)` con `valores.shape == (num_cuadros, dof)`.
        El ultimo cuadro cae exactamente en `total_duration`.
        """
        num_cuadros = max(2, int(round(self.total_duration * fps)) + 1)
        tiempos = np.linspace(0.0, self.total_duration, num_cuadros)
        valores = np.array([self.sample(t) for t in tiempos])
        return tiempos, valores


def linear_joint_space(
    waypoints: Sequence[Sequence[float]], durations: Sequence[float]
) -> JointSpaceTrajectory:
    """Atajo funcional: interpolacion lineal entre configuraciones articulares.

    Es el primer perfil de velocidad; la pestana de planeacion de trayectoria
    podra aportar otros (trapezoidal, polinomial) que produzcan el mismo tipo
    `JointSpaceTrajectory` sin que la animacion tenga que cambiar.
    """
    return JointSpaceTrajectory(
        waypoints=[np.asarray(p, dtype=float) for p in waypoints],
        durations=[float(d) for d in durations],
    )
