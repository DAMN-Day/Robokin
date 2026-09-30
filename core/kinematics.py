"""
Motor de cinematica directa.

Recibe un `RobotModel` y produce:
  * la matriz A_i de cada eslabon (numerica y simbolica),
  * las matrices acumuladas T_0^i,
  * la matriz final T_0^n,
  * la posicion y orientacion del efector final,
  * los origenes de cada sistema coordenado (utiles para graficar).

La GUI solo consume `ForwardKinematicsResult`; asi el motor puede sustituirse
o ampliarse sin tocar la interfaz.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

import numpy as np
import sympy as sp

from core import dh
from core.robot import JointType, RobotModel


# --------------------------------------------------------------------------- #
# Resultado
# --------------------------------------------------------------------------- #
@dataclass
class ForwardKinematicsResult:
    """Contenedor con todo lo que la interfaz necesita mostrar."""

    joint_symbols: List[sp.Symbol] = field(default_factory=list)
    numeric_links: List[np.ndarray] = field(default_factory=list)      # A_i
    numeric_chain: List[np.ndarray] = field(default_factory=list)      # T_0^i
    symbolic_links: List[sp.Matrix] = field(default_factory=list)      # A_i
    symbolic_chain: List[sp.Matrix] = field(default_factory=list)      # T_0^i
    numeric_total: np.ndarray = field(default_factory=lambda: np.eye(4))
    symbolic_total: sp.Matrix = field(default_factory=lambda: sp.eye(4))
    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    rpy_degrees: np.ndarray = field(default_factory=lambda: np.zeros(3))
    origins: List[np.ndarray] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    simplified: bool = False

    @property
    def dof(self) -> int:
        return len(self.numeric_links)


# --------------------------------------------------------------------------- #
# Solver
# --------------------------------------------------------------------------- #
class ForwardKinematicsSolver:
    """Calcula la cinematica directa de una cadena serial con DH estandar.

    Args:
        robot: modelo validado del manipulador.
        symbolic_lengths: si es True, las longitudes constantes (a_i, d_i)
            aparecen como simbolos (a1, d1, ...) en el resultado algebraico.
        simplify: aplica `trigsimp` a la matriz final. Es mas legible pero
            considerablemente mas lento a partir de 4 o 5 grados de libertad.
    """

    def __init__(
        self,
        robot: RobotModel,
        symbolic_lengths: bool = False,
        simplify: bool = False,
    ) -> None:
        self.robot = robot
        self.symbolic_lengths = symbolic_lengths
        self.simplify = simplify

    # -- helpers ----------------------------------------------------------- #
    @staticmethod
    def _exact(value: float):
        """Convierte un float a una expresion exacta legible (90 -> 90, 0.5 -> 1/2)."""
        return sp.nsimplify(sp.Rational(str(value)), rational=True)

    def _const(self, value: float, name: str):
        """Constante simbolica: simbolo con nombre o valor exacto."""
        if self.symbolic_lengths and abs(value) > 1e-12:
            return sp.Symbol(name, real=True)
        return self._exact(value)

    def _angle(self, degrees: float):
        """Angulo constante convertido a radianes de forma exacta (90 -> pi/2)."""
        return sp.rad(self._exact(degrees))

    # -- API --------------------------------------------------------------- #
    def solve(self) -> ForwardKinematicsResult:
        self.robot.validate()
        inicio = time.perf_counter()

        resultado = ForwardKinematicsResult(simplified=self.simplify)

        for joint in self.robot.joints:
            i = joint.index
            simbolo = sp.Symbol(joint.symbol, real=True)
            resultado.joint_symbols.append(simbolo)

            if joint.joint_type is JointType.REVOLUTE:
                theta_sym = simbolo                      # variable articular
                d_sym = self._const(joint.dh.d, f"d{i}")
                theta_num = np.radians(joint.q)
                d_num = joint.dh.d
            else:  # prismatica
                theta_sym = self._angle(joint.dh.theta)
                d_sym = simbolo                          # variable articular
                theta_num = np.radians(joint.dh.theta)
                d_num = joint.q

            a_sym = self._const(joint.dh.a, f"a{i}")
            alpha_sym = self._angle(joint.dh.alpha)

            resultado.symbolic_links.append(
                dh.dh_matrix_symbolic(theta_sym, d_sym, a_sym, alpha_sym)
            )
            resultado.numeric_links.append(
                dh.dh_matrix_numeric(
                    theta_num, d_num, joint.dh.a, np.radians(joint.dh.alpha)
                )
            )

        # Cadenas acumuladas
        resultado.numeric_chain = dh.accumulate_numeric(resultado.numeric_links)
        resultado.symbolic_chain = dh.accumulate_symbolic(resultado.symbolic_links)

        resultado.numeric_total = dh.clean_matrix(resultado.numeric_chain[-1])
        total_simbolica = sp.Matrix(resultado.symbolic_chain[-1])

        if self.simplify:
            total_simbolica = sp.trigsimp(sp.expand_trig(sp.simplify(total_simbolica)))
        else:
            total_simbolica = sp.nsimplify(total_simbolica, rational=False)
        resultado.symbolic_total = sp.Matrix(total_simbolica)

        resultado.position = resultado.numeric_total[:3, 3].copy()
        resultado.rpy_degrees = dh.rotation_to_rpy(resultado.numeric_total[:3, :3])
        resultado.origins = [np.zeros(3)] + [
            np.array(T[:3, 3], dtype=float) for T in resultado.numeric_chain
        ]
        resultado.elapsed_seconds = time.perf_counter() - inicio
        return resultado


def solve_forward_kinematics(
    robot: RobotModel,
    symbolic_lengths: bool = False,
    simplify: bool = False,
) -> ForwardKinematicsResult:
    """Atajo funcional para usar el solver desde otros modulos."""
    return ForwardKinematicsSolver(robot, symbolic_lengths, simplify).solve()
