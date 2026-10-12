# Simulador de Concurrencia · Problema de los Fumadores

Aplicación de escritorio Linux, escrita en **Python 3 + PySide6**, que simula el
clásico *problema de los fumadores* de Sistemas Operativos con fines académicos.
Cuenta con un motor determinista paso a paso, un modo demostración con hilos
reales y un modo de análisis aislado para ilustrar patologías de concurrencia.

```
Agente ──coloca 2 ingredientes──▶ mesa ──despierta al fumador del faltante──▶ fuma ──▶ agente
```

## Requisitos e instalación (Linux)

* Python ≥ 3.10 (probado con 3.14).
* PySide6 ≥ 6.6.

Instalación recomendada en Arch Linux (paquete del repositorio):

```bash
sudo pacman -S pyside6
```

Alternativa con entorno virtual (también válida para otras distribuciones,
por ejemplo con `uv` o `python -m venv`):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Ejecución

```bash
./run.sh                 # usa .venv si existe, si no el python del sistema
# o directamente:
python3 main.py
```

`run.sh` lanza `main.py` con el intérprete correspondiente.

## Uso

| Control | Efecto |
|---|---|
| **Siguiente paso** | Ejecuta exactamente una transición lógica y la muestra en el registro. |
| **Ejecutar** | Reproduce automáticamente las transiciones con la velocidad elegida. |
| **Pausar** | Detiene la reproducción automática sin perder el estado. |
| **Reiniciar** | Restablece variables, hilos, registros, estadísticas y semáforos. |
| **Velocidad** | Ajusta el intervalo de la reproducción automática (1 = lenta, 10 = rápida). |
| **Límite de rondas** | Cuántos cigarrillos se fabrican antes de finalizar (cambiar el valor reinicia). |
| **Modo con hilos reales** | Ejecuta el protocolo con `threading.Thread`, `threading.Semaphore` y `threading.Lock` reales; el fumador habilitado rota por turno (no determinista). |
| **Análisis ilustrativo** | Reproduce una patología (carrera, interbloqueo o inanición) aislada de la solución; el resultado aparece como aviso en los controles. |

El escenario superior es una **mesa redonda** y muestra de un vistazo quién
ejecuta, quién espera y qué hay en la mesa: el **agente** (engranaje) se sienta
arriba y los **tres fumadores** alrededor (izquierda, abajo y derecha). Cada
colocación del agente hace que una **ficha se deslice** desde el agente hasta la
mesa, y el consumo la lleva hasta el fumador que fuma. El hueco del tercer
ingrediente queda explicado con la etiqueta *(lo tiene: Fumador con …)*; un
**anillo azul** sobre un avatar indica que ocupa la CPU, el **anillo
discontinuo** que está bloqueado y un **cigarrillo dibujado** que en ese paso
está fumando. Las variables compartidas se muestran como tarjetas con lámpara
(encendida = ingrediente en la mesa; apagada = no disponible).

## Arquitectura

```
main.py                      Punto de entrada (QApplication + ventana).
simulador/
├── model/                   Dominio: ingredientes, participantes, estados, eventos, estadísticas.
│   ├── ingredientes.py      Ingrediente, combinaciones y faltante.
│   ├── participante.py      Participante y EstadoHilo (listo/ejecutando/bloqueado/terminado).
│   ├── evento.py            Evento atómico y TipoEvento.
│   └── estadisticas.py      Estadísticas medidas (no ilustrativas).
├── synchronization/         Mecanismos de sincronización.
│   ├── semaforos.py         Semáforo modelado (contador + cola de espera observable).
│   ├── gestor.py            turno_agente, turno_fumador_x y mutex_mesa.
│   └── mecanismos.py        Envoltorios sobre threading (hilos reales).
├── simulation/              Motores.
│   ├── mesa.py              Variables compartidas (tabaco, papel, fósforos).
│   ├── agente.py            Selección de combinación (rotación equitativa; semilla = inicio).
│   ├── fumador.py           Posee un ingrediente permanente.
│   ├── motor.py             Máquina de estados determinista (paso() = 1 transición).
│   ├── concurrente.py       Backend de hilos reales (demostración).
│   └── modo_incorrecto.py   Modo de análisis aislado.
├── registro/registro.py     Buffer circular de eventos a prueba de concurrencia.
└── ui/                      PySide6: paneles, widgets y ventana.
    ├── colores.py           Paleta pastel.
    ├── dibujos.py           Glifos vectoriales con QPainter (ingredientes, agente, cigarrillo).
    ├── theme.py             Hoja de estilo (QSS).
    ├── widgets.py           Distintivos de estado, mini-iconos y tablas de solo lectura.
    ├── escena.py            Escenario visual: agente, mesa y avatares de fumadores.
    ├── panel_*.py           Superior, semáforos, eventos y variables/estadísticas.
    ├── controles.py         Botones, velocidad, límite, modos y aviso de análisis.
    └── app.py               Ventana principal y puente con el hilo principal de Qt.
tests/                       Suite en unittest (stdlib), sin dependencias.
```

