"""
Modelo de datos del robot.

Define las estructuras que describen un manipulador serial mediante la
convencion de Denavit-Hartenberg (DH estandar):

    A_i = Rot_z(theta_i) * Trans_z(d_i) * Trans_x(a_i) * Rot_x(alpha_i)

Este modulo no depende de la interfaz grafica ni de sympy/numpy, de modo que
puede reutilizarse desde scripts, pruebas o servicios web.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class JointType(str, Enum):
    """Tipo de articulacion soportado."""

    REVOLUTE = "Revoluta"
    PRISMATIC = "Prismatica"

    @property
    def is_revolute(self) -> bool:
        return self is JointType.REVOLUTE

    @property
    def variable_symbol(self) -> str:
        """Parametro DH que se convierte en variable articular."""
        return "theta" if self.is_revolute else "d"

    @property
    def unit(self) -> str:
        return "grados" if self.is_revolute else "unidades de longitud"

    @classmethod
    def from_label(cls, label: str) -> "JointType":
        for member in cls:
            if member.value.lower() == label.strip().lower():
                return member
        raise ValueError(f"Tipo de articulacion desconocido: {label!r}")


class ModelError(ValueError):
    """Error de validacion del modelo del robot."""


@dataclass
class DHParameters:
    """Parametros DH constantes de un eslabon.

    Attributes:
        theta: Angulo alrededor de z_{i-1} en grados. Constante solo si la
            articulacion es prismatica.
        d: Desplazamiento a lo largo de z_{i-1}. Constante solo si la
            articulacion es revoluta.
        a: Longitud del eslabon (distancia a lo largo de x_i).
        alpha: Torsion del eslabon alrededor de x_i, en grados.
    """

    theta: float = 0.0
    d: float = 0.0
    a: float = 0.0
    alpha: float = 0.0


@dataclass
class Joint:
    """Una articulacion con su eslabon asociado."""

    index: int
    joint_type: JointType = JointType.REVOLUTE
    dh: DHParameters = field(default_factory=DHParameters)
    q: float = 0.0  # valor actual de la variable articular

    @property
    def symbol(self) -> str:
        return f"q{self.index}"

    @property
    def link_length(self) -> float:
        """Longitud del eslabon (parametro a de DH)."""
        return self.dh.a

    def describe(self) -> str:
        unidad = "deg" if self.joint_type.is_revolute else "u"
        return f"{self.symbol} ({self.joint_type.value}) = {self.q:g} {unidad}"


@dataclass
class RobotModel:
    """Cadena cinematica serial completa."""

    joints: List[Joint] = field(default_factory=list)
    name: str = "Manipulador"

    @property
    def dof(self) -> int:
        """Grados de libertad (numero de articulaciones)."""
        return len(self.joints)

    def validate(self) -> None:
        if not self.joints:
            raise ModelError("El robot debe tener al menos una articulacion.")
        for i, joint in enumerate(self.joints, start=1):
            if joint.index != i:
                raise ModelError(
                    f"Indice inconsistente en la articulacion {i} (se recibio {joint.index})."
                )
            valores = (joint.dh.theta, joint.dh.d, joint.dh.a, joint.dh.alpha, joint.q)
            for valor in valores:
                if not isinstance(valor, (int, float)):
                    raise ModelError(
                        f"La articulacion {i} contiene un valor no numerico."
                    )
            if joint.dh.a < 0:
                raise ModelError(
                    f"La longitud del eslabon {i} no puede ser negativa."
                )

    def summary(self) -> str:
        tipos = ", ".join(
            "R" if j.joint_type.is_revolute else "P" for j in self.joints
        )
        return f"{self.name} | {self.dof} GDL | cadena: {tipos}"
