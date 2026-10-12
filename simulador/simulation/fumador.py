"""Modelo de un fumador: posee un ingrediente permanente y espera su turno."""

from __future__ import annotations

from ..model.ingredientes import Ingrediente
from ..model.participante import EstadoHilo, Participante


class Fumador:
    """Un fumador que espera ser habilitado por el agente.

    Comienza **bloqueado** en su propio semáforo. Cuando el agente le señala
    que la combinación necesaria está en la mesa, despierta, arma el cigarrillo
    y vuelve a bloquearse. Nunca retiene un ingrediente esperando otro, por lo
    que no puede participar en un interbloqueo.
    """

    def __init__(self, participante: Participante) -> None:
        if participante.ingrediente_propio is None:
            raise ValueError("Un fumador debe tener un ingrediente propio")
        self.participante = participante
        self.ingrediente_propio: Ingrediente = participante.ingrediente_propio
        self.estado = EstadoHilo.BLOQUEADO
        self.accion = "Esperando turno"
        self.cigarros = 0

    def reiniciar(self) -> None:
        self.estado = EstadoHilo.BLOQUEADO
        self.accion = "Esperando turno"
        self.cigarros = 0

    @property
    def nombre(self) -> str:
        return self.participante.etiqueta
