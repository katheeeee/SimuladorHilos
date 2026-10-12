"""Punto de entrada del Simulador de Concurrencia: Problema de los Fumadores.

Uso:
    python3 main.py
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from simulador.ui.app import VentanaPrincipal


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Simulador de Concurrencia: Problema de los Fumadores")
    app.setOrganizationName("Sistemas Operativos")
    ventana = VentanaPrincipal()
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
