"""Panel de sincronización: semáforos, valores y hilos bloqueados."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..model.evento import TipoEvento
from ..simulation.motor import Instantanea
from .widgets import TablaSimple, crear_panel


class PanelSincronizacion(QWidget):
    def __init__(self) -> None:
        super().__init__()
        marco, layout = crear_panel("Sincronización · semáforos")
        self.tabla = TablaSimple(["Semáforo", "Valor", "Hilos bloqueados"])
        layout.addWidget(self.tabla)

        self.senal = QLabel("Última señal: —")
        self.senal.setObjectName("Subtitulo")
        self.senal.setWordWrap(True)
        layout.addWidget(self.senal)

        leyenda = QLabel(
            "P(s) = esperar (decrementa o bloquea) · V(s) = señalizar "
            "(despierta a un hilo o incrementa). mutex_mesa protege la sección crítica."
        )
        leyenda.setObjectName("Subtitulo")
        leyenda.setWordWrap(True)
        layout.addWidget(leyenda)

        contenedor = QVBoxLayout(self)
        contenedor.setContentsMargins(0, 0, 0, 0)
        contenedor.addWidget(marco)

    def actualizar(self, inst: Instantanea) -> None:
        self.tabla.vaciar()
        for nombre, valor, bloqueados in inst.semaforos:
            self.tabla.agregar([nombre, str(valor), bloqueados])
        evento = inst.ultimo_evento
        if evento is not None and evento.tipo is TipoEvento.SEMAFORO:
            quien = evento.participante.etiqueta if evento.participante else "—"
            self.senal.setText(f"Última señal: {quien} · {evento.operacion} → {evento.resultado}")
        elif evento is not None:
            self.senal.setText("Última señal: —")

    def establecer_filas(self, filas) -> None:
        """Modo hilos reales: lista de (nombre, valor)."""
        self.tabla.vaciar()
        for fila in filas:
            nombre, valor = fila[0], fila[1]
            self.tabla.agregar([nombre, str(valor), "—"])
