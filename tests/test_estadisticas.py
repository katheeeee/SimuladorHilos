"""Pruebas de que las estadísticas coinciden con los eventos registrados."""

from __future__ import annotations

import unittest

from simulador.model.evento import TipoEvento
from simulador.model.participante import FUMADORES, Participante
from simulador.model.estadisticas import Estadisticas
from simulador.simulation.motor import MotorSimulacion


class EstadisticasTest(unittest.TestCase):
    def test_cigarros_coinciden_con_eventos_de_fabricacion(self) -> None:
        motor = MotorSimulacion(limite_rondas=6, semilla=8)
        eventos = motor.ejecutar_hasta_terminar()
        fabricados = [e.participante for e in eventos if e.operacion == "Fabrica cigarrillo"]
        self.assertEqual(len(fabricados), 6)
        for fumador in FUMADORES:
            self.assertEqual(
                motor.estadisticas.cigarros_por_fumador[fumador],
                fabricados.count(fumador),
            )
        self.assertEqual(motor.estadisticas.total_cigarros, 6)
        self.assertEqual(motor.estadisticas.rondas_completadas, 6)

    def test_cambios_de_contexto_coinciden(self) -> None:
        motor = MotorSimulacion(limite_rondas=5, semilla=4)
        eventos = motor.ejecutar_hasta_terminar()
        contextos = sum(1 for e in eventos if e.tipo is TipoEvento.CONTEXTO)
        self.assertEqual(motor.estadisticas.cambios_contexto, contextos)

    def test_habilitaciones_coinciden_con_senales(self) -> None:
        motor = MotorSimulacion(limite_rondas=5, semilla=12)
        eventos = motor.ejecutar_hasta_terminar()
        # El agente es habilitado una vez por ronda (V(turno_agente) del fumador).
        self.assertEqual(motor.estadisticas.habilitaciones[Participante.AGENTE], 5)
        # Cada fumador es habilitado tantas veces como V(turno_<f>) lo señala.
        for fumador in FUMADORES:
            senales = sum(
                1 for e in eventos
                if e.operacion == f"V(turno_{fumador.value})"
            )
            self.assertEqual(motor.estadisticas.habilitaciones[fumador], senales)

    def test_reset_de_estadisticas(self) -> None:
        stats = Estadisticas()
        stats.registrar_cigarro(Participante.FUMADOR_TABACO)
        stats.registrar_habilitacion(Participante.AGENTE)
        stats.registrar_cambio_contexto()
        stats.rondas_completadas = 3
        stats.reiniciar()
        self.assertEqual(stats.rondas_completadas, 0)
        self.assertEqual(stats.total_cigarros, 0)
        self.assertEqual(stats.habilitaciones[Participante.AGENTE], 0)
        self.assertEqual(stats.cambios_contexto, 0)


if __name__ == "__main__":
    unittest.main()
