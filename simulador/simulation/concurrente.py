"""Backend con hilos **reales** para el problema de los fumadores.

Este modo usa ``threading.Thread``, ``threading.Semaphore`` y ``threading.Lock``
reales: la sincronización la lleva a cabo el planificador del sistema
operativo. Como consecuencia, el orden de los eventos **no es determinista** y
solo se puede observar de forma aproximada. Se ofrece como demostración de los
mecanismos reales, separado del motor determinista que alimenta la interfaz.

Los hilos escriben en un :class:`~simulador.registro.registro.RegistroEventos`
a prueba de concurrencia. La interfaz nunca toca widgets desde estos hilos:
consume el registro mediante un temporizador en el hilo principal.

Para trato justo, el agente habilita a los fumadores por **rotación** (cada
ronda un fumador distinto), aunque el orden temporal entre ellos siga
dependiendo del planificador del sistema.
"""

from __future__ import annotations

import threading

from ..model.evento import Evento, TipoEvento
from ..model.ingredientes import TODOS
from ..model.participante import FUMADORES, Participante
from ..registro.registro import RegistroEventos
from ..synchronization.mecanismos import Parada, SemaforoReal, mutex

__all__ = ["SimulacionConcurrente"]


class SimulacionConcurrente:
    """Ejecuta el protocolo correcto con hilos reales, acotado por rondas."""

    def __init__(self, limite_rondas: int = 5, capacidad_log: int = 3000) -> None:
        if limite_rondas < 1:
            raise ValueError("El límite de rondas debe ser al menos 1")
        self.limite = limite_rondas
        self.registro = RegistroEventos(capacidad_log)

        self._turno_agente = SemaforoReal("turno_agente", 1)
        self._turno_fumador = {f: SemaforoReal(f"turno_{f.value}", 0) for f in FUMADORES}
        self._mutex = mutex()
        self._parada = Parada()

        self._mesa: set = set()
        self._cigarros: dict[Participante, int] = {f: 0 for f in FUMADORES}
        self._rondas = 0
        self._paso = 0
        self._rotacion = 0

        self._hilos: list[threading.Thread] = []
        self._iniciada = False

    # ------------------------------------------------------------------ estado

    @property
    def iniciada(self) -> bool:
        return self._iniciada

    @property
    def activa(self) -> bool:
        return self._iniciada and any(t.is_alive() for t in self._hilos)

    @property
    def rondas_completadas(self) -> int:
        with self._mutex:
            return self._rondas

    def cigarros_por_fumador(self) -> dict[Participante, int]:
        with self._mutex:
            return dict(self._cigarros)

    def instantanea(self) -> dict:
        """Estado observable para la interfaz (sin tocar la UI)."""
        with self._mutex:
            mesa = frozenset(self._mesa)
            rondas = self._rondas
            cigarros = dict(self._cigarros)
        return {
            "mesa": mesa,
            "rondas": rondas,
            "cigarros": cigarros,
            "semaforos": (
                (self._turno_agente.nombre, self._turno_agente.valor_estimado),
                *((s.nombre, s.valor_estimado) for s in self._turno_fumador.values()),
            ),
            "activa": self.activa,
        }

    # ---------------------------------------------------------------- registro

    def _evento(self, participante: Participante | None, operacion: str, resultado: str, tipo: TipoEvento) -> None:
        with self._mutex:
            self._paso += 1
            paso = self._paso
        self.registro.agregar(Evento(paso, participante, operacion, resultado, tipo))

    # ------------------------------------------------------------------ hilos

    def _ciclo_agente(self) -> None:
        while self._parada.activa():
            self._turno_agente.p()
            if not self._parada.activa():
                break
            with self._mutex:
                terminado = self._rondas >= self.limite
            if terminado:
                # Se esperó a que la ronda anterior terminara antes de decidir,
                # por lo que no se coloca una combinación de más.
                self._turno_agente.v()
                break
            f = FUMADORES[self._rotacion % len(FUMADORES)]
            self._rotacion += 1
            propio = f.ingrediente_propio
            par = tuple(i for i in TODOS if i is not propio)
            with self._mutex:
                self._mesa.update(par)
            self._evento(
                Participante.AGENTE,
                "Coloca ingredientes",
                f"coloca {par[0].etiqueta} y {par[1].etiqueta} en la mesa",
                TipoEvento.INGREDIENTE,
            )
            self._evento(
                Participante.AGENTE,
                f"V(turno_{f.value})",
                f"señaliza al hilo «{f.etiqueta}»",
                TipoEvento.SEMAFORO,
            )
            self._turno_fumador[f].v()
        self._evento(Participante.AGENTE, "Termina", "el agente finaliza", TipoEvento.TRANSICION)

    def _ciclo_fumador(self, f: Participante) -> None:
        propio = f.ingrediente_propio
        while self._parada.activa():
            self._turno_fumador[f].p()
            if not self._parada.activa():
                break
            with self._mutex:
                necesarios = [i for i in TODOS if i != propio and i in self._mesa]
                for i in necesarios:
                    self._mesa.discard(i)
            detalle = " y ".join(i.etiqueta for i in necesarios) or "sin ingredientes"
            self._evento(f, "Toma ingredientes", f"toma {detalle} de la mesa", TipoEvento.INGREDIENTE)
            self._evento(f, "Fabrica cigarrillo", "combina los tres ingredientes", TipoEvento.TRANSICION)
            with self._mutex:
                self._cigarros[f] += 1
                self._rondas += 1
            self._evento(f, "Fuma", "consume el cigarrillo (trabajo real simulado)", TipoEvento.TRANSICION)
            self._evento(f, "V(turno_agente)", "señaliza fin de ronda", TipoEvento.SEMAFORO)
            self._turno_agente.v()
        self._evento(f, "Termina", f"{f.etiqueta} finaliza", TipoEvento.TRANSICION)

    # --------------------------------------------------------------- controles

    def iniciar(self) -> None:
        """Lanza los hilos. No hace nada si ya hay hilos vivos."""
        if self.activa:
            return
        self._parada.limpiar()
        self._iniciada = True
        self._hilos = [threading.Thread(target=self._ciclo_agente, name="agente", daemon=True)]
        for f in FUMADORES:
            self._hilos.append(
                threading.Thread(target=self._ciclo_fumador, args=(f,), name=f.value, daemon=True)
            )
        for hilo in self._hilos:
            hilo.start()

    def detener(self) -> None:
        """Señala la parada y desbloquea a los hilos dormidos."""
        self._parada.detener()
        self._turno_agente.v()
        for sem in self._turno_fumador.values():
            sem.v()

    def unir(self, timeout: float = 2.0) -> list[str]:
        """Espera a que terminen los hilos. Devuelve los que sigan vivos."""
        for hilo in list(self._hilos):
            hilo.join(timeout)
        vivos = [hilo.name for hilo in self._hilos if hilo.is_alive()]
        self._hilos = [hilo for hilo in self._hilos if hilo.is_alive()]
        if not self._hilos:
            self._iniciada = False
        return vivos

    def detener_y_unir(self, timeout: float = 2.0) -> list[str]:
        """Detiene y une los hilos; no debe dejar hilos huérfanos."""
        self.detener()
        return self.unir(timeout)
