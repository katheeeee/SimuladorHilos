"""Escena visual del problema de los fumadores: mesa redonda.

El escenario muestra una mesa circular con tres fumadores sentados alrededor
(izquierda, abajo y derecha) y el agente arriba. Los ingredientes son fichas
que **se mueven**: cuando el agente coloca, la ficha se desliza de la esquina
del agente a su plaza sobre la mesa; cuando un fumador consume, las fichas se
deslizan de la mesa hacia su puesto. La plaza del ingrediente que falta (que
posee un fumador de forma permanente) se explica en pantalla para que no parezca
un hueco sin usar.

Todo se dibuja con QPainter (cero imágenes y cero emojis); la animación es un
mero efecto visual con QTimer que **nunca** modifica el modelo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..model.ingredientes import TODOS, Ingrediente
from ..model.participante import FUMADORES, EstadoHilo, Participante, ingrediente_de, fumador_de
from ..simulation.motor import Instantanea
from . import colores as c
from .dibujos import pintar_cigarillo, pintar_engranaje, pintar_glifo
from .widgets import DistintivoEstado, MiniIcono

_MADERA_CLARA = "#efe4c8"
_MADERA_BORDE = "#cbbf9f"
_MADERA_LLANTA = "#e0cfa6"
_MADERA_PATA = "#d3c19c"

#: Frecuencia y duración del deslizamiento de las fichas (solo pintado).
GLIDE_INTERVALO = 0.03
GLIDE_DURACION = 0.34
DESTELLO_TICKS = 12


@dataclass
class _Glide:
    """Una ficha volando. ``llegada`` = agente → mesa; ``salida`` = mesa → fumador."""

    ingrediente: Ingrediente
    direccion: str
    consumidor: Participante | None
    progreso: float


class AvatarHilo(QWidget):
    """Avatar circular: color del estado, anillo de CPU, glifo y cigarrillo."""

    def __init__(self, agente: bool = False, tamano: int = 76) -> None:
        super().__init__()
        self._agente = agente
        self._ingrediente: Ingrediente | None = None
        self._estado: EstadoHilo | None = EstadoHilo.LISTO
        self._en_cpu = False
        self._fumando = False
        self._tamano = tamano
        self.setFixedSize(tamano, tamano)

    def configurar_ingrediente(self, ingrediente: Ingrediente) -> None:
        self._ingrediente = ingrediente
        self.update()

    def actualizar(self, estado: EstadoHilo, en_cpu: bool = False, fumando: bool = False) -> None:
        self._estado = estado
        self._en_cpu = en_cpu
        self._fumando = fumando
        self.update()

    def ver_libre(self) -> None:
        """Modo hilos reales: sin estado simulado (lo controla el planificador)."""
        self._estado = None
        self._en_cpu = False
        self._fumando = False
        self.update()

    def paintEvent(self, _evento) -> None:  # noqa: N802 (API de Qt)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radio = self._tamano / 2.0 - 5.0
        centro = self._tamano / 2.0

        if self._estado is None:
            fondo = c.NEUTRO
            pluma = QPen(QColor(c.BORDE))
        else:
            fondo = c.COLOR_ESTADO[self._estado]
            if self._en_cpu:
                pluma = QPen(QColor(c.ACENTO))
                pluma.setWidthF(4.0)
            elif self._estado is EstadoHilo.BLOQUEADO:
                pluma = QPen(QColor(c.TEXTO_SUAVE))
                pluma.setWidthF(2.0)
                pluma.setStyle(Qt.PenStyle.DashLine)
            else:
                pluma = QPen(QColor(c.BORDE))
                pluma.setWidthF(1.5)
        painter.setPen(pluma)
        painter.setBrush(QColor(fondo))
        painter.drawEllipse(QRectF(5.0, 5.0, self._tamano - 10.0, self._tamano - 10.0))

        area_glifo = QRectF(
            centro - radio * 0.62, centro - radio * 0.62, radio * 1.24, radio * 1.24
        )
        if self._agente:
            pintar_engranaje(painter, area_glifo)
        elif self._ingrediente is not None:
            pintar_glifo(painter, area_glifo, self._ingrediente)

        if self._fumando:
            pintar_cigarillo(painter, area_glifo)


class VisualAgente(QFrame):
    """Tarjeta del agente (arriba del escenario): engranaje, estado y acción."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Tarjeta")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        self.avatar = AvatarHilo(agente=True, tamano=64)
        layout.addWidget(self.avatar)

        textos = QVBoxLayout()
        textos.setSpacing(2)
        self.nombre = QLabel("Agente")
        self.nombre.setStyleSheet("font-weight:700; font-size:12pt;")
        textos.addWidget(self.nombre)
        self.distintivo = DistintivoEstado()
        textos.addWidget(self.distintivo)
        self.accion = QLabel("—")
        self.accion.setWordWrap(True)
        textos.addWidget(self.accion)
        layout.addLayout(textos, 1)

    def actualizar(self, estado: EstadoHilo, accion: str, en_cpu: bool) -> None:
        self.avatar.actualizar(estado, en_cpu)
        self.distintivo.establecer(estado)
        self.accion.setText(accion if accion else "—")

    def ver_libre(self) -> None:
        self.avatar.ver_libre()
        self.distintivo.establecer_libre("Hilo real", c.NEUTRO)
        self.accion.setText("Coloca dos ingredientes distintos en la mesa")


