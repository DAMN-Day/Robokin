"""
RoboKin Studio - punto de entrada.

Uso:
    python main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite ejecutar el proyecto desde cualquier directorio de trabajo.
RAIZ = Path(__file__).resolve().parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def main() -> int:
    try:
        from gui.app import RoboKinApp
    except ImportError as error:
        print("Falta una dependencia. Ejecuta: pip install -r requirements.txt")
        print(f"Detalle: {error}")
        return 1

    app = RoboKinApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
