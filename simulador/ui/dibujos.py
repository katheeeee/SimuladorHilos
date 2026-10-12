"""Glifos vectoriales dibujados con QPainter (sin imágenes ni emojis).

Cada ingrediente, el agente y el cigarrillo se representan con formas
elementales de Qt; la paleta es sobria y coherente con la interfaz.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from ..model.ingredientes import Ingrediente

_VERDE_HOJA = "#94b58a"
_VERDE_LINEA = "#6f8f66"
_PAPEL_FONDO = "#f5f2e8"
_PAPEL_LINEA = "#c9c2ae"
_FOSFORO_PALO = "#e8cd9e"
_FOSFORO_BORDE = "#b39162"
_FOSFORO_CABEZA = "#d97768"
_ENGRANAJE = "#93a7c4"
_ENGRANAJE_MECHA = "#b9c7df"
_CIGARRO_CUERPO = "#efecdd"
_CIGARRO_BORDE = "#cfc9b4"
_CIGARRO_FILTRO = "#ecd39b"
_CIGARRO_BRASA = "#e07a5f"
_HUMO = "#cdd5de"


def _pluma(color: str, grosor: float) -> QPen:
    pluma = QPen(QColor(color))
    pluma.setWidthF(max(1.0, grosor))
    pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
    return pluma


def _escala(rect: QRectF) -> tuple[float, float, float]:
    """Devuelve (escala, centro_x, centro_y) para dibujar centrado en ``rect``."""
    escala = min(rect.width(), rect.height())
    return escala, rect.center().x(), rect.center().y()


def pintar_glifo(painter: QPainter, rect: QRectF, ing: Ingrediente) -> None:
    """Dibuja el glifo de un ingrediente dentro del área ``rect``."""
    painter.save()
    escala, cx, cy = _escala(rect)
    painter.translate(cx, cy)
    if ing is Ingrediente.TABACO:
        _glifo_tabaco(painter, escala)
    elif ing is Ingrediente.PAPEL:
        _glifo_papel(painter, escala)
    else:
        _glifo_fosforos(painter, escala)
    painter.restore()


def _glifo_tabaco(p: QPainter, s: float) -> None:
    """Una hoja oblicua con su nervadura central."""
    p.rotate(-22)
    hoja = QRectF(-0.40 * s, -0.24 * s, 0.80 * s, 0.48 * s)
    p.setBrush(QColor(_VERDE_HOJA))
    p.setPen(_pluma(_VERDE_LINEA, 0.03 * s))
    p.drawEllipse(hoja)
    p.setPen(_pluma(_VERDE_LINEA, 0.045 * s))
    p.drawLine(QPointF(-0.30 * s, 0.0), QPointF(0.26 * s, 0.0))
    p.setBrush(QColor(_VERDE_LINEA))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(-0.30 * s, 0.0), 0.05 * s, 0.05 * s)


def _glifo_papel(p: QPainter, s: float) -> None:
    """Una hoja de papel con tres líneas de guionado."""
    p.rotate(8)
    hoja = QRectF(-0.30 * s, -0.38 * s, 0.60 * s, 0.76 * s)
    p.setBrush(QColor(_PAPEL_FONDO))
    p.setPen(_pluma(_PAPEL_LINEA, 0.03 * s))
    p.drawRoundedRect(hoja, 0.05 * s, 0.05 * s)
    p.setPen(_pluma(_PAPEL_LINEA, 0.035 * s))
    for dy in (-0.16, 0.0, 0.16):
        p.drawLine(
            QPointF(hoja.left() + 0.09 * s, dy * s),
            QPointF(hoja.right() - 0.09 * s, dy * s),
        )


def _glifo_fosforos(p: QPainter, s: float) -> None:
    """Dos fósforos cruzados con la cabeza encendida."""
    p.rotate(-35)
    palo = QRectF(-0.30 * s, -0.035 * s, 0.52 * s, 0.07 * s)
    p.setBrush(QColor(_FOSFORO_PALO))
    p.setPen(_pluma(_FOSFORO_BORDE, 0.02 * s))
    p.drawRoundedRect(palo, 0.035 * s, 0.035 * s)
    p.setBrush(QColor(_FOSFORO_CABEZA))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(0.25 * s, 0.0), 0.075 * s, 0.075 * s)
    p.rotate(22)
    palo2 = QRectF(-0.20 * s, -0.035 * s, 0.40 * s, 0.07 * s)
    p.setBrush(QColor(_FOSFORO_PALO))
    p.setPen(_pluma(_FOSFORO_BORDE, 0.02 * s))
    p.drawRoundedRect(palo2, 0.035 * s, 0.035 * s)
    p.setBrush(QColor(_FOSFORO_CABEZA))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(0.24 * s, 0.0), 0.075 * s, 0.075 * s)


def pintar_engranaje(painter: QPainter, rect: QRectF) -> None:
    """Engranaje que representa al agente (planificador/proveedor)."""
    painter.save()
    escala, cx, cy = _escala(rect)
    painter.translate(cx, cy)
    painter.setBrush(QColor(_ENGRANAJE))
    painter.setPen(Qt.PenStyle.NoPen)
    for i in range(10):
        angulo = 2.0 * math.pi * i / 10.0
        tx = math.cos(angulo) * 0.46 * escala
        ty = math.sin(angulo) * 0.46 * escala
        painter.drawEllipse(QPointF(tx, ty), 0.11 * escala, 0.11 * escala)
    painter.drawEllipse(QPointF(0.0, 0.0), 0.34 * escala, 0.34 * escala)
    painter.setBrush(QColor(_ENGRANAJE_MECHA))
    painter.drawEllipse(QPointF(0.0, 0.0), 0.14 * escala, 0.14 * escala)
    painter.restore()


def pintar_cigarillo(painter: QPainter, rect: QRectF) -> None:
    """Cigarrillo encendido con dos pufos de humo (indicador de «Fuma»)."""
    painter.save()
    escala, cx, cy = _escala(rect)
    painter.translate(cx, cy)
    painter.rotate(-20)
    cuerpo = QRectF(-0.34 * escala, -0.035 * escala, 0.68 * escala, 0.07 * escala)
    painter.setBrush(QColor(_CIGARRO_CUERPO))
    painter.setPen(_pluma(_CIGARRO_BORDE, 0.02 * escala))
    painter.drawRoundedRect(cuerpo, 0.035 * escala, 0.035 * escala)
    filtro = QRectF(-0.34 * escala, -0.035 * escala, 0.14 * escala, 0.07 * escala)
    painter.setBrush(QColor(_CIGARRO_FILTRO))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(filtro, 0.03 * escala, 0.03 * escala)
    painter.setBrush(QColor(_CIGARRO_BRASA))
    painter.drawEllipse(QPointF(0.32 * escala, 0.0), 0.045 * escala, 0.045 * escala)
    painter.setBrush(QColor(_HUMO))
    for dx, dy, radio in ((-0.20, -0.34, 0.060), (-0.06, -0.45, 0.075), (0.09, -0.34, 0.060)):
        painter.drawEllipse(QPointF(dx * escala, dy * escala), radio * escala, radio * escala)
    painter.restore()