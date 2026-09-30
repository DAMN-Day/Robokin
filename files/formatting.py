"""Formato de numeros, matrices numericas y expresiones simbolicas."""

from __future__ import annotations

from typing import List, Sequence

import numpy as np
import sympy as sp


def format_number(value: float, decimals: int = 4, tol: float = 5e-5) -> str:
    """Numero con signo estable y sin -0.0000."""
    valor = float(value)
    if abs(valor) < tol:
        valor = 0.0
    return f"{valor:.{decimals}f}"


def matrix_rows(matrix: np.ndarray, decimals: int = 4) -> List[List[str]]:
    """Matriz numerica como lista de filas de cadenas ya formateadas."""
    datos = np.asarray(matrix, dtype=float)
    return [[format_number(v, decimals) for v in fila] for fila in datos]


def matrix_to_text(matrix: np.ndarray, decimals: int = 4) -> str:
    """Matriz numerica como bloque de texto monoespaciado alineado."""
    filas = matrix_rows(matrix, decimals)
    ancho = max((len(v) for fila in filas for v in fila), default=1)
    return "\n".join("  ".join(v.rjust(ancho) for v in fila) for fila in filas)


def symbolic_to_text(matrix: sp.Matrix, columns: int = 110) -> str:
    """Expresion simbolica en texto 'pretty' con simbolos unicode."""
    try:
        return sp.pretty(matrix, use_unicode=True, num_columns=columns)
    except Exception:  # pragma: no cover - salvaguarda de renderizado
        return str(matrix)


def symbolic_elements(matrix: sp.Matrix, only_nontrivial: bool = True) -> List[str]:
    """Lista elemento por elemento: 'T[0,3] = ...'.

    Mas legible que la matriz completa cuando las expresiones son largas.
    """
    lineas: List[str] = []
    for i in range(matrix.rows):
        for j in range(matrix.cols):
            elemento = sp.simplify(matrix[i, j]) if matrix[i, j].free_symbols else matrix[i, j]
            if only_nontrivial and elemento in (0, 1) and not elemento.free_symbols:
                continue
            lineas.append(f"T[{i},{j}] = {elemento}")
    return lineas


def vector_to_text(vector: Sequence[float], decimals: int = 4, sep: str = ", ") -> str:
    return sep.join(format_number(v, decimals) for v in vector)


def latex_matrix(matrix: sp.Matrix) -> str:
    """Representacion LaTeX, util para exportar a reportes."""
    return sp.latex(matrix)
