"""Pruebas del motor determinista y de la consistencia de la mesa."""

from __future__ import annotations

import unittest

from simulador.model.evento import TipoEvento
from simulador.model.ingredientes import TODOS, faltante
from simulador.model.participante import FUMADORES, Participante
from simulador.simulation.motor import MotorSimulacion


class MotorBasicoTest(unittest.TestCase):
    def test_paso_unico_avanza_una_transicion(self) -> None:
        motor = MotorSimulacion(limite_rondas=2, semilla=7)
        inicial = motor.paso_actual
        motor.paso()
        self.assertEqual(motor.paso_actual, inicial + 1)

    def test_cada_ronda_produce_un_cigarrillo(self) -> None:
        for limite in (1, 2, 5, 8):
            with self.subTest(limite=limite):
                motor = MotorSimulacion(limite_rondas=limite, semilla=100 + limite)
                motor.ejecutar_hasta_terminar()
                self.assertTrue(motor.terminado)
                self.assertEqual(motor.estadisticas.rondas_completadas, limite)
                self.assertEqual(motor.estadisticas.total_cigarros, limite)

    def test_determinismo_con_misma_semilla(self) -> None:
        a = MotorSimulacion(limite_rondas=4, semilla=42)
        b = MotorSimulacion(limite_rondas=4, semilla=42)
        ea = [(e.operacion, e.resultado) for e in a.ejecutar_hasta_terminar()]
        eb = [(e.operacion, e.resultado) for e in b.ejecutar_hasta_terminar()]
        self.assertEqual(ea, eb)

    def test_semillas_distintas_pueden_diferir(self) -> None:
        secuencias = set()
        for semilla in range(6):
            motor = MotorSimulacion(limite_rondas=3, semilla=semilla)
            eventos = motor.ejecutar_hasta_terminar()
            secuencias.add(tuple(e.resultado for e in eventos if e.tipo is TipoEvento.INGREDIENTE))
        self.assertGreater(len(secuencias), 1)

    def test_cada_turno_fuma_un_fumador_distinto(self) -> None:
        motor = MotorSimulacion(limite_rondas=6, semilla=42)
        eventos = motor.ejecutar_hasta_terminar()
        fumadores = [e.participante for e in eventos if e.operacion == "Fuma"]
        self.assertEqual(len(fumadores), 6)
        for anterior, actual in zip(fumadores, fumadores[1:]):
            self.assertIsNot(
                anterior, actual, "en cada turno debe fumar un fumador distinto"
            )
        for inicio in range(0, len(fumadores), len(FUMADORES)):
            self.assertEqual(
                set(fumadores[inicio:inicio + len(FUMADORES)]),
                set(FUMADORES),
                "cada bloque de tres rondas debe cubrir a los tres fumadores",
            )

    def test_la_semilla_cambia_el_fumador_inicial(self) -> None:
        primeros = set()
        for semilla in range(len(FUMADORES)):
            motor = MotorSimulacion(limite_rondas=1, semilla=semilla)
            eventos = motor.ejecutar_hasta_terminar()
            primero = next(e.participante for e in eventos if e.operacion == "Fuma")
            primeros.add(primero)
        self.assertEqual(len(primeros), len(FUMADORES))


class ConsistenciaTest(unittest.TestCase):
    def test_solo_el_fumador_correcto_consume(self) -> None:
        for semilla in range(8):
            with self.subTest(semilla=semilla):
                motor = MotorSimulacion(limite_rondas=5, semilla=semilla)
                eventos = motor.ejecutar_hasta_terminar()
                self._validar_consumos(eventos)

    def test_agente_no_coloca_sobre_mesa_no_vacia(self) -> None:
        motor = MotorSimulacion(limite_rondas=6, semilla=3)
        eventos = motor.ejecutar_hasta_terminar()
        mesa: set = set()
        for evento in eventos:
            if evento.operacion == "Coloca ingrediente":
                # El agente coloca de a uno, pero nunca inicia una combinación
                # nueva mientras quede una sin consumir (a lo sumo 1 ingrediente).
                self.assertLessEqual(len(mesa), 1, "el agente inició ronda con la mesa ocupada")
                ing = self._ingrediente_del_texto(evento.resultado, "coloca")
                mesa.add(ing)
            elif evento.operacion == "Toma ingrediente":
                ing = self._ingrediente_del_texto(evento.resultado, "toma")
                self.assertIn(ing, mesa)
                mesa.discard(ing)
        self.assertEqual(mesa, set())

    def test_estado_de_la_mesa_siempre_valido(self) -> None:
        motor = MotorSimulacion(limite_rondas=6, semilla=11)
        while (evento := motor.paso()) is not None:
            contenido = motor.mesa.contenido
            self.assertLessEqual(len(contenido), 2)
            # En todo momento la mesa contiene a lo sumo dos ingredientes distintos.

    # ------------------------------------------------------------------ apoyo

    def _ingrediente_del_texto(self, texto: str, verbo: str):
        for ingrediente in TODOS:
            if ingrediente.etiqueta in texto:
                return ingrediente
        raise AssertionError(f"No se reconoce ingrediente en «{texto}»")

    def _validar_consumos(self, eventos) -> None:
        colocados: list = []
        mesa: set = set()
        consumidos: list = []
        for evento in eventos:
            if evento.operacion == "Coloca ingrediente":
                colocados.append(self._ingrediente_del_texto(evento.resultado, "coloca"))
                mesa.add(self._ingrediente_del_texto(evento.resultado, "coloca"))
            elif evento.operacion == "Toma ingrediente":
                ing = self._ingrediente_del_texto(evento.resultado, "toma")
                consumidos.append(ing)
                mesa.discard(ing)
                if not mesa:  # la combinación se consumió por completo
                    self.assertEqual(len(colocados), 2)
                    self.assertEqual(set(colocados), set(consumidos))
                    fumador = evento.participante
                    self.assertIsNotNone(fumador)
                    self.assertNotIn(fumador.ingrediente_propio, consumidos)
                    self.assertEqual(
                        fumador.ingrediente_propio,
                        faltante((colocados[0], colocados[1])),
                        "consumió un fumador distinto del que posee el ingrediente faltante",
                    )
                    colocados, consumidos = [], []


if __name__ == "__main__":
    unittest.main()
