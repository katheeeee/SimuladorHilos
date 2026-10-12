"""Pruebas del backend de hilos reales y de su cierre limpio."""

from __future__ import annotations

import threading
import time
import unittest

from simulador.model.evento import TipoEvento
from simulador.model.participante import FUMADORES
from simulador.simulation.concurrente import SimulacionConcurrente


def esperar_rondas(sim: SimulacionConcurrente, objetivo: int, timeout: float = 15.0) -> None:
    inicio = time.monotonic()
    while time.monotonic() - inicio < timeout:
        if sim.rondas_completadas >= objetivo:
            return
        time.sleep(0.01)
    raise AssertionError(f"No se alcanzaron {objetivo} rondas en {timeout}s")


class ConcurrenteTest(unittest.TestCase):
    def test_termina_por_limite_de_rondas(self) -> None:
        sim = SimulacionConcurrente(limite_rondas=4)
        sim.iniciar()
        try:
            esperar_rondas(sim, 4)
        finally:
            vivos = sim.detener_y_unir(2.0)
        self.assertEqual(vivos, [], f"hilos aún vivos: {vivos}")
        self.assertEqual(sum(sim.cigarros_por_fumador().values()), 4)
        self.assertFalse(sim.activa)

    def test_detener_inmediatamente_no_deja_hilos(self) -> None:
        sim = SimulacionConcurrente(limite_rondas=50)
        sim.iniciar()
        vivos = sim.detener_y_unir(3.0)
        self.assertEqual(vivos, [])
        self.assertFalse(any(t.is_alive() for t in threading.enumerate() if t.name in {"agente"}))
        for f in FUMADORES:
            self.assertFalse(any(t.is_alive() for t in threading.enumerate() if t.name == f.value))

    def test_reinicio_no_deja_hilos_huerfanos(self) -> None:
        sim = SimulacionConcurrente(limite_rondas=3)
        for _ in range(3):
            sim.iniciar()
            esperar_rondas(sim, 3)
            vivos = sim.detener_y_unir(2.0)
            self.assertEqual(vivos, [])

    def test_eventos_registrados_marcados_por_tipo(self) -> None:
        sim = SimulacionConcurrente(limite_rondas=3)
        sim.iniciar()
        try:
            esperar_rondas(sim, 3)
        finally:
            sim.detener_y_unir(2.0)
        eventos = sim.registro.eventos()
        self.assertTrue(any(e.tipo is TipoEvento.INGREDIENTE for e in eventos))
        self.assertTrue(any(e.tipo is TipoEvento.SEMAFORO for e in eventos))
        # La mesa queda vacía al terminar (cada combinación fue consumida).
        self.assertEqual(sim.instantanea()["mesa"], frozenset())

    def test_el_fumador_habilitado_rota_sin_repetir(self) -> None:
        sim = SimulacionConcurrente(limite_rondas=6)
        sim.iniciar()
        try:
            esperar_rondas(sim, 6)
        finally:
            vivos = sim.detener_y_unir(3.0)
        self.assertEqual(vivos, [])
        señalados = []
        for e in sim.registro.eventos():
            if e.operacion.startswith("V(turno_fumador_"):
                valor = e.operacion[len("V(turno_"):-1]
                señalados.append(next(f for f in FUMADORES if f.value == valor))
        self.assertEqual(len(señalados), 6)
        for anterior, actual in zip(señalados, señalados[1:]):
            self.assertIsNot(anterior, actual)


if __name__ == "__main__":
    unittest.main()