class VisualFumador(QFrame):
    """Tarjeta de un fumador sentado a la mesa: avatar, estado, acción y datos."""

    def __init__(self, fumador: Participante) -> None:
        super().__init__()
        self.fumador = fumador
        self.setObjectName("Tarjeta")
        self.setMinimumWidth(230)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 8)
        layout.setSpacing(4)

        cabecera = QHBoxLayout()
        ingrediente = ingrediente_de(fumador)
        self.mini = MiniIcono(ingrediente, tamano=24)
        self.nombre = QLabel(fumador.etiqueta)
        self.nombre.setStyleSheet("font-weight:600;")
        self.distintivo = DistintivoEstado()
        cabecera.addWidget(self.mini)
        cabecera.addWidget(self.nombre)
        cabecera.addStretch(1)
        cabecera.addWidget(self.distintivo)
        layout.addLayout(cabecera)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(10)
        self.avatar = AvatarHilo(tamano=64)
        self.avatar.configurar_ingrediente(ingrediente)
        cuerpo.addWidget(self.avatar)

        detalles = QVBoxLayout()
        detalles.setSpacing(2)
        self.accion = QLabel("—")
        self.accion.setWordWrap(True)
        detalles.addWidget(self.accion)
        self.cigarros = QLabel("Cigarrillos: 0")
        self.cigarros.setObjectName("Subtitulo")
        detalles.addWidget(self.cigarros)
        detalles.addStretch(1)
        cuerpo.addLayout(detalles, 1)
        layout.addLayout(cuerpo)

    def actualizar(
        self,
        estado: EstadoHilo,
        accion: str,
        en_cpu: bool = False,
        cigarros: int = 0,
        fumando: bool = False,
    ) -> None:
        self.avatar.actualizar(estado, en_cpu, fumando)
        self.distintivo.establecer(estado)
        self.accion.setText(accion if accion else "—")
        self.cigarros.setText(f"Cigarrillos: {cigarros}")

    def actualizar_libre(self, cigarros: int = 0, accion: str = "—") -> None:
        self.avatar.ver_libre()
        self.distintivo.establecer_libre("Hilo real", c.NEUTRO)
        self.accion.setText(accion)
        self.cigarros.setText(f"Cigarrillos: {cigarros}")


