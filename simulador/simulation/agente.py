"""Modelo del agente que coloca combinaciones de ingredientes."""

from __future__ import annotations

from ..model.ingredientes import Ingrediente, TODOS
from ..model.participante import EstadoHilo, FUMADORES, Participante


class Agente:
    """Coloca dos ingredientes distintos en la mesa en cada ronda.

    Política **equitativa**: cada ronda fuma un fumador distinto (rotación
    cíclica sobre los tres), de modo que ninguno se queda sin fumar. La
    semilla solo fija el desplazamiento inicial de la rotación, por lo que la
    secuencia sigue siendo reproducible. (El caso patológico de inanición se
    enseña aparte en :class:`~simulador.simulation.modo_incorrecto`.)
    """

    def __init__(self, semilla: int) -> None:
        self._inicio = semilla % len(FUMADORES)
        self._colocadas = 0
        self.estado = EstadoHilo.LISTO
        self.accion = "En espera"
        self.ronda_actual = 0

    def seleccionar(self) -> tuple[Ingrediente, Ingrediente]:
        """Devuelve los dos ingredientes que el fumador de turno no posee."""
        fumador = FUMADORES[(self._inicio + self._colocadas) % len(FUMADORES)]
        self._colocadas += 1
        propio = fumador.ingrediente_propio
        return tuple(ingrediente for ingrediente in TODOS if ingrediente is not propio)

    def reiniciar(self, semilla: int | None = None) -> None:
        if semilla is not None:
            self._inicio = semilla % len(FUMADORES)
        self._colocadas = 0
        self.estado = EstadoHilo.LISTO
        self.accion = "En espera"
        self.ronda_actual = 0

    @property
    def participante(self) -> Participante:
        return Participante.AGENTE
