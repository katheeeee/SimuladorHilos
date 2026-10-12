"""Prueba de humo de la interfaz (sin pantalla, plataforma «offscreen»).

Se omite automáticamente si PySide6 no está instalado, de modo que el resto de
la batería de pruebas sigue funcionando en entornos sin Qt.
"""

from __future__ import annotations

import os
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:  # pragma: no cover - depende del entorno
    from PySide6.QtWidgets import QApplication

    from simulador.simulation.modo_incorrecto import Diagnostico
    from simulador.ui.app import VentanaPrincipal

    _QT_DISPONIBLE = True
except Exception:  # pragma: no cover
    _QT_DISPONIBLE = False


@unittest.skipUnless(_QT_DISPONIBLE, "PySide6 no disponible")
class UISmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.ventana = VentanaPrincipal()

    def tearDown(self) -> None:
        self.ventana.close()
        self.app.processEvents()

    def _bombear(self, segundos: float) -> None:
        fin = time.monotonic() + segundos
        while time.monotonic() < fin:
            self.app.processEvents()
            time.sleep(0.01)

    def test_avance_manual_y_reinicio(self) -> None:
        for _ in range(12):
            self.ventana._siguiente()
        self.assertGreater(self.ventana.motor.paso_actual, 0)
        self.ventana._reiniciar()
        self.assertEqual(self.ventana.motor.ronda_actual, 0)
        self.assertEqual(self.ventana.motor.paso_actual, 0)

    def test_ejecucion_automatica_termina(self) -> None:
        self.ventana._ejecutar()
        # Se invoca el avance automático como lo haría el temporizador, sin
        # depender del tiempo real de pared.
        for _ in range(600):
            if self.ventana.motor.terminado:
                break
            self.ventana._avanzar_auto()
        self.assertTrue(self.ventana.motor.terminado)
        self.assertEqual(self.ventana.motor.estadisticas.rondas_completadas, 6)
        self.assertTrue(self.ventana.controles.btn_ejecutar.isEnabled())

    def test_modo_hilos_reales_se_detiene_sin_huerfanos(self) -> None:
        self.ventana.controles.chk_hilos.setChecked(True)
        self.ventana._iniciar_hilos()
        self._bombear(1.5)
        self.ventana._detener_hilos()
        self.assertIsNone(self.ventana._concurrente)

    def test_modo_analisis_marca_patologia(self) -> None:
        self.ventana._iniciar_analisis("carrera")
        for _ in range(8):
            self.ventana._avanzar_analisis()
        self._bombear(0.3)
        self.assertIsNotNone(self.ventana._analisis)
        self.assertEqual(self.ventana._analisis.diagnostico, Diagnostico.CARRERA)
        self.ventana._detener_analisis()
        self.assertIsNone(self.ventana._analisis)


if __name__ == "__main__":
    unittest.main()
