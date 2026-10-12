"""Controles inferiores de la simulación."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from ..simulation.modo_incorrecto import VarianteAnalisis

#: Intervalos (ms) para el valor 1..10 del deslizador de velocidad.
INTERVALOS_MS = [1600, 1200, 900, 650, 450, 300, 180, 110, 60, 30]


class Controles(QFrame):
    siguiente = Signal()
    ejecutar = Signal()
    pausar = Signal()
    reiniciar = Signal()
    velocidad = Signal(int)
    limite = Signal(int)
    modo_hilos = Signal(bool)
    iniciar_hilos = Signal()
    detener_hilos = Signal()
    analizar = Signal(str)
    detener_analisis = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Tarjeta")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(12, 10, 12, 10)
        raiz.setSpacing(8)

        # --- Fila 1: reproducción ---
        fila1 = QHBoxLayout()
        self.btn_siguiente = QPushButton("Siguiente paso")
        self.btn_ejecutar = QPushButton("Ejecutar")
        self.btn_ejecutar.setObjectName("Primario")
        self.btn_pausar = QPushButton("Pausar")
        self.btn_reiniciar = QPushButton("Reiniciar")
        for boton in (self.btn_siguiente, self.btn_ejecutar, self.btn_pausar, self.btn_reiniciar):
            fila1.addWidget(boton)
        fila1.addStretch(1)

        fila1.addWidget(QLabel("Velocidad"))
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(10)
        self.slider.setValue(6)
        self.slider.setFixedWidth(140)
        self.slider.setToolTip("Frecuencia de la reproducción automática")
        fila1.addWidget(self.slider)

        fila1.addWidget(QLabel("Límite de rondas"))
        self.spin = QSpinBox()
        self.spin.setMinimum(1)
        self.spin.setMaximum(50)
        self.spin.setValue(6)
        self.spin.setToolTip("Cuántos cigarrillos se fabrican antes de finalizar")
        fila1.addWidget(self.spin)

        raiz.addLayout(fila1)

        # --- Fila 2: modos ---
        fila2 = QHBoxLayout()
        self.chk_hilos = QCheckBox("Modo con hilos reales (demostración, no determinista)")
        self.btn_iniciar_hilos = QPushButton("Iniciar hilos")
        self.btn_detener_hilos = QPushButton("Detener hilos")
        self.btn_detener_hilos.setEnabled(False)
        fila2.addWidget(self.chk_hilos)
        fila2.addWidget(self.btn_iniciar_hilos)
        fila2.addWidget(self.btn_detener_hilos)
        fila2.addStretch(1)

        self.combo_analisis = QComboBox()
        for variante in VarianteAnalisis:
            self.combo_analisis.addItem(variante.etiqueta, variante.value)
        self.btn_analizar = QPushButton("Ejecutar análisis")
        self.btn_detener_analisis = QPushButton("Detener análisis")
        self.btn_detener_analisis.setEnabled(False)
        fila2.addWidget(QLabel("Análisis ilustrativo:"))
        fila2.addWidget(self.combo_analisis)
        fila2.addWidget(self.btn_analizar)
        fila2.addWidget(self.btn_detener_analisis)

        raiz.addLayout(fila2)

        # --- Fila 3: aviso del modo de análisis (antes panel de conceptos) ---
        self.aviso_analisis = QLabel("")
        self.aviso_analisis.setObjectName("Aviso")
        self.aviso_analisis.setWordWrap(True)
        self.aviso_analisis.hide()
        raiz.addWidget(self.aviso_analisis)

        # --- Conexiones ---
        self.btn_siguiente.clicked.connect(self.siguiente.emit)
        self.btn_ejecutar.clicked.connect(self.ejecutar.emit)
        self.btn_pausar.clicked.connect(self.pausar.emit)
        self.btn_reiniciar.clicked.connect(self.reiniciar.emit)
        self.slider.valueChanged.connect(self.velocidad.emit)
        self.spin.valueChanged.connect(self.limite.emit)
        self.chk_hilos.toggled.connect(self.modo_hilos.emit)
        self.btn_iniciar_hilos.clicked.connect(self.iniciar_hilos.emit)
        self.btn_detener_hilos.clicked.connect(self.detener_hilos.emit)
        self.btn_analizar.clicked.connect(
            lambda: self.analizar.emit(self.combo_analisis.currentData())
        )
        self.btn_detener_analisis.clicked.connect(self.detener_analisis.emit)

        self.bloquear_deterministas(False)
        self.btn_iniciar_hilos.setEnabled(False)

    # --------------------------------------------------------------- utilidades

    def intervalo_ms(self) -> int:
        return INTERVALOS_MS[self.slider.value() - 1]

    def limite_rondas(self) -> int:
        return self.spin.value()

    def en_hilos_reales(self) -> bool:
        return self.chk_hilos.isChecked()

    def bloquear_deterministas(self, bloquear: bool) -> None:
        for boton in (self.btn_siguiente, self.btn_ejecutar, self.btn_pausar, self.btn_reiniciar):
            boton.setEnabled(not bloquear)
        self.slider.setEnabled(not bloquear)
        self.spin.setEnabled(not bloquear)

    def set_ejecutando(self, ejecutando: bool) -> None:
        self.btn_ejecutar.setEnabled(not ejecutando)
        self.btn_pausar.setEnabled(ejecutando)
        self.btn_siguiente.setEnabled(not ejecutando)

    def set_hilos_activos(self, activos: bool) -> None:
        self.btn_iniciar_hilos.setEnabled(not activos)
        self.btn_detener_hilos.setEnabled(activos)

    def set_analisis_activo(self, activo: bool) -> None:
        self.btn_analizar.setEnabled(not activo)
        self.btn_detener_analisis.setEnabled(activo)

    def mostrar_aviso(self, texto: str) -> None:
        self.aviso_analisis.setText(texto)
        self.aviso_analisis.show()

    def ocultar_aviso(self) -> None:
        self.aviso_analisis.clear()
        self.aviso_analisis.hide()