class MesaRedonda(QWidget):
    """Mesa circular con plazas de ingrediente y fichas que se deslizan."""

    def __init__(self) -> None:
        super().__init__()
        self._contenido: frozenset[Ingrediente] = frozenset()
        self._glides: list[_Glide] = []
        self._destellos: dict[Ingrediente, int] = {}
        self._timer = QTimer(self)
        self._timer.setInterval(int(GLIDE_INTERVALO * 1000))
        self._timer.timeout.connect(self._tick)
        self.setMinimumHeight(195)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def sizeHint(self) -> QSize:
        return QSize(560, 380)

    # ------------------------------------------------------------ geometría

    def _centro(self) -> QPointF:
        return QPointF(self.width() / 2.0, self.height() / 2.0)

    def _radio(self) -> float:
        return min(self.width(), self.height()) * 0.30

    def _posicion_dock(self, ingrediente: Ingrediente) -> QPointF:
        angulos = {
            Ingrediente.TABACO: 155.0,
            Ingrediente.PAPEL: 90.0,
            Ingrediente.FOSFOROS: 25.0,
        }
        angulo = math.radians(angulos[ingrediente])
        centro = self._centro()
        radio = self._radio()
        return QPointF(
            centro.x() + radio * math.cos(angulo),
            centro.y() + radio * math.sin(angulo),
        )

    def _asiento(self, fumador: Participante) -> QPointF:
        centro = self._centro()
        radio = self._radio()
        indice = FUMADORES.index(fumador)
        if indice == 0:
            return QPointF(centro.x() - radio - 46.0, centro.y())
        if indice == 1:
            return QPointF(centro.x(), centro.y() + radio + 46.0)
        return QPointF(centro.x() + radio + 46.0, centro.y())

    def _posicion_agente(self) -> QPointF:
        centro = self._centro()
        radio = self._radio()
        return QPointF(centro.x(), centro.y() - radio - 18.0)

    # ------------------------------------------------------------- contenido

    def actualizar_contenido(
        self,
        contenido: frozenset,
        consumidor: Participante | None = None,
        animar: bool = True,
    ) -> None:
        """Aplica el nuevo contenido de mesa y programa las fichas voladoras."""
        nuevo = frozenset(contenido)
        agregados = set(nuevo) - set(self._contenido)
        quitados = set(self._contenido) - set(nuevo)
        self._contenido = nuevo

        if animar and (agregados or quitados):
            for ingrediente in agregados:
                self._glides.append(_Glide(ingrediente, "llegada", None, 0.0))
            if consumidor is not None and consumidor in FUMADORES:
                for ingrediente in quitados:
                    self._glides.append(_Glide(ingrediente, "salida", consumidor, 0.0))
            if self._glides:
                self._timer.start()
        self.update()

    def _tick(self) -> None:
        restantes: list[_Glide] = []
        for glide in self._glides:
            glide.progreso += GLIDE_INTERVALO / GLIDE_DURACION
            if glide.progreso >= 1.0:
                self._destellos[glide.ingrediente] = DESTELLO_TICKS
            else:
                restantes.append(glide)
        self._glides = restantes
        for ingrediente in list(self._destellos):
            self._destellos[ingrediente] -= 1
            if self._destellos[ingrediente] <= 0:
                del self._destellos[ingrediente]
        if not self._glides and not self._destellos:
            self._timer.stop()
        self.update()

    # ---------------------------------------------------------------- pintado

    def paintEvent(self, _evento) -> None:  # noqa: N802 (API de Qt)
        if self.width() <= 1 or self.height() <= 1:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._dibujar_tabla(painter)
        self._dibujar_destellos(painter)
        self._dibujar_plazas(painter)
        self._dibujar_glides(painter)

    def _dibujar_tabla(self, p: QPainter) -> None:
        cx, cy = self._centro().x(), self._centro().y()
        radio = self._radio()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 22))
        p.drawEllipse(QPointF(cx, cy + 6.0), radio + 3.0, radio + 3.0)
        p.setBrush(QColor(_MADERA_PATA))
        p.drawRoundedRect(QRectF(cx - radio * 0.26, cy + radio - 8.0, radio * 0.52, radio * 0.28), 8, 8)
        p.setBrush(QColor(_MADERA_LLANTA))
        p.setPen(QPen(QColor(_MADERA_BORDE), 2.0))
        p.drawEllipse(QPointF(cx, cy), radio, radio)
        p.setBrush(QColor(_MADERA_CLARA))
        p.setPen(QPen(QColor("#d8cbaa"), 1.0))
        p.drawEllipse(QPointF(cx, cy), radio - 12.0, radio - 12.0)

    def _dibujar_destellos(self, p: QPainter) -> None:
        p.setBrush(Qt.BrushStyle.NoBrush)
        for ingrediente, ticks in self._destellos.items():
            radio = 26.0 + ticks
            p.setPen(QPen(QColor(c.ACENTO), 2.5))
            p.drawEllipse(self._posicion_dock(ingrediente), radio, radio)

    def _dibujar_plazas(self, p: QPainter) -> None:
        for ingrediente in TODOS:
            llegando = any(
                g.ingrediente is ingrediente and g.direccion == "llegada" for g in self._glides
            )
            if llegando:
                continue
            posicion = self._posicion_dock(ingrediente)
            presente = ingrediente in self._contenido
            placa = QRectF(posicion.x() - 24.0, posicion.y() - 24.0, 48.0, 48.0)
            if presente:
                p.setBrush(QColor(c.SUPERFICIE))
                p.setPen(QPen(QColor(c.ACENTO), 2.0))
                p.drawRoundedRect(placa, 8, 8)
                margen = 8.0
                pintar_glifo(p, placa.adjusted(margen, margen, -margen, -margen), ingrediente)
                self._rotular(p, posicion, [ingrediente.etiqueta], normal=True)
            else:
                p.setBrush(QColor(c.SUPERFICIE_ALT))
                pluma = QPen(QColor(c.BORDE))
                pluma.setStyle(Qt.PenStyle.DashLine)
                p.setPen(pluma)
                p.drawRoundedRect(placa, 8, 8)
                dueno = fumador_de(ingrediente).etiqueta
                self._rotular(p, posicion, [ingrediente.etiqueta, f"(lo tiene: {dueno})"], normal=False)

    def _rotular(self, p: QPainter, posicion: QPointF, lineas: list[str], normal: bool) -> None:
        fuente = QFont(p.font())
        fuente.setPointSize(8)
        if not normal:
            fuente.setBold(True)
        p.setFont(fuente)
        p.setPen(QPen(QColor(c.TEXTO_SUAVE if normal else c.ACENTO), 1.0))
        caja = QRectF(posicion.x() - 84.0, posicion.y() - 70.0, 168.0, 30.0)
        for i, linea in enumerate(lineas):
            p.drawText(
                QRectF(caja.left(), caja.top() + i * 13.0, caja.width(), 13.0),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                linea,
            )

    def _dibujar_glides(self, p: QPainter) -> None:
        for glide in self._glides:
            if glide.direccion == "llegada":
                origen = self._posicion_agente()
                destino = self._posicion_dock(glide.ingrediente)
            else:
                origen = self._posicion_dock(glide.ingrediente)
                destino = self._asiento(glide.consumidor) if glide.consumidor else origen
            progreso = min(glide.progreso, 1.0)
            x = origen.x() + (destino.x() - origen.x()) * progreso
            y = origen.y() + (destino.y() - origen.y()) * progreso
            posicion = QPointF(x, y)
            tamano = 44.0 - progreso * 8.0
            placa = QRectF(posicion.x() - tamano / 2.0, posicion.y() - tamano / 2.0, tamano, tamano)
            p.setBrush(QColor(c.SUPERFICIE))
            p.setPen(QPen(QColor(c.ACENTO), 2.0))
            p.drawRoundedRect(placa, 7, 7)
            margen = tamano * 0.18
            pintar_glifo(p, placa.adjusted(margen, margen, -margen, -margen), glide.ingrediente)


