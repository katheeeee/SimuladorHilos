"""Conjunto de mecanismos de sincronización del problema de los fumadores.

El protocolo correcto usa cuatro semáforos y un mutex:

* ``turno_agente`` (valor inicial 1): el agente lo adquiere al empezar cada
  ronda; queda bloqueado hasta que un fumador le devuelve el turno.
* ``turno_fumador[f]`` (valor inicial 0): el agente señala **solo** al fumador
  cuyo ingrediente falta. Un fumador nunca despierta a otro.
* ``mutex_mesa`` (valor inicial 1): protege la mesa y las variables
  compartidas (sección crítica).

Como cada fumador espera únicamente en su propio semáforo y nunca retiene un
ingrediente esperando otro, el protocolo está libre de interbloqueo.
"""

from __future__ import annotations

from ..model.participante import FUMADORES, Participante
from .semaforos import Semaforo


class GestorSincronizacion:
    """Contiene y administra los semáforos modelados de una simulación."""

    def __init__(self) -> None:
        self.turno_agente: Semaforo
        self.turno_fumador: dict[Participante, Semaforo]
        self.mutex_mesa: Semaforo
        self.reiniciar()

    def reiniciar(self) -> None:
        """Recrea todos los semáforos en su estado inicial."""
        self.turno_agente = Semaforo("turno_agente", 1)
        self.turno_fumador = {
            f: Semaforo(f"turno_{f.value}", 0) for f in FUMADORES
        }
        self.mutex_mesa = Semaforo("mutex_mesa", 1)

    @property
    def semaforos(self) -> tuple[Semaforo, ...]:
        """Todos los semáforos, en orden de presentación."""
        return (
            self.turno_agente,
            *self.turno_fumador.values(),
            self.mutex_mesa,
        )

    def filtro(self, fumador: Participante) -> Semaforo:
        """Semáforo que despierta al fumador indicado."""
        return self.turno_fumador[fumador]

    def instantanea(self) -> list[tuple[str, int, str]]:
        return [s.instantanea() for s in self.semaforos]
