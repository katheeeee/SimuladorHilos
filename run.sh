#!/usr/bin/env bash
# Lanzador de conveniencia del Simulador de Concurrencia: Problema de los Fumadores.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Si existe un entorno virtual local, se usa ese interprete; si no, el del sistema.
if [[ -x "$DIR/.venv/bin/python" ]]; then
    PY="$DIR/.venv/bin/python"
else
    PY="python3"
fi

exec "$PY" "$DIR/main.py" "$@"
