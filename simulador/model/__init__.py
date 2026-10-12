"""Modelo de dominio: ingredientes, participantes, eventos y estadísticas."""

from .estadisticas import Estadisticas
from .evento import Evento, TipoEvento
from .ingredientes import TODOS, Ingrediente, faltante, pares_distintos
from .participante import (
    FUMADORES,
    PARTICIPANTES,
    EstadoHilo,
    Participante,
    fumador_de,
    ingrediente_de,
)

__all__ = [
    "Estadisticas",
    "Evento",
    "TipoEvento",
    "Ingrediente",
    "TODOS",
    "faltante",
    "pares_distintos",
    "EstadoHilo",
    "Participante",
    "FUMADORES",
    "PARTICIPANTES",
    "fumador_de",
    "ingrediente_de",
]
