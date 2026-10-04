# Análisis del video 15.20.54 · 4 de octubre de 2026

Video de 40,498 s, correspondiente según la secuencia de la conversación a la revisión cargada de 8.528 bytes. Se examinaron una hoja general y fotogramas exactos en intervalos 9–13 s y 24–33 s, con tolerancias temporales de AVAssetImageGenerator a cero. No hay telemetría sincronizada de sensores ni órdenes de motor.

| Intervalo aproximado | Observación | Alcance |
|---|---|---|
| 9–10,8 s | Permanece enfrentado y próximo al rival | La imagen no mide PWM, fuerza ni detección |
| 11–11,5 s | Se separa hacia atrás y después gira, sobre zona visualmente negra | Compatible con escape falso; no demuestra su estado interno |
| 13–24 s | Repite orientación cerca del borde mientras el rival permanece más al interior | Seguimiento y recuperación ineficientes observables |
| 24,75–25,5 s | Se aproxima, hace contacto y desplaza al rival hacia el borde | Existe capacidad de aproximación y empuje en esta secuencia |
| 26–32,6 s | Repite giros y aproximaciones a la franja, sin retirarse de forma sostenida al interior | La salida del borde no queda consolidada; no se confirma una caída completa |

## Hallazgos del código y posibles causas

La búsqueda está configurada con 220 ms de pivote y solo 20 ms de avance (aproximadamente 92% de cada ciclo en pivote), alternando lado cada 1.280 ms. Esta configuración puede limitar la exploración aunque haya bajado las caídas del lote simulado. El control de giro no mide orientación física ni velocidad de rueda; los tiempos no aseguran un ángulo de salida real.

Una detección de piso incierto, blanco o predicción prevalece sobre cualquier frontal. Por tanto, incluso tres frontales activos no cancelan un escape que sigue viendo peligro. El retroceso observado en negro requiere comprobar ADC reales en contacto: iluminación, inclinación al tocar la pala rival y señales espurias son hipótesis, no causas confirmadas.

El último lado frontal se conserva al recibir central aislado y puede reutilizarse hasta 1.200 ms tras perder señal. Esa memoria puede orientar hacia una posición obsoleta. Un lateral persistente también ordena pivote continuo mientras no aparezca frontal. Falta determinar si los giros del video corresponden a estas ramas o al escape.

## Prioridad de diagnóstico

Registrar simultáneamente piso ADC, cinco sensores de enemigo, RUN, estado de escape y órdenes de motor en el instante de separarse del rival sobre negro. Verificar negro y blanco con motores en movimiento y robot en contacto, además del mapa lateral y sentido físico de avance. Después ajustar salida del borde y recuperación del rival con esa evidencia. No se modificó ni cargó otro firmware como parte de este análisis.

La simulación actual no modela empujones, colisiones, inclinación al tocar palas ni interferencia eléctrica real; sus 21/270 caídas no validan el comportamiento de ataque mostrado.
