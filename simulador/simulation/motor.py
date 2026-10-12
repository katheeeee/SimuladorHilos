"""Motor de simulación determinista del problema de los fumadores.

Es una máquina de estados dirigida por una cola de pasos. Cada llamada a
:meth:`MotorSimulacion.paso` ejecuta **exactamente una** transición lógica y
emite un :class:`~simulador.model.evento.Evento`. El modo manual y el
automático recorren la misma secuencia, de modo que el resultado es
reproducible y equitativo (cada ronda fuma un fumador distinto; la semilla
solo fija el inicio de esa rotación).

El motor no usa ``threading``: modela los semáforos y las variables compartidas
para poder inspeccionar cada operación. El backend con hilos reales vive en
:mod:`simulador.simulation.concurrente`.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict

from ..model.estadisticas import Estadisticas
from ..model.evento import Evento, TipoEvento
from ..model.ingredientes import Ingrediente, faltante
from ..model.participante import (
    FUMADORES,
    PARTICIPANTES,
    EstadoHilo,
    Participante,
    fumador_de,
)
from ..registro.registro import RegistroEventos
from ..synchronization.gestor import GestorSincronizacion
from .agente import Agente
from .fumador import Fumador
from .mesa import Mesa

__all__ = ["MotorSimulacion", "Instantanea"]

#: Límite de rondas por defecto.
LIMITE_POR_DEFECTO = 6
#: Semilla por defecto: misma secuencia de combinaciones en manual y auto.
SEMILLA_POR_DEFECTO = 20260611


@dataclass(frozen=True)
class Instantanea:
    """Vista inmutable del estado del motor para la interfaz."""

    ronda_actual: int
    limite: int
    terminado: bool
    en_cpu: Participante | None
    estados: Dict[Participante, EstadoHilo]
    acciones: Dict[Participante, str]
    variables: Dict[Ingrediente, bool]
    contenido_mesa: frozenset
    semaforos: tuple
    estadisticas: Estadisticas
    ultimo_evento: Evento | None
    total_eventos: int


class _Paso:
    """Un paso programado: función a ejecutar y metadatos del evento."""

    __slots__ = ("participante", "operacion", "tipo", "ejecutar")

    def __init__(
        self,
        participante: Participante | None,
        operacion: str,
        tipo: TipoEvento,
        ejecutar: Callable[[], str],
    ) -> None:
        self.participante = participante
        self.operacion = operacion
        self.tipo = tipo
        self.ejecutar = ejecutar


class MotorSimulacion:
    """Máquina de estados determinista del problema de los fumadores."""

    def __init__(self, limite_rondas: int = LIMITE_POR_DEFECTO, semilla: int = SEMILLA_POR_DEFECTO) -> None:
        if limite_rondas < 0:
            raise ValueError("El límite de rondas no puede ser negativo")
        self.limite = limite_rondas
        self.semilla = semilla
        self.gestor = GestorSincronizacion()
        self.registro = RegistroEventos()
        self.mesa = Mesa()
        self.agente = Agente(semilla)
        self.fumadores: dict[Participante, Fumador] = {
            f: Fumador(f) for f in FUMADORES
        }
        self.estadisticas = Estadisticas()
        self._cola: deque[_Paso] = deque()
        self._paso = 0
        self._rondas_planificadas = 0
        self._terminacion_planificada = False
        self._en_cpu: Participante | None = None
        self._ultimo: Evento | None = None
        self._estado_inicial()

    # ------------------------------------------------------------------ estado

    def _estado_inicial(self) -> None:
        """Restablece el estado lógico (semáforos, mesa, participantes)."""
        self.gestor.reiniciar()
        self.mesa.vaciar()
        self.agente.reiniciar(self.semilla)
        for fumador in self.fumadores.values():
            fumador.reiniciar()
        self.registro.limpiar()
        self.estadisticas.reiniciar()
        self._cola.clear()
        self._paso = 0
        self._rondas_planificadas = 0
        self._terminacion_planificada = False
        self._en_cpu = None
        self._ultimo = None
        # Los fumadores arrancan bloqueados en su propio semáforo (su primer P).
        for fumador in self.fumadores.values():
            self.gestor.turno_fumador[fumador.participante].intentar_p(fumador.participante)
        # El primer evento: la simulación está lista para comenzar.
        self.registro.agregar(
            Evento(0, None, "Simulación lista", "Pulse «Siguiente paso» o «Ejecutar»", TipoEvento.SISTEMA)
        )

    def reiniciar(self, limite_rondas: int | None = None, semilla: int | None = None) -> None:
        """Devuelve el motor a su estado inicial, sin hilos ni señales antiguas."""
        if limite_rondas is not None:
            if limite_rondas < 0:
                raise ValueError("El límite de rondas no puede ser negativo")
            self.limite = limite_rondas
        if semilla is not None:
            self.semilla = semilla
        self._estado_inicial()

    # --------------------------------------------------------------- consultas

    @property
    def terminado(self) -> bool:
        return self._terminacion_planificada and not self._cola

    @property
    def ronda_actual(self) -> int:
        return self.agente.ronda_actual

    @property
    def paso_actual(self) -> int:
        return self._paso

    @property
    def pendientes(self) -> int:
        return len(self._cola)

    def instantanea(self) -> Instantanea:
        estados: dict[Participante, EstadoHilo] = {Participante.AGENTE: self.agente.estado}
        acciones: dict[Participante, str] = {Participante.AGENTE: self.agente.accion}
        for f in FUMADORES:
            estados[f] = self.fumadores[f].estado
            acciones[f] = self.fumadores[f].accion
        return Instantanea(
            ronda_actual=self.agente.ronda_actual,
            limite=self.limite,
            terminado=self.terminado,
            en_cpu=self._en_cpu,
            estados=estados,
            acciones=acciones,
            variables=self.mesa.variables,
            contenido_mesa=self.mesa.contenido,
            semaforos=tuple(self.gestor.instantanea()),
            estadisticas=self.estadisticas,
            ultimo_evento=self._ultimo,
            total_eventos=self._paso,
        )

    # ------------------------------------------------------------------ avance

    def paso(self) -> Evento | None:
        """Ejecuta exactamente una transición lógica. ``None`` si ya terminó."""
        if not self._cola:
            if self._rondas_planificadas < self.limite:
                self._planificar_ronda()
            elif not self._terminacion_planificada:
                self._planificar_terminacion()
            else:
                return None

        realizado = self._cola.popleft()
        resultado = realizado.ejecutar()
        self._paso += 1
        evento = Evento(self._paso, realizado.participante, realizado.operacion, resultado, realizado.tipo)
        self.registro.agregar(evento)
        self._ultimo = evento
        return evento

    def avanzar(self, n: int) -> list[Evento]:
        """Ejecuta hasta ``n`` pasos (o hasta terminar). Útil en las pruebas."""
        salida: list[Evento] = []
        for _ in range(n):
            evento = self.paso()
            if evento is None:
                break
            salida.append(evento)
        return salida

    def ejecutar_hasta_terminar(self, maximo: int = 5000) -> list[Evento]:
        """Ejecuta la simulación completa con un tope de seguridad."""
        salida: list[Evento] = []
        for _ in range(maximo):
            evento = self.paso()
            if evento is None:
                break
            salida.append(evento)
        return salida

    # --------------------------------------------------------------- utilidades

    def _encolar(
        self,
        participante: Participante | None,
        operacion: str,
        tipo: TipoEvento,
        ejecutar: Callable[[], str],
    ) -> None:
        self._cola.append(_Paso(participante, operacion, tipo, ejecutar))

    def _encolar_contexto(self, destino: Participante) -> None:
        def ejecutar() -> str:
            anterior = self._en_cpu
            self._en_cpu = destino
            self.estadisticas.registrar_cambio_contexto()
            if destino is Participante.AGENTE:
                self.agente.estado = EstadoHilo.EJECUTANDO
            else:
                self.fumadores[destino].estado = EstadoHilo.EJECUTANDO
            if anterior is None:
                return f"la CPU pasa a {destino.etiqueta}"
            return f"la CPU pasa de «{anterior.etiqueta}» a «{destino.etiqueta}»"

        self._encolar(destino, "Cambio de contexto", TipoEvento.CONTEXTO, ejecutar)

    # --- operaciones del protocolo (semáforos) ---

    def _p_agente_inicial(self) -> str:
        sem = self.gestor.turno_agente
        adquirio = sem.intentar_p(Participante.AGENTE)
        self.agente.accion = "Inicia la ronda"
        return (
            f"P(turno_agente): adquiere el turno (valor={sem.valor})"
            if adquirio
            else "P(turno_agente): se bloquea"
        )

    def _p_agente_final(self) -> str:
        self.gestor.turno_agente.intentar_p(Participante.AGENTE)
        self.agente.estado = EstadoHilo.BLOQUEADO
        self.agente.accion = "Esperando fin de la ronda"
        return "P(turno_agente): se bloquea hasta que el fumador termine"

    def _v_turno_fumador(self, f: Participante) -> str:
        despertado = self.gestor.turno_fumador[f].v()
        self.estadisticas.registrar_habilitacion(f)
        self.agente.accion = f"Señala a {f.etiqueta}"
        extra = "despierta su hilo" if despertado is not None else "habilita su hilo"
        return f"V(turno_{f.value}): {extra} («{f.etiqueta}»)"

    def _p_mutex(self, p: Participante) -> str:
        ok = self.gestor.mutex_mesa.intentar_p(p)
        self._fijar_accion(p, "Entra a la sección crítica")
        return "P(mutex_mesa): entra a la sección crítica" if ok else "P(mutex_mesa): bloqueado"

    def _v_mutex(self, p: Participante) -> str:
        self.gestor.mutex_mesa.v()
        self._fijar_accion(p, "Sale de la sección crítica")
        return "V(mutex_mesa): libera la sección crítica"

    def _v_turno_agente(self, f: Participante) -> str:
        self.gestor.turno_agente.v()
        self.estadisticas.registrar_habilitacion(Participante.AGENTE)
        self.fumadores[f].cigarros += 1
        self.estadisticas.registrar_cigarro(f)
        self.estadisticas.rondas_completadas += 1
        self.fumadores[f].accion = "Notifica al agente"
        return "V(turno_agente): señaliza fin de ronda y despierta al agente"

    def _p_turno_fumador_final(self, f: Participante) -> str:
        self.gestor.turno_fumador[f].intentar_p(f)
        self.fumadores[f].estado = EstadoHilo.BLOQUEADO
        self.fumadores[f].accion = "Esperando turno"
        return "P(turno_fumador): se bloquea esperando la próxima ronda"

    def _fijar_accion(self, p: Participante, accion: str) -> None:
        if p is Participante.AGENTE:
            self.agente.accion = accion
        else:
            self.fumadores[p].accion = accion

    # ------------------------------------------------------------- planificación

    def _planificar_ronda(self) -> None:
        r = self._rondas_planificadas + 1
        self._rondas_planificadas = r
        self.agente.ronda_actual = r
        i1, i2 = self.agente.seleccionar()
        f = fumador_de(faltante((i1, i2)))
        es_ultima = r >= self.limite

        if r == 1:
            self._encolar_contexto(Participante.AGENTE)
            self._encolar(Participante.AGENTE, "P(turno_agente)", TipoEvento.SEMAFORO, self._p_agente_inicial)

        # --- Agente coloca la combinación ---
        self._encolar(Participante.AGENTE, "P(mutex_mesa)", TipoEvento.SEMAFORO,
                      lambda: self._p_mutex(Participante.AGENTE))
        self._encolar_colocacion(i1)
        self._encolar_colocacion(i2)
        self._encolar(Participante.AGENTE, "V(mutex_mesa)", TipoEvento.SEMAFORO,
                      lambda: self._v_mutex(Participante.AGENTE))
        self._encolar(Participante.AGENTE, f"V(turno_{f.value})", TipoEvento.SEMAFORO,
                      lambda: self._v_turno_fumador(f))
        self._encolar(Participante.AGENTE, "P(turno_agente)", TipoEvento.SEMAFORO,
                      self._p_agente_final)
        self._encolar_contexto(f)

        # --- El fumador correcto consume ---
        self._encolar(f, "P(mutex_mesa)", TipoEvento.SEMAFORO, lambda: self._p_mutex(f))
        self._encolar_consumo(f, i1)
        self._encolar_consumo(f, i2)
        self._encolar(f, "V(mutex_mesa)", TipoEvento.SEMAFORO, lambda: self._v_mutex(f))
        self._encolar_fabricacion(f, i1, i2)
        self._encolar(f, "Fuma", TipoEvento.TRANSICION, lambda: self._fumar(f))
        self._encolar(f, "V(turno_agente)", TipoEvento.SEMAFORO, lambda: self._v_turno_agente(f))

        if es_ultima:
            self._planificar_terminacion()
        else:
            self._encolar(f, "P(turno_fumador)", TipoEvento.SEMAFORO,
                          lambda: self._p_turno_fumador_final(f))
            self._encolar_contexto(Participante.AGENTE)

    def _encolar_colocacion(self, ing: Ingrediente) -> None:
        def ejecutar() -> str:
            self.mesa.colocar(ing)
            self.agente.accion = f"Coloca {ing.etiqueta}"
            return f"coloca {ing.etiqueta} en la mesa"
        self._encolar(Participante.AGENTE, "Coloca ingrediente", TipoEvento.INGREDIENTE, ejecutar)

    def _encolar_consumo(self, f: Participante, ing: Ingrediente) -> None:
        def ejecutar() -> str:
            self.mesa.tomar(ing)
            self.fumadores[f].accion = f"Toma {ing.etiqueta}"
            return f"toma {ing.etiqueta} de la mesa"
        self._encolar(f, "Toma ingrediente", TipoEvento.INGREDIENTE, ejecutar)

    def _encolar_fabricacion(self, f: Participante, i1: Ingrediente, i2: Ingrediente) -> None:
        propio = f.ingrediente_propio
        def ejecutar() -> str:
            self.fumadores[f].accion = "Fabrica cigarrillo"
            return f"combina {propio.etiqueta} + {i1.etiqueta} + {i2.etiqueta}"
        self._encolar(f, "Fabrica cigarrillo", TipoEvento.TRANSICION, ejecutar)

    def _fumar(self, f: Participante) -> str:
        self.fumadores[f].accion = "Fuma"
        return "consume el cigarrillo (trabajo simulado)"

    def _planificar_terminacion(self) -> None:
        def terminar_agente() -> str:
            self.agente.estado = EstadoHilo.TERMINADO
            self.agente.accion = "Finalizado"
            return "el agente finaliza (límite de rondas alcanzado)"
        self._encolar(Participante.AGENTE, "Termina", TipoEvento.TRANSICION, terminar_agente)

        def fabricar_terminador(fumador: Participante) -> Callable[[], str]:
            def ejecutar() -> str:
                self.fumadores[fumador].estado = EstadoHilo.TERMINADO
                self.fumadores[fumador].accion = "Finalizado"
                return f"{fumador.etiqueta} finaliza"
            return ejecutar

        for fumador in FUMADORES:
            self._encolar(fumador, "Termina", TipoEvento.TRANSICION, fabricar_terminador(fumador))

        def fin() -> str:
            return (
                f"total: {self.estadisticas.rondas_completadas} rondas y "
                f"{self.estadisticas.total_cigarros} cigarrillos"
            )
        self._encolar(None, "Simulación finalizada", TipoEvento.SISTEMA, fin)
        self._terminacion_planificada = True
