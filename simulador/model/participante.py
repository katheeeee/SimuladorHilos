"""Participantes (agente y fumadores) y estados de los hilos simulados."""

from __future__ import annotations

from enum import Enum

from .ingredientes import Ingrediente


class EstadoHilo(Enum):
    """Estados de un hilo usados en la simulación.

    * ``LISTO``      : puede usar la CPU, solo espera ser elegido.
    * ``EJECUTANDO`` : ocupa la CPU en este instante.
    * ``BLOQUEADO``  : no puede avanzar; espera una señal (un semáforo).
    * ``TERMINADO``  : finalizó su trabajo.
    """

    LISTO = "listo"
    EJECUTANDO = "ejecutando"
    BLOQUEADO = "bloqueado"
    TERMINADO = "terminado"

    @property
    def etiqueta(self) -> str:
        return _ESTADO_ETIQUETA[self]

    @property
    def descripcion(self) -> str:
        return _ESTADO_DESCRIPCION[self]


_ESTADO_ETIQUETA: dict[EstadoHilo, str] = {
    EstadoHilo.LISTO: "Listo",
    EstadoHilo.EJECUTANDO: "Ejecutando",
    EstadoHilo.BLOQUEADO: "Bloqueado",
    EstadoHilo.TERMINADO: "Terminado",
}

_ESTADO_DESCRIPCION: dict[EstadoHilo, str] = {
    EstadoHilo.LISTO: "Listo para usar la CPU (no bloqueado)",
    EstadoHilo.EJECUTANDO: "Usando la CPU ahora mismo",
    EstadoHilo.BLOQUEADO: "Bloqueado esperando una señal",
    EstadoHilo.TERMINADO: "Trabajo finalizado",
}


class Participante(Enum):
    """Los cuatro participantes del problema."""

    AGENTE = "agente"
    FUMADOR_TABACO = "fumador_tabaco"
    FUMADOR_PAPEL = "fumador_papel"
    FUMADOR_FOSFOROS = "fumador_fosforos"

    @property
    def etiqueta(self) -> str:
        return _PARTICIPANTE_ETIQUETA[self]

    @property
    def ingrediente_propio(self) -> Ingrediente | None:
        """Ingrediente permanente del fumador (``None`` para el agente)."""
        return _PROPIO.get(self)


_PARTICIPANTE_ETIQUETA: dict[Participante, str] = {
    Participante.AGENTE: "Agente",
    Participante.FUMADOR_TABACO: "Fumador con tabaco",
    Participante.FUMADOR_PAPEL: "Fumador con papel",
    Participante.FUMADOR_FOSFOROS: "Fumador con fósforos",
}

#: Ingrediente que posee cada fumador de forma permanente.
_PROPIO: dict[Participante, Ingrediente] = {
    Participante.FUMADOR_TABACO: Ingrediente.TABACO,
    Participante.FUMADOR_PAPEL: Ingrediente.PAPEL,
    Participante.FUMADOR_FOSFOROS: Ingrediente.FOSFOROS,
}

#: Los tres fumadores, en orden canónico.
FUMADORES: tuple[Participante, ...] = (
    Participante.FUMADOR_TABACO,
    Participante.FUMADOR_PAPEL,
    Participante.FUMADOR_FOSFOROS,
)

#: Todos los participantes.
PARTICIPANTES: tuple[Participante, ...] = (Participante.AGENTE, *FUMADORES)


def fumador_de(ingrediente: Ingrediente) -> Participante:
    """Fumador que posee de forma permanente ``ingrediente``."""
    for fumador, propio in _PROPIO.items():
        if propio is ingrediente:
            return fumador
    raise KeyError(ingrediente)


def ingrediente_de(fumador: Participante) -> Ingrediente:
    """Ingrediente permanente de un fumador (error si es el agente)."""
    try:
        return _PROPIO[fumador]
    except KeyError as exc:  # pragma: no cover - defensivo
        raise ValueError(f"{fumador} no es un fumador") from exc
