"""Semáforo *modelado* para el motor determinista.

No usa ``threading``: representa explícitamente el contador y la cola de
procesos bloqueados para que la interfaz pueda mostrar el estado de cada
mecanismo de sincronización paso a paso. La semántica es la clásica:

* ``P()`` (wait): si el contador es mayor que cero se decrementa y el proceso
  continúa; si no, el proceso queda bloqueado en la cola de espera.
* ``V()`` (signal): si hay procesos bloqueados, se despierta exactamente a uno
  (sin tocar el contador); si no hay ninguno, se incrementa el contador.
"""

from __future__ import annotations

from collections import deque

from ..model.participante import Participante


class Semaforo:
    """Semáforo contador con cola de espera observable."""

    def __init__(self, nombre: str, valor_inicial: int = 0) -> None:
        if valor_inicial < 0:
            raise ValueError("El valor inicial no puede ser negativo")
        self.nombre = nombre
        self.valor_inicial = valor_inicial
        self.valor = valor_inicial
        self.esperando: deque[Participante] = deque()
        self.operaciones_p = 0
        self.operaciones_v = 0

    def intentar_p(self, participante: Participante) -> bool:
        """Operación ``P()``. Devuelve ``True`` si adquiere, ``False`` si se bloquea."""
        self.operaciones_p += 1
        if self.valor > 0:
            self.valor -= 1
            return True
        self.esperando.append(participante)
        return False

    def v(self) -> Participante | None:
        """Operación ``V()``. Devuelve el participante despertado, o ``None``."""
        self.operaciones_v += 1
        if self.esperando:
            return self.esperando.popleft()
        self.valor += 1
        return None

    def reiniciar(self) -> None:
        self.valor = self.valor_inicial
        self.esperando.clear()
        self.operaciones_p = 0
        self.operaciones_v = 0

    @property
    def bloqueados(self) -> tuple[Participante, ...]:
        return tuple(self.esperando)

    def instantanea(self) -> tuple[str, int, str]:
        """(nombre, valor, lista de bloqueados) para la interfaz."""
        if self.esperando:
            esperando = ", ".join(p.etiqueta for p in self.esperando)
        else:
            esperando = "—"
        return (self.nombre, self.valor, esperando)
