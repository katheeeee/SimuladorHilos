"""Hoja de estilo (QSS) de la aplicación, de tono académico y sobrio."""

from __future__ import annotations

from . import colores as c

QSS = f"""
QWidget {{
    background-color: {c.FONDO};
    color: {c.TEXTO};
    font-family: "DejaVu Sans", "Noto Sans", sans-serif;
    font-size: 10pt;
}}
QScrollArea {{ border: none; background-color: {c.FONDO}; }}
QScrollArea > QWidget > QWidget {{ background-color: {c.FONDO}; }}

QFrame#Tarjeta, QFrame#Panel {{
    background-color: {c.SUPERFICIE};
    border: 1px solid {c.BORDE};
    border-radius: 8px;
}}
QFrame#VariableCard {{
    background-color: {c.SUPERFICIE};
    border: 1px solid {c.BORDE};
    border-radius: 8px;
}}
QLabel#Aviso {{
    background-color: {c.ACENTO_SUAVE};
    color: {c.TEXTO};
    border: 1px solid {c.ACENTO};
    border-radius: 6px;
    padding: 6px 10px;
    font-weight: 600;
}}
QLabel#TituloSeccion {{
    font-size: 10pt;
    font-weight: 600;
    color: {c.TEXTO};
    padding-bottom: 2px;
}}
QLabel#Subtitulo {{ color: {c.TEXTO_SUAVE}; font-size: 9pt; }}
QLabel#TituloApp {{ font-size: 15pt; font-weight: 700; }}
QLabel#Dato {{ font-weight: 600; }}

QPushButton {{
    background-color: {c.SUPERFICIE};
    border: 1px solid {c.BORDE};
    border-radius: 6px;
    padding: 6px 12px;
    color: {c.TEXTO};
}}
QPushButton:hover {{ background-color: {c.SUPERFICIE_ALT}; }}
QPushButton:pressed {{ background-color: {c.ACENTO_SUAVE}; }}
QPushButton:disabled {{ color: {c.TEXTO_SUAVE}; background-color: {c.FONDO}; }}
QPushButton#Primario {{
    background-color: {c.ACENTO};
    border-color: {c.ACENTO};
    color: #ffffff;
    font-weight: 600;
}}
QPushButton#Primario:hover {{ background-color: {c.ACENTO}; }}
QPushButton#Primario:disabled {{ background-color: {c.ACENTO_SUAVE}; color: {c.TEXTO_SUAVE}; }}

QComboBox, QSpinBox {{
    background-color: {c.SUPERFICIE};
    border: 1px solid {c.BORDE};
    border-radius: 6px;
    padding: 4px 6px;
}}
QSlider::groove:horizontal {{ height: 4px; background: {c.BORDE}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {c.ACENTO}; width: 14px; margin: -6px 0; border-radius: 7px;
}}
QTableWidget {{
    background-color: {c.SUPERFICIE};
    border: 1px solid {c.BORDE};
    border-radius: 6px;
    gridline-color: {c.SUPERFICIE_ALT};
    selection-background-color: {c.ACENTO_SUAVE};
    selection-color: {c.TEXTO};
}}
QHeaderView::section {{
    background-color: {c.SUPERFICIE_ALT};
    border: none;
    border-bottom: 1px solid {c.BORDE};
    padding: 4px;
    font-weight: 600;
}}
QTabWidget::pane {{ border: 1px solid {c.BORDE}; border-radius: 6px; background: {c.SUPERFICIE}; }}
QTabBar::tab {{
    background: {c.SUPERFICIE_ALT};
    border: 1px solid {c.BORDE};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 6px 10px;
    color: {c.TEXTO_SUAVE};
}}
QTabBar::tab:selected {{ background: {c.SUPERFICIE}; color: {c.TEXTO}; font-weight: 600; }}
QCheckBox {{ spacing: 6px; }}
QToolTip {{
    background-color: {c.SUPERFICIE};
    color: {c.TEXTO};
    border: 1px solid {c.BORDE};
    padding: 4px;
}}
"""
