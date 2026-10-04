# Predicción del borde ajustada con simulación

El firmware anticipa la transición al blanco a partir de las lecturas ADC del robot. Los parámetros y las velocidades se eligieron comparando lotes de simulación; no recibe la posición, orientación ni distancia geométrica al borde del simulador.

## Comportamiento

Cada 2 ms guarda las lecturas de ambos sensores de piso. Si el ADC se acerca al blanco al menos 50 unidades entre muestras y está dentro de 500 unidades del umbral, estima si alcanzará ese umbral en los siguientes 15 ms:

```
distancia_adc * tiempo_entre_muestras <= acercamiento_adc * 15 ms
```

Si lo estima, inicia el escape antes de alcanzar el umbral blanco. El cálculo respeta `PISO_BLANCO_LOW` y usa enteros, sin división ni coma flotante. Descarta la tendencia después de una maniobra bloqueante o de más de 20 ms sin muestras; también se reinicia al arrancar tras STOP.

Aprende una referencia de negro por sensor mediante una media móvil (7/8 del valor anterior y 1/8 del nuevo), lejos de la transición al blanco. Una lectura que se aleja más de 80 unidades de ese negro hacia el lado contrario al blanco se considera piso incierto y conserva la prioridad de escape. Esto evita aceptar automáticamente como negro el ADC alto que el modelo entrega fuera del dojo. El robot necesita haber observado negro para disponer de esa referencia. La lectura incierta no identifica con certeza el exterior: es una medida conservadora de seguridad.

Ante una predicción, completa el freno inicial y al menos 40 ms de retroceso. Después, puede cancelar el resto del escape para perseguir al rival cuando el piso lleve 20 ms libre y no sea incierto. Ante blanco real se conserva la respuesta anterior de retirada. STOP mantiene prioridad.

Se limitan a PWM **190** el ataque, la búsqueda, el seguimiento, el retroceso, los giros de escape/laterales y el desbloqueo. Las ruedas interiores de seguimiento y ataque pasan a **89/104**, manteniendo la proporción de las curvas anteriores. Se conservaron pausas 100/80/80 ms y tiempos de escape. Esta combinación fue más estable que conservar el ataque a 255.

## Resultados de confirmación

Semillas **501–600**, que no se usaron para elegir el ajuste; 100 corridas por entorno y modo de enemigo, 30 s nominales. Cada fila reúne tres modos: sin enemigo, quieto y móvil. Misma física y colocaciones iniciales entre controladores; motores 750 rpm, masa 300 g y ruedas de 3 cm.

| Entorno | Antes | Predictivo |
|---|---:|---:|
| Todo el dojo | 24/300 | 0/300 |
| Arranques junto al borde | 30/300 | 1/300 |
| Batería +30 %, reductora suave | 149/300 | 4/300 |
| Piso resbaloso μ=0.3 y batería +30 % | 288/300 | 254/300 |
| Total | **491/1200** | **259/1200** |

Son **47 % menos caídas** en este conjunto, y **54/600 → 1/600** en los dos entornos normales. Las corridas con orden de ataque pasan de **739/800 a 766/800** entre los escenarios con enemigo. No equivale a victorias: el modelo no simula empujones ni colisiones. La mejora corresponde al conjunto de predicción, referencia de negro y velocidades; no debe atribuirse solo a la extrapolación.

El lote de selección independiente anterior, con semillas 101–200, dio 490/1200 frente a 265/1200. No se mezclan estas mediciones con los lotes históricos de la respuesta lateral. La adherencia baja sigue causando numerosas caídas, especialmente sin enemigo o con enemigo móvil.

## Reproducir

```sh
python3 simulacion/reducir_caidas.py --n 100 --semilla 501 \
  --candidatos sin_prediccion actual \
  --entornos todo borde bateria_alta resbaloso \
  --salida simulacion/resultados/prediccion/repeticion
python3 -m unittest discover -s test -p 'test_simulacion.py' -v
pio run -e nano
```

La referencia anterior conserva el código en `referencias/Robot_sin_prediccion.cpp.txt` y los parámetros en `referencias/Definiciones_sin_prediccion.h.txt`; el script aplica esos parámetros aunque cambie la configuración actual. Guarda CSV por candidato/entorno/enemigo, resúmenes y metadatos con hashes. Los resultados de confirmación están en `resultados/prediccion/confirmacion/` y la selección en `resultados/prediccion/validacion_segura/`; los resultados y ejecutables generados están ignorados en Git.

Pasan **21 pruebas**, incluidas anticipación antes del blanco con enemigo presente, polaridad ADC inversa, negro constante sin frenadas falsas, lectura incierta que impide volver a atacar y las regresiones de respuesta lateral/escape. El firmware compila para Nano. No se ha cargado al robot.

Los umbrales ADC y el comportamiento fuera de la superficie deben verificarse con lecturas reales del robot. El horizonte de 15 ms estima llegada al umbral ADC, no una distancia física ni una frenada completa garantizada. Dos sensores delanteros no vigilan el borde trasero. En el modelo se declara caída cuando el centro sale del dojo; las esquinas pueden sobresalir antes.
