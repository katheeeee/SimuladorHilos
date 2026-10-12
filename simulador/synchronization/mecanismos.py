"""Envoltorios sobre los mecanismos *reales* de ``threading``.

Estos objetos se usan en el modo de ejecución con hilos reales
(:mod:`simulador.simulation.concurrente`). A diferencia de
:class:`~simulador.synchronization.semaforos.Semaforo`, aquí la sincronización
la realiza el planificador del sistema operativo; aquí solo la observamos.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from ..model.participante import Participante


@dataclass
class SemaforoReal:
    """``threading.Semaphore`` con una estimación del contador para mostrar."""

    nombre: str
    valor_inicial: int = 0
    _sem: threading.Semaphore = field(init=False, repr=False)
    _lock: threading.Lock = field(init=False, repr=False)
    valor_estimado: int = field(init=False)

    def __post_init__(self) -> None:
        self._sem = threading.Semaphore(self.valor_inicial)
        self._lock = threading.Lock()
        self.valor_estimado = self.valor_inicial

    def p(self) -> None:
        self._sem.acquire()
        with self._lock:
            self.valor_estimado -= 1

    def v(self) -> None:
        self._sem.release()
        with self._lock:
            self.valor_estimado += 1

    def __enter__(self) -> "SemaforoReal":
        self.p()
        return self

    def __exit__(self, *exc: object) -> None:
        self.v()


def mutex() -> threading.Lock:
    """Un mutex real (``threading.Lock``)."""
    return threading.Lock()


class Parada:
    """Señal de parada cooperativa para terminar hilos reales limpiamente."""

    def __init__(self) -> None:
        self._evento = threading.Event()

    def detener(self) -> None:
        self._evento.set()

    def activa(self) -> bool:
        return not self._evento.is_set()

    def esperar(self, timeout: float | None = None) -> bool:
        return self._evento.wait(timeout)

    def limpiar(self) -> None:
        self._evento.clear()


def etiqueta_hilo(participante: Participante) -> str:
    """Nombre legible para ``threading.Thread(name=...)``."""
    return participante.value
