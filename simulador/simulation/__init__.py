"""Simulación: motor determinista, backend de hilos reales y modo de análisis."""

from .agente import Agente
from .concurrente import SimulacionConcurrente
from .fumador import Fumador
from .mesa import Mesa
from .modo_incorrecto import Diagnostico, ModoAnalisis, VarianteAnalisis
from .motor import (
    LIMITE_POR_DEFECTO,
    SEMILLA_POR_DEFECTO,
    Instantanea,
    MotorSimulacion,
)

__all__ = [
    "Agente",
    "Fumador",
    "Mesa",
    "MotorSimulacion",
    "Instantanea",
    "SimulacionConcurrente",
    "ModoAnalisis",
    "VarianteAnalisis",
    "Diagnostico",
    "LIMITE_POR_DEFECTO",
    "SEMILLA_POR_DEFECTO",
]
