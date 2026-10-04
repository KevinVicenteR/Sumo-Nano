# Comparación para reducir las caídas

Este informe corresponde al controlador anterior a la predicción del borde. El firmware y sus resultados actuales están descritos en [PREDICCION_BORDE.md](PREDICCION_BORDE.md). Para reproducir la referencia anterior se conservan `referencias/Robot_sin_prediccion.cpp.txt` y `referencias/Definiciones_sin_prediccion.h.txt`.

Fecha: 4 de octubre de 2026. Se evaluó el controlador que interrumpe el escape al detectar enemigo con piso libre. No se cambiaron los parámetros del firmware instalado en `include/Definiciones.h` ni se cargó firmware al robot.

## Ajuste recomendado

Bajar únicamente `Velocidad_estandar` (retroceso) y `VELOCIDAD_GIRO_ESCAPE` de PWM 255 a **180**. Conservar ataque, búsqueda, pausas y tiempos actuales. En la validación normal redujo las caídas de **54/600 a 40/600** (26 % menos), manteniendo **394/400** corridas con orden de ataque entre los escenarios con enemigo. El tiempo medio con orden de ataque fue 4.54 s frente a 4.56 s por corrida con enemigo. Estas métricas no evalúan victorias ni empujones.

El resultado es especialmente claro sin enemigo: **11/200 → 0/200**. Con enemigo quieto: **18/200 → 16/200**. Con enemigo móvil: **25/200 → 24/200**; esa diferencia pequeña no demuestra una mejora robusta del seguimiento.

## Validación independiente

100 semillas nuevas (101–200) por combinación de entorno y enemigo; 30 s nominales; modos sin enemigo, quieto y móvil. Cada fila reúne 300 corridas. Se usaron las mismas semillas, modelo físico y colocaciones en cada comparación.

| Entorno | Actual | Escape PWM 180 | Velocidades PWM 190 |
|---|---:|---:|---:|
| Todo el dojo | 31/300 | 25/300 | 29/300 |
| Arranques junto al borde | 23/300 | 15/300 | 29/300 |
| Batería +30 %, reductora suave | 147/300 | 142/300 | 12/300 |
| Piso resbaloso μ=0.3 y batería +30 % | 289/300 | 289/300 | 273/300 |

La variante de velocidades 190 limita retroceso, giro de escape, búsqueda, seguimiento, ataque, desbloqueo y giro lateral a 190; escala las ruedas interiores de seguimiento/ataque a 89/104. Aunque mejora mucho con batería alta, en condiciones normales con enemigo móvil empeora de **25/200 a 56/200** caídas. Por eso no se recomienda como ajuste general. La variante de escape 180 conserva el ataque a 255 y la interrupción por detección de enemigo.

## Ajustes descartados en la exploración

30 semillas (1–30), 30 s nominales, todo el dojo y junto al borde; tres modos de enemigo: 180 corridas por candidato.

| Ajuste | Caídas / 180 |
|---|---:|
| Actual | 14 |
| Escape PWM 180 | 8 |
| Escape PWM 180 y retroceso mínimo/máximo 200/300 ms | 8 |
| Escape PWM 180 y piso libre estable 60 ms | 8 |
| Pausa inicial 150 ms | 10 |
| Escape PWM 150 | 15 |
| Retroceso mínimo/máximo 200/300 ms | 16 |
| Ataque PWM 180 | 16 |
| Escape y ataque PWM 180 | 16 |
| Mezcla conservadora de velocidades, pausas y detección | 20 |
| Piso libre estable 60 ms | 21 |
| Pausas 40/30/30 ms | 22 |
| Búsqueda PWM 160 y giro de seguimiento 180 | 27 |
| Umbral blanco 500 y margen cercano 80 | 29 |
| Retroceso mínimo/máximo 60/120 ms | 41 |

El nombre «detección temprana» del script describe una hipótesis: subir el umbral no mejoró las caídas con enemigo. El margen cercano solo actúa durante la búsqueda. No protege el ataque directamente.

## Causas observadas y siguientes mejoras

En la semilla 21, sin enemigo y junto al borde, el controlador actual detecta blanco a los 15.13 s y entra al freno a los 15.14 s. El centro cruza el límite a los 15.167 s, todavía durante la pausa de frenado. Los sensores ya están fuera de la línea y vuelven a entregar un ADC alto. En piso resbaloso esa misma semilla cae a los 1.857 s durante el freno. Las trayectorias se guardaron en `resultados/reducir_caidas/diagnostico/`.

Esto apunta a inercia y distancia de frenado; no se resuelve simplemente acortando esperas. Mejoras que quedan por implementar y medir:

- Frenado anticipado también durante el ataque, cuando el ADC empiece a acercarse al blanco, con histéresis para no oscilar. Probarlo por separado: cambiar solo el umbral resultó peor.
- Mantener un estado de emergencia después de ver blanco para no confundir una lectura alta fuera del dojo con piso negro seguro. La interrupción por enemigo necesita considerar esta ambigüedad.
- Añadir sensores de piso traseros para vigilar el retroceso y los giros. El modelo actual solo tiene dos delanteros; esta alternativa requiere hardware y ampliar la simulación.
- Calibrar adherencia, freno, reductora y batería con mediciones del robot. Los escenarios resbalosos siguen fallando masivamente incluso bajando velocidades.

No se garantiza permanecer dentro del dojo. El simulador declara caída cuando el centro sale del círculo; las esquinas pueden sobresalir antes. El rival no produce colisiones ni empujones.

## Repetir la comparación

```sh
python3 simulacion/reducir_caidas.py --n 100 --semilla 101 \
  --candidatos actual escape_moderado limite_190 \
  --entornos todo borde bateria_alta resbaloso \
  --salida simulacion/resultados/reducir_caidas/repeticion
```

El script aplica variantes únicamente a copias de los encabezados para compilar cada ejecutable. Guarda CSV completos, resúmenes y metadatos con parámetros, condiciones y hashes de fuentes. Los resultados generados están ignorados en Git. Las 17 pruebas existentes siguen pasando.
