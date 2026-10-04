# Avance y ataque fluidos

Se suavizan las transiciones del movimiento hacia adelante, conservando la predicción del borde y el límite PWM 190.

- Cada rueda cambia como máximo 4 unidades PWM por milisegundo entre órdenes de avance y curva. La rampa usa el reloj y no añade esperas bloqueantes. Una transición de 190 a 104 tarda aproximadamente 22 ms.
- Cuando el central pierde al enemigo brevemente, conserva el ataque hasta 60 ms desde la última detección. Un enemigo lateral tiene prioridad sobre esa memoria. El borde, el piso incierto, la predicción y STOP se revisan antes del ataque y cancelan la memoria.
- La búsqueda zigzag usa curvas con ambas ruedas hacia adelante, intercaladas con avance recto. Reduce las inversiones entre búsqueda y ataque. `BUSQUEDA_FLUIDA false` permite comparar con la búsqueda anterior.
- El freno, el retroceso de seguridad y la orientación ante enemigo lateral conservan respuesta directa. La rampa se reinicia después de esas maniobras para que no retrase las órdenes de seguridad. La primera orden de avance tras una maniobra se aplica directamente.

Parámetros nuevos en `include/Definiciones.h`: `RAMPA_AVANCE_PWM_MS 4`, `MEMORIA_ATAQUE_MS 60` y `BUSQUEDA_FLUIDA true`.

## Comparación de simulación

100 semillas (501–600) por combinación de entorno y enemigo; 30 s nominales, motores 750 rpm. Cuatro entornos: todo el dojo, arranques junto al borde, batería alta y piso resbaloso. Tres modos de enemigo: ninguno, quieto y móvil.

| Controlador | Caídas totales | Caídas normales | Corridas con orden de ataque |
|---|---:|---:|---:|
| Predictivo anterior | 259/1200 | 1/600 | 766/800 |
| Fluido con curvas de búsqueda | 256/1200 | 0/600 | 769/800 |
| Fluido con búsqueda anterior | 258/1200 | 2/600 | 764/800 |

La diferencia pequeña de caídas no demuestra una mejora general de seguridad. El objetivo de este cambio es la continuidad de las órdenes de motor. Las caídas con baja adherencia siguen siendo frecuentes. En la primera trayectoria de búsqueda sin enemigo de la semilla 501, las inversiones de ruedas durante el primer segundo bajaron de 11 a 0; ese ejemplo no representa todos los arranques ni incluye garantías ante el borde.

```sh
python3 simulacion/fluidez.py --n 100 --semilla 501
python3 -m unittest discover -s test -p 'test_simulacion.py' -v
pio run -e nano
```

El script compara contra `referencias/Robot_prediccion_sin_fluidez.cpp.txt` con los mismos parámetros actuales y guarda CSV, trayectorias y resúmenes en `resultados/fluidez/`. Las variantes nuevas añaden tres pruebas: continuidad ante central intermitente, cambio gradual del PWM al entrar/salir de una curva de ataque y búsqueda sin invertir ruedas. Pasan **24 pruebas**. Compila para Nano con **181 bytes de RAM y 6910 bytes de flash**. No se ha cargado al robot.
