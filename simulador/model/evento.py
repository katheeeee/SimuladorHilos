"""Evento atómico del registro de la simulación."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .participante import Participante


class TipoEvento(Enum):
    """Clasificación del evento, útil para colorear y filtrar el registro."""

    TRANSICION = "transicion"   # cambio de estado de un hilo
    INGREDIENTE = "ingrediente" # colocación / consumo sobre la mesa
    SEMAFORO = "semaforo"       # operación V()/P() sobre un semáforo
    CONTEXTO = "contexto"       # cambio de contexto simulado
    SISTEMA = "sistema"         # arranque, fin, reinicio, etc.
    ILUSTRATIVO = "ilustrativo" # proviene del modo de análisis (no medido)

    @property
    def etiqueta(self) -> str:
        return _ETIQUETAS[self]


_ETIQUETAS: dict[TipoEvento, str] = {
    TipoEvento.TRANSICION: "Transición",
    TipoEvento.INGREDIENTE: "Ingrediente",
    TipoEvento.SEMAFORO: "Semáforo",
    TipoEvento.CONTEXTO: "Contexto",
    TipoEvento.SISTEMA: "Sistema",
    TipoEvento.ILUSTRATIVO: "Ilustrativo",
}


@dataclass(frozen=True)
class Evento:
    """Una operación observable de la simulación.

    Attributes:
        paso: número de paso global (1, 2, 3, ...).
        participante: quién ejecuta la operación (``None`` para eventos de sistema).
        operacion: qué se hace ("Coloca ingrediente", "P(semáforo)", ...).
        resultado: efecto observable sobre el estado.
        tipo: clasificación del evento.
    """

    paso: int
    participante: Participante | None
    operacion: str
    resultado: str
    tipo: TipoEvento = TipoEvento.TRANSICION

    def como_fila(self) -> tuple[str, str, str, str]:
        """Representación tabular para la interfaz y los informes."""
        quien = self.participante.etiqueta if self.participante else "—"
        return (str(self.paso), quien, self.operacion, self.resultado)
