"""
Configuraciones de ejemplo listas para cargar en la tabla DH.

Sirven como punto de partida y como casos de prueba conocidos. Para agregar un
robot nuevo basta con anadir una entrada al diccionario `PRESETS`.
"""

from __future__ import annotations

from typing import Dict, List

from core.robot import DHParameters, Joint, JointType, RobotModel


def _revoluta(i: int, d: float, a: float, alpha: float, q: float = 0.0) -> Joint:
    return Joint(i, JointType.REVOLUTE, DHParameters(theta=0.0, d=d, a=a, alpha=alpha), q)


def _prismatica(i: int, theta: float, a: float, alpha: float, q: float = 0.0) -> Joint:
    return Joint(i, JointType.PRISMATIC, DHParameters(theta=theta, d=0.0, a=a, alpha=alpha), q)


def planar_2r() -> RobotModel:
    return RobotModel(
        name="Planar 2R",
        joints=[
            _revoluta(1, d=0.0, a=1.0, alpha=0.0, q=30.0),
            _revoluta(2, d=0.0, a=0.8, alpha=0.0, q=45.0),
        ],
    )


def antropomorfico_3r() -> RobotModel:
    return RobotModel(
        name="Antropomorfico 3R",
        joints=[
            _revoluta(1, d=0.50, a=0.00, alpha=90.0, q=0.0),
            _revoluta(2, d=0.00, a=0.80, alpha=0.0, q=45.0),
            _revoluta(3, d=0.00, a=0.60, alpha=0.0, q=-30.0),
        ],
    )


def scara_rrp() -> RobotModel:
    return RobotModel(
        name="SCARA (RRP)",
        joints=[
            _revoluta(1, d=0.40, a=0.50, alpha=0.0, q=20.0),
            _revoluta(2, d=0.00, a=0.40, alpha=180.0, q=-35.0),
            _prismatica(3, theta=0.0, a=0.0, alpha=0.0, q=0.15),
        ],
    )


PRESETS: Dict[str, callable] = {
    "Planar 2R": planar_2r,
    "Antropomorfico 3R": antropomorfico_3r,
    "SCARA (RRP)": scara_rrp,
}


def preset_names() -> List[str]:
    return list(PRESETS.keys())


def load_preset(name: str) -> RobotModel:
    if name not in PRESETS:
        raise KeyError(f"No existe la configuracion {name!r}.")
    return PRESETS[name]()
