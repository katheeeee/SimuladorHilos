"""Pruebas del modo de análisis y de su aislamiento respecto del motor."""

from __future__ import annotations

import unittest

from simulador.model.participante import Participante
from simulador.simulation.modo_incorrecto import Diagnostico, ModoAnalisis, VarianteAnalisis
from simulador.simulation.motor import MotorSimulacion


class ModoAnalisisTest(unittest.TestCase):
    def test_carrera_detecta_actualizacion_perdida(self) -> None:
        modo = ModoAnalisis(VarianteAnalisis.CARRERA)
        eventos = modo.ejecutar_todo()
        self.assertEqual(modo.diagnostico, Diagnostico.CARRERA)
        self.assertTrue(any("actualización perdida" in e.resultado for e in eventos))

    def test_interbloqueo_detectado(self) -> None:
        modo = ModoAnalisis(VarianteAnalisis.INTERBLOQUEO)
        eventos = modo.ejecutar_todo()
        self.assertEqual(modo.diagnostico, Diagnostico.INTERBLOQUEO)
        self.assertTrue(any("interbloqueo" in e.resultado.lower() for e in eventos))

    def test_inanicion_detectada(self) -> None:
        modo = ModoAnalisis(VarianteAnalisis.INANICION, rondas=5)
        eventos = modo.ejecutar_todo()
        self.assertEqual(modo.diagnostico, Diagnostico.INANICION)
        # Los fumadores con tabaco y papel nunca despiertan.
        despiertos = {
            e.participante for e in eventos
            if e.operacion == "Despierta y fuma"
        }
        self.assertNotIn(Participante.FUMADOR_TABACO, despiertos)
        self.assertNotIn(Participante.FUMADOR_PAPEL, despiertos)

    def test_reinicio_del_modo(self) -> None:
        modo = ModoAnalisis(VarianteAnalisis.CARRERA)
        modo.ejecutar_todo()
        modo.reiniciar()
        self.assertEqual(modo.diagnostico, Diagnostico.NINGUNO)
        self.assertFalse(modo.terminado)
        self.assertGreater(len(modo.ejecutar_todo()), 0)

    def test_aislado_del_motor_correcto(self) -> None:
        motor = MotorSimulacion(limite_rondas=3, semilla=1)
        motor.ejecutar_hasta_terminar()
        antes = motor.estadisticas.total_cigarros
        modo = ModoAnalisis(VarianteAnalisis.INTERBLOQUEO)
        modo.ejecutar_todo()
        # El modo de análisis no comparte estado con el motor correcto.
        self.assertEqual(motor.estadisticas.total_cigarros, antes)
        self.assertEqual(motor.mesa.contenido, frozenset())


if __name__ == "__main__":
    unittest.main()
