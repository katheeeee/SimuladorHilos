"""Pruebas de los semáforos modelados y de los invariantes de sincronización."""

from __future__ import annotations

import unittest

from simulador.model.evento import TipoEvento
from simulador.model.participante import FUMADORES, Participante
from simulador.simulation.motor import MotorSimulacion
from simulador.synchronization.semaforos import Semaforo


class SemaforoModeladoTest(unittest.TestCase):
    def test_p_sobre_cero_bloquea(self) -> None:
        sem = Semaforo("s", 0)
        self.assertFalse(sem.intentar_p(Participante.FUMADOR_TABACO))
        self.assertEqual(sem.valor, 0)
        self.assertEqual(sem.bloqueados, (Participante.FUMADOR_TABACO,))

    def test_v_despierta_exactamente_a_uno(self) -> None:
        sem = Semaforo("s", 0)
        sem.intentar_p(Participante.FUMADOR_TABACO)
        sem.intentar_p(Participante.FUMADOR_PAPEL)
        despertado = sem.v()
        self.assertEqual(despertado, Participante.FUMADOR_TABACO)
        self.assertEqual(sem.valor, 0)  # el contador no sube al despertar
        self.assertEqual(sem.bloqueados, (Participante.FUMADOR_PAPEL,))

    def test_v_sin_espera_incrementa(self) -> None:
        sem = Semaforo("s", 0)
        self.assertIsNone(sem.v())
        self.assertEqual(sem.valor, 1)
        self.assertTrue(sem.intentar_p(Participante.AGENTE))
        self.assertEqual(sem.valor, 0)

    def test_reiniciar(self) -> None:
        sem = Semaforo("s", 1)
        sem.intentar_p(Participante.AGENTE)
        sem.reiniciar()
        self.assertEqual(sem.valor, 1)
        self.assertEqual(sem.bloqueados, ())


class SincronizacionMotorTest(unittest.TestCase):
    def test_invariantes_de_semaforos_durante_la_ejecucion(self) -> None:
        motor = MotorSimulacion(limite_rondas=6, semilla=5)
        while (evento := motor.paso()) is not None:
            for sem in motor.gestor.semaforos:
                self.assertGreaterEqual(sem.valor, 0, f"{sem.nombre} con valor negativo")
                if sem.esperando:
                    self.assertEqual(sem.valor, 0, f"{sem.nombre} con espera y contador > 0")

    def test_mutex_regresa_a_libre(self) -> None:
        motor = MotorSimulacion(limite_rondas=4, semilla=9)
        motor.ejecutar_hasta_terminar()
        self.assertEqual(motor.gestor.mutex_mesa.valor, 1)
        self.assertEqual(motor.gestor.mutex_mesa.bloqueados, ())

    def test_solo_un_fumador_es_habilitado_por_ronda(self) -> None:
        motor = MotorSimulacion(limite_rondas=7, semilla=21)
        eventos = motor.ejecutar_hasta_terminar()
        habilitaciones = [
            e for e in eventos
            if e.operacion.startswith("V(turno_") and e.participante in FUMADORES
        ]
        # 7 rondas → 7 señalizaciones a fumadores (una por ronda).
        self.assertEqual(len(habilitaciones), 7)
        for evento in habilitaciones:
            self.assertIn(evento.participante, FUMADORES)
            self.assertEqual(evento.tipo, TipoEvento.SEMAFORO)

    def test_agente_espera_hasta_fin_de_ronda(self) -> None:
        motor = MotorSimulacion(limite_rondas=5, semilla=2)
        eventos = motor.ejecutar_hasta_terminar()
        notificaciones = [i for i, e in enumerate(eventos) if e.operacion == "V(turno_agente)"]
        self.assertEqual(len(notificaciones), 5)
        # Tras cada notificación (salvo la última ronda), el agente solo puede
        # volver a colocar tras recuperar la CPU en un cambio de contexto.
        for indice in notificaciones[:-1]:
            siguientes = eventos[indice + 1:]
            contextos = [
                e.participante for e in siguientes
                if e.tipo is TipoEvento.CONTEXTO and e.participante is Participante.AGENTE
            ]
            self.assertTrue(contextos, "el agente reanudó sin cambio de contexto")


if __name__ == "__main__":
    unittest.main()
