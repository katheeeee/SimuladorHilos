"""Componentes gráficos reutilizables (creados con Qt, sin imágenes externas)."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..model.ingredientes import Ingrediente
from ..model.participante import EstadoHilo
from . import colores as c
from .dibujos import pintar_glifo


def crear_panel(titulo: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    """Crea una tarjeta con borde y, opcionalmente, un título de sección."""
    marco = QFrame()
    marco.setObjectName("Tarjeta")
    layout = QVBoxLayout(marco)
    layout.setContentsMargins(12, 10, 12, 12)
    layout.setSpacing(8)
    if titulo:
        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("TituloSeccion")
        layout.addWidget(etiqueta)
    return marco, layout


class DistintivoEstado(QLabel):
    """Etiqueta con color **y** texto para el estado de un hilo."""

    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)
        self.setMinimumWidth(96)
        self.establecer(EstadoHilo.LISTO)

    def establecer(self, estado: EstadoHilo) -> None:
        self.setText(estado.etiqueta)
        fondo = c.COLOR_ESTADO[estado]
        self.setStyleSheet(
            f"background-color:{fondo}; border-radius:12px; padding:1px 10px;"
            f" color:{c.TEXTO}; font-weight:600;"
        )
        self.setToolTip(estado.descripcion)

    def establecer_libre(self, texto: str, fondo: str = c.NEUTRO) -> None:
        """Etiqueta con texto y color arbitrarios (modo hilos reales)."""
        self.setText(texto)
        self.setStyleSheet(
            f"background-color:{fondo}; border-radius:12px; padding:1px 10px;"
            f" color:{c.TEXTO}; font-weight:600;"
        )
        self.setToolTip("")


class MiniIcono(QWidget):
    """Cuadro pequeño que pinta el glifo de un ingrediente."""

    def __init__(self, ingrediente: Ingrediente | None = None, tamano: int = 24) -> None:
        super().__init__()
        self._ingrediente = ingrediente
        self._tamano = tamano
        self.setFixedSize(tamano + 4, tamano + 4)

    def set_ingrediente(self, ingrediente: Ingrediente | None) -> None:
        self._ingrediente = ingrediente
        self.update()

    def paintEvent(self, _evento) -> None:  # noqa: N802 (API de Qt)
        if self._ingrediente is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margen = self._tamano * 0.08
        pintar_glifo(painter, QRectF(margen, margen, self._tamano, self._tamano), self._ingrediente)


class TablaSimple(QWidget):
    """Tabla de solo lectura con encabezados, sin edición."""

    def __init__(self, encabezados: list[str]) -> None:
        super().__init__()
        from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget

        self.tabla = QTableWidget(0, len(encabezados))
        self.tabla.setHorizontalHeaderLabels(encabezados)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setWordWrap(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabla)

    def vaciar(self) -> None:
        self.tabla.setRowCount(0)

    def agregar(self, valores: list[str], color: str | None = None) -> None:
        from PySide6.QtGui import QBrush, QColor
        from PySide6.QtWidgets import QTableWidgetItem

        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        for columna, valor in enumerate(valores):
            item = QTableWidgetItem(str(valor))
            if color:
                item.setBackground(QBrush(QColor(color)))
            self.tabla.setItem(fila, columna, item)
        self.tabla.scrollToBottom()