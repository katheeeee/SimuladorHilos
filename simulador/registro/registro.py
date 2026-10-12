"""Registro de eventos a prueba de accesos concurrentes.

El motor determinista y el backend de hilos reales escriben aquí. La interfaz
**nunca** lee al mismo tiempo desde el hilo de trabajo: consume una copia
mediante un temporizador en el hilo principal de Qt.
"""

from __future__ import annotations

from collections import deque
from threading import Lock

from ..model.evento import Evento


class RegistroEventos:
    """Buffer circular de eventos protegido por un mutex real."""

    def __init__(self, capacidad: int = 4000) -> None:
        self._capacidad = capacidad
        self._eventos: deque[Evento] = deque(maxlen=capacidad)
        self._lock = Lock()

    def agregar(self, evento: Evento) -> None:
        with self._lock:
            self._eventos.append(evento)

    def eventos(self) -> list[Evento]:
        with self._lock:
            return list(self._eventos)

    def ultimo(self) -> Evento | None:
        with self._lock:
            return self._eventos[-1] if self._eventos else None

    def limpiar(self) -> None:
        with self._lock:
            self._eventos.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._eventos)
