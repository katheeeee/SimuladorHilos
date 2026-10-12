"""Modo de análisis: patologías de concurrencia **aisladas** de la solución.

Cada variante produce una secuencia **determinista y acotada** de eventos que
ilustra una patología clásica. No comparte estado con
:class:`~simulador.simulation.motor.MotorSimulacion`, de modo que no puede
desestabilizar la aplicación. Todos sus eventos se marcan como
``ILUSTRATIVO`` y las estadísticas que produce son ilustrativas, no medidas.

Una patología (interbloqueo, inanición, carrera) **solo** se reporta como
detectada cuando la secuencia la demuestra explícitamente.
"""

from __future__ import annotations

from collections import deque
from enum import Enum

from ..model.evento import Evento, TipoEvento
from ..model.ingredientes import Ingrediente
from ..model.participante import FUMADORES, Participante

__all__ = ["ModoAnalisis", "VarianteAnalisis", "Diagnostico"]


class VarianteAnalisis(Enum):
    CARRERA = "carrera"
    INTERBLOQUEO = "interbloqueo"
    INANICION = "inanicion"

    @property
    def etiqueta(self) -> str:
        return _ETIQUETAS[self]

    @property
    def descripcion(self) -> str:
        return _DESCRIPCIONES[self]


_ETIQUETAS = {
    VarianteAnalisis.CARRERA: "Condición de carrera",
    VarianteAnalisis.INTERBLOQUEO: "Interbloqueo",
    VarianteAnalisis.INANICION: "Inanición",
}

_DESCRIPCIONES = {
    VarianteAnalisis.CARRERA: (
        "Dos hilos leen la misma variable compartida sin exclusión mutua y "
        "escriben por separado: una actualización se pierde."
    ),
    VarianteAnalisis.INTERBLOQUEO: (
        "Dos hilos toman un recurso y esperan indefinidamente el del otro: "
        "ninguno puede avanzar."
    ),
    VarianteAnalisis.INANICION: (
        "El agente repite siempre la misma combinación: algunos hilos nunca "
        "son habilitados."
    ),
}


class Diagnostico(Enum):
    NINGUNO = "ninguno"
    CARRERA = "carrera"
    INTERBLOQUEO = "interbloqueo"
    INANICION = "inanicion"


class ModoAnalisis:
    """Secuencia acotada de eventos que ilustra una patología."""

    MAXIMO_PASOS = 60

    def __init__(self, variante: VarianteAnalisis, rondas: int = 6) -> None:
        self.variante = variante
        self.rondas = max(1, rondas)
        self._cola: deque[Evento] = deque()
        self._paso = 0
        self.diagnostico = Diagnostico.NINGUNO
        self._diagnostico_final = Diagnostico.NINGUNO
        self.consumidos: list[Evento] = []
        self._construir()

    # ------------------------------------------------------------------ avance

    def reiniciar(self) -> None:
        self._cola.clear()
        self._paso = 0
        self.diagnostico = Diagnostico.NINGUNO
        self._diagnostico_final = Diagnostico.NINGUNO
        self.consumidos.clear()
        self._construir()

    @property
    def terminado(self) -> bool:
        return not self._cola

    def paso(self) -> Evento | None:
        if not self._cola:
            return None
        evento = self._cola.popleft()
        self.consumidos.append(evento)
        if not self._cola:
            # La patología solo se da por detectada al consumir toda la secuencia.
            self.diagnostico = self._diagnostico_final
        return evento

    def ejecutar_todo(self) -> list[Evento]:
        salida: list[Evento] = []
        while (evento := self.paso()) is not None:
            salida.append(evento)
        return salida

    # ------------------------------------------------------------ construcción

    def añadir(self, participante: Participante | None, operacion: str, resultado: str) -> None:
        self._paso += 1
        self._cola.append(
            Evento(self._paso, participante, operacion, resultado, TipoEvento.ILUSTRATIVO)
        )

    def _construir(self) -> None:
        self.diagnostico = Diagnostico.NINGUNO
        self._diagnostico_final = Diagnostico.NINGUNO
        if self.variante is VarianteAnalisis.CARRERA:
            self._construir_carrera()
        elif self.variante is VarianteAnalisis.INTERBLOQUEO:
            self._construir_interbloqueo()
        else:
            self._construir_inanicion()

    def _construir_carrera(self) -> None:
        a, b = Participante.FUMADOR_TABACO, Participante.FUMADOR_PAPEL
        self.añadir(Participante.AGENTE, "Coloca ingredientes",
                    "coloca dos ingredientes (inventario compartido = 2, sin mutex)")
        self.añadir(a, "Lee variable compartida", "lee inventario = 2")
        self.añadir(b, "Lee variable compartida", "lee inventario = 2  (mismo valor, lectura entrelazada)")
        self.añadir(a, "Escribe variable compartida", "escribe inventario = 2 − 1 = 1")
        self.añadir(b, "Escribe variable compartida", "escribe inventario = 2 − 1 = 1  (pisa el valor anterior)")
        self._diagnostico_final = Diagnostico.CARRERA
        self.añadir(None, "Diagnóstico",
                    "condición de carrera: se esperaban 0 ingredientes y quedó 1 (actualización perdida)")

    def _construir_interbloqueo(self) -> None:
        a, b = Participante.FUMADOR_TABACO, Participante.FUMADOR_PAPEL
        self.añadir(a, "P(recurso_1)", "adquiere recurso_1 y lo retiene")
        self.añadir(b, "P(recurso_2)", "adquiere recurso_2 y lo retiene")
        self.añadir(a, "P(recurso_2)", "se bloquea esperando recurso_2 (lo tiene B)")
        self.añadir(b, "P(recurso_1)", "se bloquea esperando recurso_1 (lo tiene A)")
        self._diagnostico_final = Diagnostico.INTERBLOQUEO
        self.añadir(None, "Diagnóstico",
                    "interbloqueo: A espera a B y B espera a A; ninguno puede continuar")

    def _construir_inanicion(self) -> None:
        tabaco, papel, fosforos = FUMADORES
        par = (Ingrediente.TABACO, Ingrediente.PAPEL)
        for ronda in range(1, self.rondas + 1):
            self.añadir(Participante.AGENTE, "Coloca ingredientes",
                        f"ronda {ronda}: coloca Tabaco y Papel (siempre la misma combinación)")
            self.añadir(fosforos, "Despierta y fuma",
                        "único fumador habilitado en cada ronda")
        self.añadir(tabaco, "Permanece bloqueado",
                    f"nunca fue habilitado en {self.rondas} rondas")
        self.añadir(papel, "Permanece bloqueado",
                    f"nunca fue habilitado en {self.rondas} rondas")
        self._diagnostico_final = Diagnostico.INANICION
        self.añadir(None, "Diagnóstico",
                    "inanición: los fumadores con tabaco y papel nunca recibieron su señal")

    # ------------------------------------------------------------------ informe

    def resumen(self) -> str:
        if self.diagnostico is Diagnostico.NINGUNO:
            return "Sin patología detectada todavía."
        return f"{self.variante.etiqueta}: {self.variante.descripcion}"
