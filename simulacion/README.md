## Firmware cargado

Round1 cargado y verificado enNano (9.122bytes). Apertura curva derecha desdeSTART; enemigo/piso/STOPla interrumpen. Incluye todas las correcciones de búsqueda, retirada y empuje. Validación física pendiente. Las notas de carga pendientes que siguen son históricas.

## Competencia integrada en código

Aperturas por `ROUND_COMPETENCIA`:1curva derecha,2curva izquierda,3avance recto. Predeterminado1; entornosPlatformIO `round1`, `round2`, `round3`. Interrumpibles por enemigo, piso ySTOP.29pruebas;0caídas y ataque360/360corridas de competencia. Firmware preparado, no cargado (Nano ausente). Ver [COMPETENCIA.md](COMPETENCIA.md).

## Arranques de competencia

Se añadieron las tres poses aproximadas de la imagen y pruebas de inicio inmediato desdeRUN: [COMPETENCIA.md](COMPETENCIA.md). Ejecutar `python3 simulacion/competencia.py`:360corridas,0caídas,ataque360/360 en ese modelo. Distancias supuestas; no garantiza comportamiento físico. Pasan28regresiones.

## Revisión vigente: más retirada, ataque al liberar piso

Retirada240–320ms aPWM160; recuperación100–150ms. El frontal puede interrumpir escape tras80ms de piso libre, desde120ms de retirada, sin completar giro obligatorio. Ataque255 y memoria600ms.0/270caídas en lote; pendiente de cargar porNano ausente. Ver [SEGUIMIENTO_ACTUAL.md](SEGUIMIENTO_ACTUAL.md). Las siguientes versiones son históricas.

## Empuje sostenido vigente

El ataque mantienePWM255 durante pérdidas de señal de hasta600ms, incluso si solo queda señal lateral, tras detectar al rival alineado. Borde y STOP prevalecen.27pruebas pasan;0/270caídas simuladas. Todavía sin cargar (Nano no conectado); las secciones siguientes son históricas. Ver [SEGUIMIENTO_ACTUAL.md](SEGUIMIENTO_ACTUAL.md).

## Configuración vigente

Búsqueda siempre con ambas ruedas hacia adelante, curvas130/60 y recto130/130. Retroceso de borde200–280ms aPWM160; recuperación80–120ms. Seguimiento y ataque255; giros140. Pérdida lateral: hasta250ms de pivote y luego aproximación.25pruebas;0/270caídas simuladas y180/180corridas con rival registraron ataque. Revisión sin cargar, Nano no conectado. Ver [SEGUIMIENTO_ACTUAL.md](SEGUIMIENTO_ACTUAL.md). Las secciones siguientes conservan perfiles anteriores.

## Configuración actual: seguimiento y ataque al máximo

Seguimiento frontal PWM255, búsqueda130, retroceso160 y giros140. Tiempos adaptados: retirada160–220ms, recuperación60–90ms, giro300ms; búsqueda300ms de barrido y50ms de avance. Pasan23pruebas y0/270caídas en el lote; prueba física pendiente y revisión sin cargar porqueNano no aparece porUSB. Ver [SEGUIMIENTO_ACTUAL.md](SEGUIMIENTO_ACTUAL.md). Los perfiles siguientes son históricos.

## Revisión actual: máximo solo al atacar

Por petición del usuario, búsqueda PWM130, seguimiento180, retroceso160 y giros140; ataque recto255. Compila y pasan23pruebas. El lote actual obtuvo0caídas/270corridas (tres entornos, tres modos y30semillas); no garantiza cero en el robot real. No cargada aún: porUSB apareció Leonardo en lugar deNano. Los perfiles siguientes son históricos.

## Controlador actual: PID/Kalman con PWM 255

El firmware actual usa PWM 255 en ambos motores durante todo movimiento, según la selección explícita del usuario. El central aislado y los tres frontales simultáneos activan ataque recto inmediato; el lateral pivota para alinear; un frontal descentrado usa PID/Kalman. Corrige la dirección alternando avance y pivote a plena potencia; el escape es una máquina de estados sin pausas programadas. Una detección repetida del borde dentro de 900 ms obliga a completar 200 ms de giro antes de retomar al enemigo. El giro con borde persistente se limita a 350 ms y se reintenta con retirada de 40–60 ms. La retirada inicial dura 100–140 ms y la persecución tras perder señal, 1.200 ms. La búsqueda barre 220 ms y avanza 20 ms, alternando lados. STOP conserva prioridad.

Ejecutar `python3 simulacion/seguimiento.py --n 30` para reproducir los lotes actuales y `python3 -m unittest discover -s test -v` para las regresiones. El visor prioriza `resultados/seguimiento/lotes`; iniciar `python3 simulacion/servidor.py` permite probar posiciones manuales con el firmware actual, sin Kalman o con control proporcional.

