"""
Cinematica directa numerica rapida, sin SymPy.

`ForwardKinematicsSolver` (en `core/kinematics.py`) arma en cada llamada una
version simbolica completa -crea simbolos, matrices simbolicas y aplica
`nsimplify`/`trigsimp`- incluso cuando solo se necesita la posicion numerica.
Eso lo hace demasiado lento para animar a 30 cuadros por segundo.

Este modulo solo mueve arreglos de NumPy y reutiliza `dh.dh_matrix_numeric`,
que ya es puramente numerico. Se evalua una vez por cuadro de animacion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from core import dh
from core.robot import JointType, RobotModel


@dataclass
class FastFrames:
    """Marcos de referencia de una configuracion articular concreta.

    `origins[0]` es la base (O_0); `origins[i]` es el origen del sistema i.
    `kinks[i]` es el punto intermedio del eslabon i-esimo -tras Trans_z(d_i),
    antes de Trans_x(a_i)-, necesario para dibujar el eslabon como dos tramos
    en vez de una linea recta entre origenes (ver `skeleton_polyline`).
    `rotations[i]` es la matriz de rotacion 3x3 del sistema i, para triedros.
    """

    origins: np.ndarray     # (n+1, 3)
    kinks: np.ndarray       # (n, 3)
    rotations: np.ndarray   # (n+1, 3, 3)

    @property
    def dof(self) -> int:
        return self.kinks.shape[0]

    @property
    def position(self) -> np.ndarray:
        return self.origins[-1]

    def skeleton_polyline(self) -> np.ndarray:
        """Puntos, en orden, para dibujar el robot con una sola polilinea:

            O_0, m_1, O_1, m_2, O_2, ..., m_n, O_n
        """
        puntos = [self.origins[0]]
        for i in range(self.dof):
            puntos.append(self.kinks[i])
            puntos.append(self.origins[i + 1])
        return np.array(puntos)


def solve_fast(robot: RobotModel, q: Sequence[float]) -> FastFrames:
    """Cinematica directa numerica pura para un vector de variables articulares.

    Args:
        robot: modelo ya validado (no se vuelve a validar aqui: esta funcion
            se llama muchas veces por segundo durante la animacion).
        q: valores de la variable articular de cada eslabon, en el mismo
            orden que `robot.joints`. Unidades igual que `Joint.q`: grados en
            revolutas, longitud en prismaticas.
    """
    n = robot.dof
    if len(q) != n:
        raise ValueError(f"Se esperaban {n} valores articulares, llegaron {len(q)}.")

    T = np.eye(4)
    origins = [T[:3, 3].copy()]
    rotations = [T[:3, :3].copy()]
    kinks = np.zeros((n, 3))

    for i, joint in enumerate(robot.joints):
        if joint.joint_type is JointType.REVOLUTE:
            theta = np.radians(q[i])
            d = joint.dh.d
        else:
            theta = np.radians(joint.dh.theta)
            d = q[i]
        a = joint.dh.a
        alpha = np.radians(joint.dh.alpha)

        # Rot_z(theta) no mueve el origen ni cambia la direccion de z, asi
        # que Trans_z(d) siempre corre a lo largo del eje z del marco previo:
        # ese es el punto de "quiebre" del eslabon.
        kinks[i] = T[:3, 3] + d * T[:3, 2]

        T = T @ dh.dh_matrix_numeric(theta, d, a, alpha)
        origins.append(T[:3, 3].copy())
        rotations.append(T[:3, :3].copy())

    return FastFrames(
        origins=np.array(origins), kinks=kinks, rotations=np.array(rotations)
    )


def solve_fast_from_robot(robot: RobotModel) -> FastFrames:
    """Atajo: usa los valores `q` que ya trae cada articulacion del modelo."""
    return solve_fast(robot, [joint.q for joint in robot.joints])


@dataclass
class FastFrameSequence:
    """Todos los cuadros de una animacion, ya calculados y apilados."""

    times: np.ndarray       # (num_frames,) segundos
    origins: np.ndarray     # (num_frames, n+1, 3)
    kinks: np.ndarray       # (num_frames, n, 3)
    rotations: np.ndarray   # (num_frames, n+1, 3, 3)

    @property
    def num_frames(self) -> int:
        return self.times.shape[0]

    @property
    def dof(self) -> int:
        return self.kinks.shape[1]

    def frame(self, index: int) -> FastFrames:
        return FastFrames(
            origins=self.origins[index],
            kinks=self.kinks[index],
            rotations=self.rotations[index],
        )

    def end_effector_trace(self) -> np.ndarray:
        """Posicion del efector final en todos los cuadros: (num_frames, 3)."""
        return self.origins[:, -1, :]


def solve_fast_sequence(
    robot: RobotModel, q_sequence: np.ndarray, times: np.ndarray
) -> FastFrameSequence:
    """Corre `solve_fast` sobre cada fila de `q_sequence` y apila el resultado.

    Se usa una sola vez, antes de reproducir la animacion: el animador solo
    consume el resultado, nunca vuelve a llamar al solver cuadro por cuadro.
    """
    cuadros = [solve_fast(robot, fila) for fila in q_sequence]
    return FastFrameSequence(
        times=np.asarray(times, dtype=float),
        origins=np.array([c.origins for c in cuadros]),
        kinks=np.array([c.kinks for c in cuadros]),
        rotations=np.array([c.rotations for c in cuadros]),
    )
