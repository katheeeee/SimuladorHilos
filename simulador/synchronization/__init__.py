"""Mecanismos de sincronización: semáforos modelados y reales."""

from .gestor import GestorSincronizacion
from .mecanismos import Parada, SemaforoReal, etiqueta_hilo, mutex
from .semaforos import Semaforo

__all__ = [
    "Semaforo",
    "GestorSincronizacion",
    "SemaforoReal",
    "Parada",
    "mutex",
    "etiqueta_hilo",
]