class EscenarioVisual(QFrame):
    """Agente arriba, mesa redonda al centro y los tres fumadores alrededor."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Tarjeta")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 10)
        layout.setSpacing(8)

        cabecera = QHBoxLayout()
        titulo = QLabel("Mesa redonda · ficha que se mueve con cada intercambio")
        titulo.setObjectName("TituloSeccion")
        self.intercambio = QLabel("Último intercambio: —")
        self.intercambio.setObjectName("Subtitulo")
        self.cpu = QLabel("En CPU: —")
        self.cpu.setStyleSheet(f"color:{c.ACENTO}; font-weight:600;")
        cabecera.addWidget(titulo)
        cabecera.addWidget(self.intercambio)
        cabecera.addStretch(1)
        cabecera.addWidget(self.cpu)
        layout.addLayout(cabecera)

        # --- El agente se sienta arriba de la mesa ---
        fila_agente = QHBoxLayout()
        fila_agente.addStretch(1)
        self.agente = VisualAgente()
        fila_agente.addWidget(self.agente)
        fila_agente.addStretch(1)
        layout.addLayout(fila_agente)

        # --- Mesa al centro; un fumador a cada lado ---
        self.mesa = MesaRedonda()
        self.fumadores: dict[Participante, VisualFumador] = {}
        fila_media = QHBoxLayout()
        fila_media.setSpacing(12)
        self._construir_fumador(fila_media, FUMADORES[0])
        fila_media.addWidget(self.mesa, 3)
        self._construir_fumador(fila_media, FUMADORES[2])
        layout.addLayout(fila_media, 5)

        # --- El tercer fumador, al fondo ---
        fila_inferior = QHBoxLayout()
        fila_inferior.addStretch(2)
        self._construir_fumador(fila_inferior, FUMADORES[1])
        fila_inferior.addStretch(2)
        layout.addLayout(fila_inferior, 3)

    def _construir_fumador(self, fila: QHBoxLayout, fumador: Participante) -> None:
        tarjeta = VisualFumador(fumador)
        self.fumadores[fumador] = tarjeta
        fila.addWidget(tarjeta, 2)

    @staticmethod
    def _consumidor(inst: Instantanea) -> Participante | None:
        if inst.en_cpu is not None and inst.en_cpu in FUMADORES:
            return inst.en_cpu
        ultimo = inst.ultimo_evento
        if ultimo is not None and ultimo.participante in FUMADORES:
            return ultimo.participante
        return None

    def actualizar(self, inst: Instantanea) -> None:
        cpu = inst.en_cpu
        self.cpu.setText(f"En CPU: {cpu.etiqueta}" if cpu is not None else "En CPU: —")
        self.intercambio.setText(self._texto_intercambio(inst))
        self.agente.actualizar(
            inst.estados[Participante.AGENTE],
            inst.acciones[Participante.AGENTE],
            en_cpu=cpu is Participante.AGENTE,
        )
        self.mesa.actualizar_contenido(inst.contenido_mesa, self._consumidor(inst), animar=True)
        ultimo = inst.ultimo_evento
        for fumador, tarjeta in self.fumadores.items():
            significa_fuma = (
                ultimo is not None and ultimo.participante is fumador and ultimo.operacion == "Fuma"
            )
            tarjeta.actualizar(
                inst.estados[fumador],
                inst.acciones[fumador],
                en_cpu=cpu is fumador,
                cigarros=inst.estadisticas.cigarros_por_fumador[fumador],
                fumando=significa_fuma,
            )

    @staticmethod
    def _texto_intercambio(inst: Instantanea) -> str:
        ultimo = inst.ultimo_evento
        if ultimo is None or ultimo.participante is None:
            return "Último intercambio: —"
        quien = ultimo.participante.etiqueta
        return f"Último intercambio: {quien} · {ultimo.operacion} → {ultimo.resultado}"

    def actualizar_libre(self, mesa: frozenset, cigarros: dict) -> None:
        """Modo hilos reales: la CPU la decide el planificador del sistema."""
        self.cpu.setText("En CPU: — (la decide el planificador del sistema)")
        self.intercambio.setText("Último intercambio: — (hilos reales)")
        self.agente.ver_libre()
        self.mesa.actualizar_contenido(mesa, None, animar=False)
        for fumador, tarjeta in self.fumadores.items():
            tarjeta.actualizar_libre(cigarros.get(fumador, 0))