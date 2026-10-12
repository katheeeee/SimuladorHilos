"""Variables compartidas y estadísticas, con tarjetas visuales por ingrediente."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..model.ingredientes import TODOS, Ingrediente
from ..simulation.motor import Instantanea
from . import colores as c
from .widgets import MiniIcono, TablaSimple, crear_panel


class LamparaEstado(QLabel):
    """Lámpara circular encendida/apagada para cada variable."""

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(18, 18)
        self._color = c.NEUTRO
        self._aplicar()

    def _aplicar(self) -> None:
        self.setStyleSheet(
            f"background-color:{self._color}; border-radius:9px;"
            f" border:1px solid {c.BORDE};"
        )

    def encender(self, color: str = c.ACENTO) -> None:
        self._color = color
        self._aplicar()

    def apagar(self) -> None:
        self._color = c.NEUTRO
        self._aplicar()


class VariableCard(QFrame):
    """Tarjeta de una variable compartida: icono, lámpara y estado."""

    def __init__(self, ingrediente: Ingrediente) -> None:
        super().__init__()
        self._ingrediente = ingrediente
        self.setObjectName("VariableCard")
        self.setMinimumHeight(86)

        fila = QHBoxLayout(self)
        fila.setContentsMargins(8, 6, 8, 6)
        fila.setSpacing(8)

        self.icono = MiniIcono(ingrediente, tamano=34)
        fila.addWidget(self.icono)

        textos = QVBoxLayout()
        textos.setSpacing(1)
        nombre = QLabel(ingrediente.etiqueta)
        nombre.setStyleSheet("font-weight:600;")
        self.estado = QLabel("no disponible")
        self.estado.setObjectName("Subtitulo")
        textos.addWidget(nombre)
        textos.addWidget(self.estado)

        fila.addLayout(textos, 1)
        self.lampara = LamparaEstado()
        fila.addWidget(self.lampara, 0, Qt.AlignmentFlag.AlignVCenter)

    def establecer(self, presente: bool) -> None:
        if presente:
            self.estado.setText("en la mesa")
            self.lampara.encender(c.COLOR_INGREDIENTE[self._ingrediente.value])
        else:
            self.estado.setText("no disponible")
            self.lampara.apagar()


class PanelVariables(QWidget):
    def __init__(self) -> None:
        super().__init__()
        marco, layout = crear_panel("Variables compartidas y estadísticas")

        fila_variables = QHBoxLayout()
        fila_variables.setSpacing(8)
        self.cards: dict[Ingrediente, VariableCard] = {}
        for ing in TODOS:
            tarjeta = VariableCard(ing)
            self.cards[ing] = tarjeta
            fila_variables.addWidget(tarjeta, 1)
        layout.addLayout(fila_variables)

        subtitulo = QLabel("Estadísticas medidas por el simulador")
        subtitulo.setObjectName("Subtitulo")
        layout.addWidget(subtitulo)
        self.estadisticas = TablaSimple(["Métrica", "Valor"])
        layout.addWidget(self.estadisticas, 1)

        nota = QLabel(
            "Datos medidos. Los eventos del modo de análisis (carrera, interbloqueo, "
            "inanición) son ilustrativos y se anuncian en los controles."
        )
        nota.setObjectName("Subtitulo")
        nota.setWordWrap(True)
        layout.addWidget(nota)

        contenedor = QVBoxLayout(self)
        contenedor.setContentsMargins(0, 0, 0, 0)
        contenedor.addWidget(marco)

    def _desde_variables(self, presentes) -> None:
        for ing, tarjeta in self.cards.items():
            if isinstance(presentes, dict):
                presente = presentes.get(ing, False)
            else:
                presente = ing in presentes
            tarjeta.establecer(bool(presente))

    def actualizar(self, inst: Instantanea) -> None:
        self._desde_variables(inst.variables)
        self.estadisticas.vaciar()
        for nombre, valor in inst.estadisticas.como_filas():
            self.estadisticas.agregar([nombre, valor])

    def establecer_desde(self, variables: dict, cigarros: dict, rondas: int) -> None:
        """Modo hilos reales: estado de mesa y conteos observados."""
        self._desde_variables(variables)
        self.estadisticas.vaciar()
        self.estadisticas.agregar(["Rondas completadas", str(rondas)])
        for fumador, cuenta in cigarros.items():
            self.estadisticas.agregar([f"Cigarrillos de {fumador.etiqueta}", str(cuenta)])