**Separación simulación/UI:** el modelo y el motor no importan Qt; la interfaz
solo lee `MotorSimulacion.instantanea()` y el registro de eventos. El
backend de hilos reales nunca toca widgets: escribe en el registro a prueba de
concurrencia y un `QTimer` del hilo principal de Qt los consume.

## Reglas de sincronización

El protocolo correcto usa cuatro semáforos modelados y un mutex:

* `turno_agente` (inicia en **1**): solo con turno el agente coloca; si está a 0,
  el agente queda **bloqueado** esperando el fin de la ronda.
* `turno_fumador_t` / `p` / `f` (inician en **0**): el agente hace `V()` **solo**
  sobre el semáforo del fumador cuyo ingrediente falta en la mesa.
* `mutex_mesa` (inicia en **1**): protege la sección crítica (colocar/tomar
  ingredientes). `P(mutex_mesa)` ~ "entrar", `V(mutex_mesa)` ~ "salir".

Ciclo de una ronda (determinista, paso a paso):

1. El agente toma el turno, entra en la sección crítica y coloca dos
   ingredientes distintos.
2. Sale de la sección crítica y hace `V(turno_fumador_x)` del fumador correcto.
3. El agente hace `P(turno_agente)` y queda **bloqueado**.
4. El fumador despierta, entra en la sección crítica, toma los dos ingredientes
   y sale. Fabrica el cigarrillo y fuma.
5. El fumador hace `V(turno_agente)` (fin de ronda), luego `P(turno_fumador_x)`
   y queda **bloqueado** esperando la próxima señal.

**Por qué no hay interbloqueo:** cada fumador espera únicamente en su propio
semáforo; nadie retiene un ingrediente mientras espera otro. Se despierta
exactamente a un fumador por ronda y el agente no coloca una combinación nueva
hasta que la anterior se consume.

**Por qué no hay inanición:** el agente habilita a los fumadores por
**rotación** —cada ronda fuma un fumador distinto—, por lo que ninguno puede
quedar excluido ni se queda sin fumar.

## Estados de los hilos

Se muestran en las tarjetas con **color y texto**:

* **Listo** — puede usar la CPU, espera ser elegido.
* **Ejecutando** — ocupa la CPU en este instante.
* **Bloqueado** — espera una señal (un semáforo); no avanzará solo.
* **Terminado** — finalizó su trabajo.

Los **cambios de contexto** se registran como eventos explícitos
(`Cambio de contexto: la CPU pasa de X a Y`). Son **simulaciones**
del planificador: la aplicación no observa el planificador real del SO.

## Modo de análisis

Aislado por completo del motor correcto (no comparte estado con él) y acotado,
de modo que **no puede desestabilizar la aplicación**:

* **Condición de carrera** — dos hilos leen el inventario sin mutex y pierden
  una actualización.
* **Interbloqueo** — dos hilos retienen un recurso y esperan el del otro.
* **Inanición** — el agente repite siempre la misma combinación y deja a dos
  fumadores sin ser habilitados.

Todos sus eventos se marcan `ILUSTRATIVO` y sus estadísticas no forman parte de
las mediciones.

## Pruebas

Suite en `unittest` (sin dependencias). Ejecución:

```bash
python3 -m unittest discover -s tests -v
```

Cubre: solo el fumador correcto consume; no hay doble consumo; el agente espera
el fin de ronda; la mesa permanece consistente; invariantes de los semáforos; que
las estadísticas coincidan con los eventos; que la pausa/reanudación y el
reinicio no dejen hilos vivos; el cierre del backend de hilos reales; el modo de
análisis y su aislamiento; y una prueba de humo de la UI en `offscreen` (se
omite sola si no hay PySide6).

## Limitaciones conocidas

* **GIL:** los hilos de Python no ejecutan bytecode en paralelo real. El modo de
  hilos demuestra primitivas de sincronización y compartición de estado, no
  paralelismo físico.
* **Modelo determinista:** el motor es un modelo de eventos discretos; los
  tiempos son lógicos, no de reloj. Lo que ocurre es *simulado*, no una traza
  del planificador real.
* **Modo de hilos reales:** el orden de los eventos depende del planificador
  del SO y **no es reproducible** (aunque el fumador habilitado rota por
  turno). Solo se ofrece como demostración.
* **Estadísticas:** los contadores del panel son medidos por el simulador. El
  modo de análisis presenta datos ilustrativos, siempre etiquetados.
* El registro de eventos conserva las últimas 4000 entradas.

## Verificación en este equipo

* `python3 -m unittest discover -s tests` → **32 pruebas en OK**.
* PySide6 6.11.2, Python 3.14, Arch Linux.
* Arranque real de la GUI verificado (5 segundos de ejecución estable).