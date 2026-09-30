"""
Matrices de transformacion homogenea de Denavit-Hartenberg.

Se implementan dos versiones de la misma matriz: una numerica (numpy) y otra
simbolica (sympy), para poder mostrar tanto la expresion algebraica como el
valor evaluado en la interfaz.

Convencion estandar (Denavit-Hartenberg clasico):

    A_i = Rot_z(theta) * Trans_z(d) * Trans_x(a) * Rot_x(alpha)

        [ c(th)  -s(th)c(al)   s(th)s(al)   a*c(th) ]
        [ s(th)   c(th)c(al)  -c(th)s(al)   a*s(th) ]
        [   0       s(al)        c(al)         d    ]
        [   0         0            0           1    ]
"""

from __future__ import annotations

from typing import Iterable, List, Sequence

import numpy as np
import sympy as sp


# --------------------------------------------------------------------------- #
# Version numerica
# --------------------------------------------------------------------------- #
def dh_matrix_numeric(theta: float, d: float, a: float, alpha: float) -> np.ndarray:
    """Matriz homogenea 4x4. Los angulos se reciben en radianes."""
    ct, st = np.cos(theta), np.sin(theta)
    ca, sa = np.cos(alpha), np.sin(alpha)
    return np.array(
        [
            [ct, -st * ca, st * sa, a * ct],
            [st, ct * ca, -ct * sa, a * st],
            [0.0, sa, ca, d],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def compose_numeric(matrices: Iterable[np.ndarray]) -> np.ndarray:
    """Producto acumulado de una lista de matrices homogeneas."""
    total = np.eye(4)
    for matrix in matrices:
        total = total @ matrix
    return total


def accumulate_numeric(matrices: Sequence[np.ndarray]) -> List[np.ndarray]:
    """Devuelve [T_0_1, T_0_2, ..., T_0_n]."""
    acumuladas: List[np.ndarray] = []
    total = np.eye(4)
    for matrix in matrices:
        total = total @ matrix
        acumuladas.append(total.copy())
    return acumuladas


# --------------------------------------------------------------------------- #
# Version simbolica
# --------------------------------------------------------------------------- #
def dh_matrix_symbolic(theta, d, a, alpha) -> sp.Matrix:
    """Matriz homogenea 4x4 simbolica. Los angulos se reciben en radianes."""
    ct, st = sp.cos(theta), sp.sin(theta)
    ca, sa = sp.cos(alpha), sp.sin(alpha)
    return sp.Matrix(
        [
            [ct, -st * ca, st * sa, a * ct],
            [st, ct * ca, -ct * sa, a * st],
            [0, sa, ca, d],
            [0, 0, 0, 1],
        ]
    )


def compose_symbolic(matrices: Iterable[sp.Matrix]) -> sp.Matrix:
    total = sp.eye(4)
    for matrix in matrices:
        total = total * matrix
    return total


def accumulate_symbolic(matrices: Sequence[sp.Matrix]) -> List[sp.Matrix]:
    acumuladas: List[sp.Matrix] = []
    total = sp.eye(4)
    for matrix in matrices:
        total = total * matrix
        acumuladas.append(sp.Matrix(total))
    return acumuladas


# --------------------------------------------------------------------------- #
# Utilidades de orientacion
# --------------------------------------------------------------------------- #
def rotation_to_rpy(rotation: np.ndarray) -> np.ndarray:
    """Convierte una matriz de rotacion a angulos RPY (ZYX) en grados."""
    r = np.asarray(rotation, dtype=float)
    sy = float(np.sqrt(r[0, 0] ** 2 + r[1, 0] ** 2))
    if sy > 1e-9:
        roll = np.arctan2(r[2, 1], r[2, 2])
        pitch = np.arctan2(-r[2, 0], sy)
        yaw = np.arctan2(r[1, 0], r[0, 0])
    else:  # configuracion singular (gimbal lock)
        roll = np.arctan2(-r[1, 2], r[1, 1])
        pitch = np.arctan2(-r[2, 0], sy)
        yaw = 0.0
    return np.degrees(np.array([roll, pitch, yaw]))


def clean_matrix(matrix: np.ndarray, tol: float = 1e-12) -> np.ndarray:
    """Elimina ruido numerico muy cercano a cero."""
    limpia = np.array(matrix, dtype=float, copy=True)
    limpia[np.abs(limpia) < tol] = 0.0
    return limpia
