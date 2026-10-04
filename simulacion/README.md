## Controlador actual: PID/Kalman con PWM 255

El firmware actual usa PWM 255 en ambos motores durante todo movimiento, según la selección explícita del usuario. El central activa ataque recto inmediato; el lateral pivota para alinear; un frontal descentrado usa PID/Kalman. Corrige la dirección alternando avance y pivote a plena potencia; el escape es una máquina de estados sin pausas programadas. Una detección repetida del borde dentro de 900 ms obliga a completar 200 ms de giro antes de retomar al enemigo. STOP conserva prioridad.

Ejecutar `python3 simulacion/agresivo.py --n 60` para reproducir los lotes actuales y `python3 -m unittest discover -s test -v` para las regresiones. El visor prioriza `resultados/agresivo/lotes`; iniciar `python3 simulacion/servidor.py` permite probar posiciones manuales con el firmware actual, sin Kalman o con control proporcional.

Los informes siguientes y los scripts `optimizar_seguridad.py`, `reducir_caidas.py`, `fluidez.py` y `laterales.py` describen controladores anteriores. Sus parámetros de velocidades y pausas no representan el controlador actual. El resultado histórico de cero caídas a potencia reducida no es un resultado a PWM 255. Consultar [PID_AGRESIVO.md](PID_AGRESIVO.md) para las mediciones actuales.

# Control seguro y simulación del Nano

El control actual obtuvo **0 caídas en 5,052 corridas**, incluyendo los 14 entornos de simulación y una malla de 384 poses por modo de enemigo. Conserva movimiento y ataque: en la malla con enemigo atacó en 766/768 corridas. Los resultados y sus límites están en [SEGURIDAD.md](SEGURIDAD.md).

## Configuración actual

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
