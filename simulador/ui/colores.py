"""Paleta pastel discreta y mapas de color para los estados y eventos."""

from __future__ import annotations

from ..model.evento import TipoEvento
from ..model.participante import EstadoHilo

# --- Paleta base (pastel, fondo claro) ---
FONDO = "#f6f7fb"
SUPERFICIE = "#ffffff"
SUPERFICIE_ALT = "#eef1f7"
BORDE = "#d8dbe4"
TEXTO = "#2b2d36"
TEXTO_SUAVE = "#6b6f7a"
ACENTO = "#7f9cc0"
ACENTO_SUAVE = "#dbe4f2"

# --- Colores por estado de hilo (pastel) ---
LISTO = "#bfe3c9"
EJECUTANDO = "#b6d2f0"
BLOQUEADO = "#f4dfb0"
TERMINADO = "#d9dbe1"
ALERTA = "#f0c3c3"
NEUTRO = "#e7e9ef"

# --- Colores por ingrediente ---
INGREDIENTE = {
    "tabaco": "#e7d3b8",
    "papel": "#cfe0ef",
    "fosforos": "#f3d4cf",
}

COLOR_ESTADO: dict[EstadoHilo, str] = {
    EstadoHilo.LISTO: LISTO,
    EstadoHilo.EJECUTANDO: EJECUTANDO,
    EstadoHilo.BLOQUEADO: BLOQUEADO,
    EstadoHilo.TERMINADO: TERMINADO,
}

COLOR_EVENTO: dict[TipoEvento, str] = {
    TipoEvento.TRANSICION: NEUTRO,
    TipoEvento.INGREDIENTE: "#dbe8d8",
    TipoEvento.SEMAFORO: "#e3ddf3",
    TipoEvento.CONTEXTO: "#d5eaec",
    TipoEvento.SISTEMA: "#e7e9ef",
    TipoEvento.ILUSTRATIVO: "#f6d9d4",
}

#: Color de fondo (pastel) para un ingrediente, por su valor de enum.
COLOR_INGREDIENTE: dict[str, str] = INGREDIENTE
