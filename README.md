# Sumo Nano

Firmware para un robot minisumo con Arduino Nano: arranque por control remoto, aperturas para los tres rounds, búsqueda, ataque con PID y escape del borde. Incluye un simulador que compila el mismo código.

## Contenido

1. [Conexiones](#conexiones)
2. [Cargar el firmware](#cargar-el-firmware)
3. [Uso en competencia](#uso-en-competencia)
4. [Qué hace el robot](#qué-hace-el-robot)
5. [LED de la placa](#led-de-la-placa)
6. [Calibración](#calibración)
7. [Ajustes](#ajustes)
8. [Simulación y pruebas](#simulación-y-pruebas)
9. [Estructura del proyecto](#estructura-del-proyecto)
10. [Problemas comunes](#problemas-comunes)

## Conexiones

| Elemento | Pin del Nano |
|---|---|
| Sensor de piso izquierdo (analógico) | A0 |
| Sensor de piso derecho (analógico) | A7 |
| Sensor frontal izquierdo | A2 |
| Sensor frontal central | A3 |
| Sensor frontal derecho | A4 |
| Sensor lateral izquierdo | A1 |
| Sensor lateral derecho | A5 |
| Señal del módulo de arranque (control remoto) | D4 |
| Motor izquierdo: PWM / IN1 / IN2 | D5 / D7 / D6 |
| Motor derecho: PWM / IN1 / IN2 | D10 / D8 / D9 |

El módulo de arranque se alimenta con 5 V y GND del Nano. Su salida va a D4: en `HIGH` el robot pelea y en `LOW` se detiene.

## Cargar el firmware

Necesitas [PlatformIO](https://platformio.org/), como extensión de VS Code o por línea de comandos.

```sh
pio run -e nano -t upload        # firmware de combate
pio device monitor               # monitor serie (solo calibración/registro)
```

En VS Code puedes usar los botones de la barra de PlatformIO: ✓ compila, → carga y 🧪 ejecuta las pruebas.

| Entorno | Para qué sirve |
|---|---|
| `nano` | Firmware de combate (predeterminado). |
| `calibracion` | Muestra los sensores por Serial a 9600 baudios. Los motores no se mueven. |
| `registro` | Combate normal que además envía un registro CSV por Serial a 115200 baudios. |

Para cargar otro entorno: `pio run -e calibracion -t upload`. Después de calibrar, vuelve a cargar `nano`.

## Uso en competencia

### Encendido y rounds

1. **Al encender**, el robot queda en el **round 1**, quieto, esperando la señal del control.
2. **START** en el control: arranca con la apertura del round actual.
3. **STOP** en el control: se detiene de inmediato y **pasa al siguiente round** (1 → 2 → 3 → 1).
4. **Al apagarlo** se reinicia: al volver a encender empieza otra vez en el round 1.

Si el round se desincroniza, apaga y enciende el robot para volver al round 1.

### Colocación y apertura de cada round

| Round | Posición inicial | Apertura del robot |
|---|---|---|
| 1 | En el centro, espalda con espalda en diagonal | Media vuelta rápida hacia la derecha (PWM 200, 630 ms). |
| 2 | En el centro, espalda con espalda en vertical | Media vuelta hacia el lado del sensor lateral que vea al rival; si ninguno lo ve, hacia la izquierda (PWM 200, 630 ms). |
| 3 | En los extremos, de frente | Avanza recto (PWM 180, 300 ms) y ataca en cuanto ve al rival. |

En los rounds 1 y 2, durante los primeros 700 ms los sensores de enemigo no interrumpen el giro. Solo el borde blanco puede cortarlo. Así una detección falsa al arrancar no lo manda a atacar recto.

## Qué hace el robot

El orden de prioridad en cada ciclo es:

1. **STOP**: si el control indica STOP, frena los motores.
2. **Borde**: si un sensor de piso ve blanco, o la lectura indica que está a punto de verlo, retrocede (240–320 ms) y gira para alejarse. Si al terminar ve al rival al frente, vuelve a atacar.
3. **Apertura** del round, como se describe arriba.
4. **Ataque**: con el sensor central, o con los dos frontales laterales a la vez, avanza a PWM 255. Mantiene el empuje 600 ms aunque pierda la señal un momento.
5. **Seguimiento**: si solo lo ve un frontal lateral, un PID con filtro de Kalman corrige el rumbo hacia él.
6. **Lateral**: si lo ve un sensor lateral, pivota hacia ese lado.
7. **Recuperación**: si pierde al rival, lo busca hacia el último lado donde lo vio durante 1,2 s.
8. **Búsqueda**: recorre el dojo en arcos (300 ms) y tramos rectos (50 ms), y cambia de lado cada 2,1 s.

## LED de la placa

| LED | Significado |
|---|---|
| Apagado | Detenido (STOP) |
| Encendido fijo | Avanza |
| Parpadeo lento | Retrocede |
| Parpadeo medio | Gira a la derecha |
| Parpadeo rápido | Gira a la izquierda |

## Calibración

Carga el entorno `calibracion` y abre el monitor serie a 9600 baudios:

```text
Piso I:812 D:798 | Frente I/C/D:010 | Laterales I/D:00 | Remoto:0 | Round:1
```

- **Piso**: anota el valor sobre negro y sobre blanco. Pon `BLANCO` en un punto intermedio, más cerca del negro que del blanco para reaccionar antes. Si el blanco da valores **altos**, cambia `PISO_BLANCO_LOW` a `false`.
- **Sensores de enemigo**: deben marcar `1` solo con un objeto delante. Si marcan al revés, cambia `ENEMIGO_ACTIVE_HIGH`. Si alguno marca `1` sin nada delante (gente o paredes lejos), reduce su alcance.
- **Remoto**: debe pasar a `1` con START y a `0` con STOP. Si va al revés, cambia `REMOTE_ACTIVE_HIGH` a `false`.
- **Motores**: con el firmware `nano` en el suelo, el robot debe avanzar al buscar. Si una rueda gira al revés, cambia `INVERTIR_MOTOR_IZQUIERDO` o `INVERTIR_MOTOR_DERECHO`. Si avanza bien pero gira hacia el lado contrario, cambia `INVERTIR_SENTIDO_GIRO`.

## Ajustes

Todos los parámetros están en [include/Definiciones.h](include/Definiciones.h). Los PWM van de 0 a 255 y los tiempos están en milisegundos.

| Parámetro | Valor | Qué controla |
|---|---|---|
| `ROUND_COMPETENCIA` | 1 | Round con el que arranca al encender (0 desactiva las aperturas). |
| `ROUND_ROTATIVO` | true | Si STOP avanza al siguiente round. |
| `APERTURA_R1_PWM` / `APERTURA_R1_MS` | 200 / 630 | Velocidad y duración del giro del round 1. |
| `APERTURA_R2_PWM` / `APERTURA_R2_MS` | 200 / 630 | Velocidad y duración del giro del round 2. |
| `APERTURA_FRENTE_PWM` / `APERTURA_FRENTE_MS` | 180 / 300 | Avance inicial del round 3. |
| `APERTURA_COMPROMISO_MS` | 700 | Tiempo en que el giro de los rounds 1 y 2 ignora los sensores de enemigo. |
| `BLANCO` | 300 | Umbral del sensor de piso. |
| `VELOCIDAD_BUSQUEDA_PWM` | 130 | Velocidad al buscar. |
| `VELOCIDAD_SEGUIMIENTO_PWM` | 255 | Velocidad al seguir al rival. |
| `VELOCIDAD_RETROCESO_PWM` | 160 | Velocidad al retroceder del borde. |
| `VELOCIDAD_GIRO_PWM` | 140 | Velocidad de los giros. |
| `ESCAPE_RETROCESO_MIN_MS` / `MAX_MS` | 240 / 320 | Duración del retroceso al ver el borde. |
| `ESCAPE_GIRO_MS` | 300 | Giro después de retroceder. |
| `MEMORIA_ATAQUE_MS` | 600 | Cuánto mantiene el ataque tras perder la señal central. |
| `SEGUIMIENTO_PERDIDA_MS` | 1200 | Cuánto busca hacia el último lado antes de volver a la búsqueda general. |
| `PID_DIRECCION_KP` / `KI` / `KD` | 200 / 20 / 3 | Ganancias del PID de seguimiento. |
| `COMPENSACION_MOTOR_IZQ` / `DER` | 100 | Porcentaje de potencia de cada motor, por si uno es más rápido. |

Para calibrar los giros de apertura: si el robot no completa la media vuelta, sube `APERTURA_R1_MS` / `APERTURA_R2_MS`; si se pasa, bájalos. Si subes el PWM, baja el tiempo en la misma proporción.

## Simulación y pruebas

El simulador compila `src/` con un Arduino simulado (`simulacion/support/Arduino.h` y `simulacion/sim.cpp`) y modela el dojo, los motores y los sensores. Se necesitan Python 3.10+ y un compilador de C++ (`c++`).

```sh
pio test                                   # pruebas de regresión (o el botón 🧪)
python3 -m unittest discover -s test       # las mismas pruebas sin PlatformIO

python3 simulacion/simular.py              # lote de combates en 3 escenarios
python3 simulacion/simular.py --param ROUND_COMPETENCIA=0 --n 300
python3 simulacion/competencia.py          # posiciones de los tres rounds

python3 simulacion/lotes.py                # genera simulacion/resultados/visor.html
python3 simulacion/servidor.py             # abre http://127.0.0.1:8765/visor.html
```

- `simular.py` acepta `--param NOMBRE=valor` para probar cambios de `Definiciones.h` sin editarlo. También acepta opciones del entorno como `--mu 0.3` (piso resbaloso), `--bateria 1.3` o `--vel-enemigo 0.6`.
- En el visor puedes reproducir los ejemplos grabados y, con el servidor activo, hacer clic en el dojo para simular un arranque concreto con la apertura de cualquier round.
- El rival simulado no empuja: los resultados sirven para comparar versiones del código, no garantizan el comportamiento del robot real.

## Estructura del proyecto

```text
include/Definiciones.h    pines y parámetros
include/Robot.h           máquina de estados del robot
include/ControlDireccion.h PID + Kalman para seguir al rival
include/Motor.h           control de los dos motores
include/SensorPiso.h      sensores de línea (analógicos)
include/SensorEnemigo.h   sensores de enemigo (digitales)
src/                      implementación
test/                     pruebas de regresión con el simulador
simulacion/               simulador, lotes y visor
```

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| No arranca con START | Polaridad del módulo o cableado de D4 | Revisa `Remoto:` en calibración y `REMOTE_ACTIVE_HIGH`. |
| Arranca recto en vez de girar en los rounds 1/2 | Está en el round 3 | Apaga y enciende para volver al round 1. |
| Ataca al público o a las paredes | Alcance excesivo de los sensores de enemigo | Revisa en calibración qué sensor marca `1` y reduce su alcance. |
| Se sale del dojo | Umbral `BLANCO` mal ajustado | Recalibra con los valores reales del dojo. |
| Gira hacia el lado contrario | Motores cruzados | Cambia `INVERTIR_SENTIDO_GIRO`. |
| `pio test` falla al compilar el simulador | Falta un compilador de C++ | Instala las Xcode Command Line Tools (`xcode-select --install`). |
