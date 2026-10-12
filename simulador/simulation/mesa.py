"""Mesa: variable compartida que indica qué ingredientes están disponibles."""

from __future__ import annotations

from ..model.ingredientes import TODOS, Ingrediente


class Mesa:
    """Los tres ingredientes como variables compartidas booleanas.

    Es la sección crítica protegida por ``mutex_mesa``. El motor solo la
    modifica a través de los métodos :meth:`colocar` y :meth:`tomar`.
    """

    def __init__(self) -> None:
        self._contenido: set[Ingrediente] = set()

    def colocar(self, ingrediente: Ingrediente) -> None:
        if ingrediente in self._contenido:
            raise ValueError(f"{ingrediente.etiqueta} ya está en la mesa")
        self._contenido.add(ingrediente)

    def tomar(self, ingrediente: Ingrediente) -> None:
        if ingrediente not in self._contenido:
            raise ValueError(f"{ingrediente.etiqueta} no está en la mesa")
        self._contenido.discard(ingrediente)

    def vaciar(self) -> None:
        self._contenido.clear()

    def disponible(self, ingrediente: Ingrediente) -> bool:
        return ingrediente in self._contenido

    @property
    def contenido(self) -> frozenset[Ingrediente]:
        return frozenset(self._contenido)

    @property
    def variables(self) -> dict[Ingrediente, bool]:
        """Estado de cada variable compartida (tabaco, papel, fósforos)."""
        return {i: self.disponible(i) for i in TODOS}

    @property
    def cantidad(self) -> int:
        return len(self._contenido)
