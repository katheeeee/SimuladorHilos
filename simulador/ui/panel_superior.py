"""Panel superior: título, estado general y ronda actual."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ..simulation.motor import Instantanea
from . import colores as c


class PanelSuperior(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Tarjeta")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        izquierda = QVBoxLayout()
        self.titulo = QLabel("Simulador de Concurrencia · Problema de los Fumadores")
        self.titulo.setObjectName("TituloApp")
        self.subtitulo = QLabel(
            "Modelo educativo de hilos, semáforos y exclusión mutua en Sistemas Operativos"
        )
        self.subtitulo.setObjectName("Subtitulo")
        izquierda.addWidget(self.titulo)
        izquierda.addWidget(self.subtitulo)

        derecha = QVBoxLayout()
        derecha.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.estado = QLabel("Listo")
        self.estado.setObjectName("Dato")
        self.estado.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ronda = QLabel("Ronda 0 de 0")
        self.ronda.setObjectName("Dato")
        self.ronda.setAlignment(Qt.AlignmentFlag.AlignRight)
        derecha.addWidget(self.estado)
        derecha.addWidget(self.ronda)

        layout.addLayout(izquierda)
        layout.addStretch(1)
        layout.addLayout(derecha)

    def actualizar(self, inst: Instantanea, modo: str) -> None:
        if inst.terminado:
            situacion = "Finalizada"
        elif inst.en_cpu is not None:
            situacion = "En ejecución"
        else:
            situacion = "Lista"
        self.estado.setText(f"Estado general: {situacion} · {modo}")
        self.estado.setStyleSheet(f"color:{c.ACENTO};")
        self.ronda.setText(f"Ronda actual: {inst.ronda_actual} de {inst.limite}")