Los informes siguientes y los scripts `optimizar_seguridad.py`, `reducir_caidas.py`, `fluidez.py` y `laterales.py` describen controladores anteriores. Sus parámetros de velocidades y pausas no representan el controlador actual. El resultado histórico de cero caídas a potencia reducida no es un resultado a PWM 255. Consultar [PID_AGRESIVO.md](PID_AGRESIVO.md) para las mediciones anteriores y [SEGUIMIENTO_ACTUAL.md](SEGUIMIENTO_ACTUAL.md) para la versión cargada.

# Perfil histórico a potencia reducida

El control histórico obtuvo **0 caídas en 5,052 corridas**, incluyendo los 14 entornos de simulación y una malla de 384 poses por modo de enemigo. Conserva movimiento y ataque: en la malla con enemigo atacó en 766/768 corridas. Los resultados y sus límites están en [SEGURIDAD.md](SEGURIDAD.md).

## Configuración histórica

Avance y ataque a PWM **55**; orientación y giros a **100**. El escape frena 180 ms, retrocede brevemente (20–60 ms), frena antes de pivotar y orienta al robot para evitar repetir retrocesos hacia un borde trasero que los sensores delanteros no ven. El enemigo interrumpe las fases restantes cuando el piso está libre. STOP y el borde mantienen prioridad.

El central confirma ataque recto y continuo. Un frontal lateral orienta con pivote; las pérdidas breves del central se toleran hasta 60 ms. La búsqueda alterna orientación y avance, con frenado antes de cambiar a pivote. Se mantiene la predicción del borde con lecturas ADC reales y una referencia de negro aprendida por cada sensor. No se usan las coordenadas del simulador para decidir movimientos.

El perfil es más lento que las versiones anteriores: se priorizó eliminar las caídas de los lotes, especialmente con baja adherencia, ruedas grandes y batería alta. El firmware todavía no se ha cargado al robot.

## Ver los resultados

```sh
python3 simulacion/visualizar.py
python3 simulacion/servidor.py
```

Abre http://127.0.0.1:8765/visor.html. El visor muestra los lotes de seguridad cuando están disponibles. Permite reproducir la trayectoria y ejecutar una corrida manual con X/Y en centímetros, orientación y semilla. La API manual compila el firmware actual al iniciar el servidor; reinícialo si estaba abierto antes de cambiar el código.

Para regenerar todos los lotes y el visor, usa el comando completo de [SEGURIDAD.md](SEGURIDAD.md). Los resultados y ejecutables generados se ignoran en Git. `optimizar_seguridad.py --exigir-cero` falla si encuentra una caída.

## Pruebas

```sh
python3 -m unittest discover -s test -p 'test_simulacion.py' -v
pio run -e nano
```

Pasan **26 pruebas**. La simulación compila las fuentes reales de `src/` con una interfaz Arduino; el reloj y la física siguen avanzando también durante los escapes. No cambia el criterio de caída para obtener cero.

## Modelo y alcance

Dojo Ø70 cm, línea blanca 1 cm, robot de 10×10 cm, motores 750 rpm, masa 300 g, ruedas de 3 cm, trocha 8.5 cm y par de 0.6 kg·cm. Los entornos extremos cambian adherencia, batería, tamaño de rueda o sobrecosto del ciclo según `arranques.py`. Se diferencia freno eléctrico y rueda libre. El rival es cinemático: no hay empujones ni colisiones. Una caída significa que el centro salió del círculo; el cuerpo puede sobresalir antes. Dos sensores delanteros no vigilan el borde trasero.

Los cero fallos pertenecen a los lotes medidos; no garantizan seguridad en cualquier condición ni en el robot real.

## Historial

Los informes anteriores corresponden a otras configuraciones y no deben mezclarse con la validación actual:

- [FLUIDEZ.md](FLUIDEZ.md): suavización y búsqueda en curvas a PWM 190.
- [PREDICCION_BORDE.md](PREDICCION_BORDE.md): introducción del predictor ADC y referencia de negro.
- [REDUCIR_CAIDAS.md](REDUCIR_CAIDAS.md): exploración previa de velocidades y tiempos.

## Lecturas del Nano por USB

`pio run -e calibracion -t upload --upload-port /dev/cu.usbserial-1130` carga únicamente el diagnóstico con motores detenidos. Leer a 9600 baudios. El entorno `nano` sigue siendo el firmware de combate y el entorno predeterminado; `calibracion` activa `MODO_CALIBRACION=1` mediante una opción de compilación. Tras medir, se debe cargar `nano` para volver a combatir. El puerto puede cambiar al reconectar.
