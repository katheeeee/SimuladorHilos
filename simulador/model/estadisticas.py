"""Estadísticas medidas por el simulador (no ilustrativas)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .participante import FUMADORES, PARTICIPANTES, Participante


@dataclass
class Estadisticas:
    """Contadores acumulados durante una ejecución.

    Todos los valores de esta clase son **medidos** por el motor determinista
    o por el backend de hilos reales. El modo de análisis mantiene sus propias
    estadísticas y se marcan siempre como ilustrativas.
    """

    rondas_completadas: int = 0
    cigarros_por_fumador: dict[Participante, int] = field(
        default_factory=lambda: {f: 0 for f in FUMADORES}
    )
    habilitaciones: dict[Participante, int] = field(
        default_factory=lambda: {p: 0 for p in PARTICIPANTES}
    )
    cambios_contexto: int = 0

    def reiniciar(self) -> None:
        """Devuelve todos los contadores a cero."""
        self.rondas_completadas = 0
        for f in FUMADORES:
            self.cigarros_por_fumador[f] = 0
        for p in PARTICIPANTES:
            self.habilitaciones[p] = 0
        self.cambios_contexto = 0

    def registrar_cigarro(self, fumador: Participante) -> None:
        self.cigarros_por_fumador[fumador] += 1

    def registrar_habilitacion(self, participante: Participante) -> None:
        self.habilitaciones[participante] += 1

    def registrar_cambio_contexto(self) -> None:
        self.cambios_contexto += 1

    @property
    def total_cigarros(self) -> int:
        return sum(self.cigarros_por_fumador.values())

    def como_filas(self) -> list[tuple[str, str]]:
        """Filas (nombre, valor) para el panel de estadísticas."""
        filas = [("Rondas completadas", str(self.rondas_completadas))]
        for f in FUMADORES:
            filas.append((f"Cigarrillos de {f.etiqueta}", str(self.cigarros_por_fumador[f])))
        for p in PARTICIPANTES:
            filas.append((f"Habilitaciones de {p.etiqueta}", str(self.habilitaciones[p])))
        filas.append(("Cambios de contexto (simulados)", str(self.cambios_contexto)))
        return filas
