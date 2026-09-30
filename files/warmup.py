"""
Precalentamiento del motor simbolico.

SymPy importa varios submodulos de forma perezosa la primera vez que se usa
`simplify`, `trigsimp` o `nsimplify`. Si esa carga ocurre dentro del hilo de
calculo, cualquier finalizador de Tkinter que el recolector de basura dispare
en ese momento intentara hablar con Tcl desde un hilo que no es el principal y
la aplicacion se queda bloqueada.

La solucion es ejecutar un calculo pequeno en el hilo principal al arrancar,
para que todos los submodulos queden cargados antes de lanzar ningun hilo.
"""

from __future__ import annotations

from core.kinematics import ForwardKinematicsSolver
from core.robot import DHParameters, Joint, JointType, RobotModel

_warmed = False


def warm_up_symbolic_engine() -> None:
    """Resuelve un robot de juguete para forzar la carga de SymPy."""
    global _warmed
    if _warmed:
        return

    robot = RobotModel(
        name="warmup",
        joints=[
            Joint(1, JointType.REVOLUTE, DHParameters(0.0, 0.0, 1.0, 0.0), 10.0),
            Joint(2, JointType.PRISMATIC, DHParameters(0.0, 0.0, 1.0, 90.0), 0.2),
        ],
    )
    try:
        ForwardKinematicsSolver(robot, symbolic_lengths=True, simplify=True).solve()
    except Exception:  # pragma: no cover - el precalentamiento nunca debe romper la app
        pass
    _warmed = True
