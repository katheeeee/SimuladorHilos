"""Registro de eventos con número de paso, participante, operación y resultado."""

from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..model.evento import Evento
from . import colores as c
from .widgets import TablaSimple, crear_panel

MAX_FILAS = 400


class PanelEventos(QWidget):
    def __init__(self) -> None:
        super().__init__()
        marco, layout = crear_panel("Registro de eventos")
        self.tabla = TablaSimple(["Paso", "Participante", "Operación", "Resultado"])
        layout.addWidget(self.tabla)
        contenedor = QVBoxLayout(self)
        contenedor.setContentsMargins(0, 0, 0, 0)
        contenedor.addWidget(marco)

    def establecer(self, eventos: list[Evento]) -> None:
        self.tabla.vaciar()
        for evento in eventos[-MAX_FILAS:]:
            self.tabla.agregar(list(evento.como_fila()), color=c.COLOR_EVENTO[evento.tipo])
