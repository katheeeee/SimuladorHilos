"""Ingredientes compartidos del problema de los fumadores.

Para fabricar un cigarrillo se necesitan exactamente tres ingredientes:
tabaco, papel y fósforos. El agente coloca dos distintos en la mesa y el
fumador que posee el tercero (el que falta) puede actuar.
"""

from __future__ import annotations

from enum import Enum
from itertools import combinations


class Ingrediente(Enum):
    """Los tres ingredientes posibles."""

    TABACO = "tabaco"
    PAPEL = "papel"
    FOSFOROS = "fosforos"

    @property
    def etiqueta(self) -> str:
        return _ETIQUETAS[self]


_ETIQUETAS: dict[Ingrediente, str] = {
    Ingrediente.TABACO: "Tabaco",
    Ingrediente.PAPEL: "Papel",
    Ingrediente.FOSFOROS: "Fósforos",
}

#: Orden canónico de los ingredientes (útil para mostrar y para barajar).
TODOS: tuple[Ingrediente, ...] = (
    Ingrediente.TABACO,
    Ingrediente.PAPEL,
    Ingrediente.FOSFOROS,
)


def pares_distintos() -> tuple[tuple[Ingrediente, Ingrediente], ...]:
    """Las tres combinaciones posibles de dos ingredientes distintos."""
    return tuple((a, b) for a, b in combinations(TODOS, 2))


def faltante(par: tuple[Ingrediente, Ingrediente]) -> Ingrediente:
    """Ingrediente que no está en el par; identifica al fumador que puede actuar.

    Si el agente coloca seis opciones de dos ingredientes, el ``faltante`` es
    el ingrediente que posee de forma permanente el único fumador habilitado.
    """
    if par[0] == par[1]:
        raise ValueError("La combinación debe tener dos ingredientes distintos")
    return next(i for i in TODOS if i not in par)
