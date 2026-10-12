"""Ventana principal: une el motor de simulación con la interfaz Qt.

Reglas de seguridad de hilos:

* El modelo determinista se ejecuta **en el hilo principal** de Qt mediante un
  :class:`QTimer`; cada pulsación de «Siguiente paso» ejecuta una sola transición.
* El backend de hilos reales corre en hilos de trabajo y **nunca** toca widgets:
  escribe en un registro a prueba de concurrencia que un temporizador del hilo
  principal consume.
* El modo de análisis usa su propio objeto aislado y no comparte estado con el
  motor correcto.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from ..simulation.concurrente import SimulacionConcurrente
from ..simulation.modo_incorrecto import ModoAnalisis, VarianteAnalisis
from ..simulation.motor import MotorSimulacion
from .controles import Controles
from .escena import EscenarioVisual
from .panel_eventos import PanelEventos
from .panel_sincronizacion import PanelSincronizacion
from .panel_superior import PanelSuperior
from .panel_variables import PanelVariables
from . import theme

MODO_DETERMINISTA = "Modelo determinista (paso a paso)"
MODO_HILOS = "Hilos reales (demostración no determinista)"
MODO_HILOS_FIN = "Hilos reales (finalizado)"
MODO_ANALISIS = "Análisis ilustrativo (aislado)"


class VentanaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Simulador de Concurrencia · Problema de los Fumadores")
        self.resize(1440, 960)
        self.setMinimumSize(1180, 800)

        self.motor = MotorSimulacion(limite_rondas=6)
        self._modo = MODO_DETERMINISTA
        self._concurrente: SimulacionConcurrente | None = None
        self._analisis: ModoAnalisis | None = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._avanzar_auto)
        self._timer_hilos = QTimer(self)
        self._timer_hilos.timeout.connect(self._poll_hilos)
        self._timer_analisis = QTimer(self)
        self._timer_analisis.timeout.connect(self._avanzar_analisis)

        self._construir_interfaz()
        self._conectar_controles()
        self._actualizar()

    # ------------------------------------------------------------- construcción

    def _construir_interfaz(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(12, 12, 12, 12)
        raiz.setSpacing(10)

        self.panel_superior = PanelSuperior()
        raiz.addWidget(self.panel_superior)

        self.escenario = EscenarioVisual()
        raiz.addWidget(self.escenario, 8)

        fila_inferior = QWidget()
        inferior = QHBoxLayout(fila_inferior)
        inferior.setContentsMargins(0, 0, 0, 0)
        inferior.setSpacing(10)

        self.panel_eventos = PanelEventos()
        self.panel_sincro = PanelSincronizacion()
        self.panel_variables = PanelVariables()
        inferior.addWidget(self.panel_eventos, 48)
        inferior.addWidget(self.panel_sincro, 22)
        inferior.addWidget(self.panel_variables, 30)
        raiz.addWidget(fila_inferior, 2)

        self.controles = Controles()
        raiz.addWidget(self.controles)

        self.setStyleSheet(theme.QSS)

    def _conectar_controles(self) -> None:
        self.controles.siguiente.connect(self._siguiente)
        self.controles.ejecutar.connect(self._ejecutar)
        self.controles.pausar.connect(self._pausar)
        self.controles.reiniciar.connect(self._reiniciar)
        self.controles.velocidad.connect(self._cambiar_velocidad)
        self.controles.limite.connect(self._cambiar_limite)
        self.controles.modo_hilos.connect(self._toggle_modo_hilos)
        self.controles.iniciar_hilos.connect(self._iniciar_hilos)
        self.controles.detener_hilos.connect(self._detener_hilos)
        self.controles.analizar.connect(self._iniciar_analisis)
        self.controles.detener_analisis.connect(self._detener_analisis)

    # ------------------------------------------------------- modelo determinista

    def _siguiente(self) -> None:
        if self.motor.terminado or self.controles.en_hilos_reales():
            return
        self.motor.paso()
        self._actualizar()
        if self.motor.terminado:
            self._pausar()

    def _avanzar_auto(self) -> None:
        if self.motor.terminado:
            self._pausar()
            return
        self.motor.paso()
        self._actualizar()
        if self.motor.terminado:
            self._pausar()

    def _ejecutar(self) -> None:
        if self.motor.terminado or self.controles.en_hilos_reales():
            return
        self._timer.start(self.controles.intervalo_ms())
        self.controles.set_ejecutando(True)

    def _pausar(self) -> None:
        self._timer.stop()
        self.controles.set_ejecutando(False)

    def _reiniciar(self) -> None:
        self._pausar()
        self._detener_analisis()
        self._detener_hilos()
        self.motor.reiniciar(limite_rondas=self.controles.limite_rondas())
        self._modo = MODO_DETERMINISTA
        self._actualizar()

    def _cambiar_velocidad(self, _valor: int) -> None:
        if self._timer.isActive():
            self._timer.start(self.controles.intervalo_ms())

    def _cambiar_limite(self, _valor: int) -> None:
        self._reiniciar()

    def _actualizar(self) -> None:
        inst = self.motor.instantanea()
        self.panel_superior.actualizar(inst, self._modo)
        self.escenario.actualizar(inst)
        self.panel_sincro.actualizar(inst)
        self.panel_eventos.establecer(self.motor.registro.eventos())
        self.panel_variables.actualizar(inst)

    # ---------------------------------------------------------- hilos reales

    def _toggle_modo_hilos(self, activo: bool) -> None:
        self._pausar()
        self.controles.set_hilos_activos(False)
        if activo:
            self._detener_analisis()
            self.controles.bloquear_deterministas(True)
            self._modo = MODO_HILOS
        else:
            self.controles.bloquear_deterministas(False)
            self._modo = MODO_DETERMINISTA
        self._actualizar()

    def _iniciar_hilos(self) -> None:
        if not self.controles.en_hilos_reales():
            return
        self._detener_analisis()
        self._detener_hilos()
        self._concurrente = SimulacionConcurrente(limite_rondas=self.controles.limite_rondas())
        self.panel_eventos.establecer([])
        self._concurrente.iniciar()
        self.controles.set_hilos_activos(True)
        self._modo = MODO_HILOS
        self._timer_hilos.start(120)

    def _detener_hilos(self) -> None:
        self._timer_hilos.stop()
        if self._concurrente is not None:
            self._concurrente.detener_y_unir(2.0)
            self._concurrente = None
        self.controles.set_hilos_activos(False)

    def _poll_hilos(self) -> None:
        sim = self._concurrente
        if sim is None:
            self._timer_hilos.stop()
            return
        datos = sim.instantanea()
        self.panel_eventos.establecer(sim.registro.eventos())
        self.panel_sincro.establecer_filas(datos["semaforos"])
        self.escenario.actualizar_libre(datos["mesa"], datos["cigarros"])
        self.panel_variables.establecer_desde(datos["mesa"], datos["cigarros"], datos["rondas"])
        inst = self.motor.instantanea()
        self.panel_superior.actualizar(inst, self._modo)
        if not sim.activa and datos["rondas"] >= sim.limite:
            self._detener_hilos()
            self._modo = MODO_HILOS_FIN
            self.panel_superior.actualizar(self.motor.instantanea(), self._modo)

    # ----------------------------------------------------------- modo análisis

    def _iniciar_analisis(self, variante_valor: str) -> None:
        self._pausar()
        self._detener_hilos()
        variante = VarianteAnalisis(variante_valor)
        self._analisis = ModoAnalisis(variante, rondas=self.controles.limite_rondas())
        self.panel_eventos.establecer([])
        self.controles.set_analisis_activo(True)
        self._modo = MODO_ANALISIS
        self.controles.mostrar_aviso(
            f"Ejecutando «{variante.etiqueta}» (ilustrativo, aislado del modelo principal)…"
        )
        self.panel_superior.actualizar(self.motor.instantanea(), self._modo)
        self._timer_analisis.start(350)

    def _avanzar_analisis(self) -> None:
        if self._analisis is None:
            return
        for _ in range(2):
            if self._analisis.paso() is None:
                break
        self.panel_eventos.establecer(list(self._analisis.consumidos))
        if self._analisis.terminado:
            self._finalizar_analisis()

    def _finalizar_analisis(self) -> None:
        self._timer_analisis.stop()
        self.controles.set_analisis_activo(False)
        if self._analisis is not None:
            self.controles.mostrar_aviso(
                f"Patología ilustrada · {self._analisis.resumen()} "
                "(eventos ilustrativos; la solución principal no se ve afectada)."
            )
        self._modo = MODO_DETERMINISTA
        self.panel_superior.actualizar(self.motor.instantanea(), self._modo)

    def _detener_analisis(self) -> None:
        self._timer_analisis.stop()
        self._analisis = None
        self.controles.set_analisis_activo(False)
        self.controles.ocultar_aviso()

    # ------------------------------------------------------------------ cierre

    def closeEvent(self, evento) -> None:  # noqa: N802 (API de Qt)
        self._timer.stop()
        self._timer_hilos.stop()
        self._timer_analisis.stop()
        self._detener_hilos()
        evento.accept()
