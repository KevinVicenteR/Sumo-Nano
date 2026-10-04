# Sumo: ataque continuo y persecución en curva

## Ver la simulación actualizada

```sh
python3 simulacion/seguimiento.py --n 300
python3 simulacion/visualizar.py
python3 simulacion/servidor.py
```

Abre http://127.0.0.1:8765/visor.html y pulsa **Reproducir**. El visor arranca con enemigo móvil. Puedes elegir enemigo quieto o ninguno, avanzar de 50 ms en 50 ms y comparar los lotes **Continuo** con **Antes · ataque con pausas**. Para probar otra pose, haz clic en el dojo o escribe X/Y en centímetros y el ángulo; pulsa **Simular este arranque**. El robot completo debe caber dentro del dojo, aunque sus sensores pueden empezar sobre el blanco. El firmware no recibe las coordenadas.

## Cambios del control

El ataque deja de alternar 90 ms de marcha y 30 ms de frenado. Ahora avanza continuamente. El central confirma ataque; si además un frontal lateral indica un rival descentrado, corrige mientras avanza. Esta información antes se ignoraba durante el ataque.

| Acción | Configuración |
|---|---:|
| Ataque recto | ambas ruedas PWM 255, sin pausas |
| Corrección durante ataque | exterior 255; interior 140 |
| Seguimiento frontal lateral / recuperación de frontal perdido | exterior 255; interior 60 |
| Filtro de cambios de dirección | 90 ms |
| Memoria del último contacto | hasta 150 ms |
| Reposicionamiento | solo detecciones laterales o ambiguas persistentes: 40 ms de avance tras 150 ms |
| Escape: frenado antes / después del retroceso / después del giro | 100 / 80 / 80 ms |
| Retroceso adaptativo | mínimo 120 ms; máximo 240 ms; piso libre durante 20 ms |
| Giro de escape con ambos sensores / uno | 150 / 110 ms |

Un frontal inequívoco ya no se interrumpe cada 150 ms para avanzar recto. Si aparece durante un reposicionamiento lateral, retoma el seguimiento inmediatamente. Al perder momentáneamente el frontal conserva un avance curvo hacia el último lado visto, en lugar de volver inmediatamente a un giro sobre su eje. Ambas ruedas avanzan durante las curvas; la exterior mantiene la potencia máxima. Las lecturas alternantes de 10 ms no cambian la dirección cada 10 ms.

Se conservaron los tiempos del escape que el usuario dio por buenos. El blanco tiene prioridad sobre cualquier ataque, curva o reposicionamiento; STOP sigue atendido también dentro de las maniobras de escape. La búsqueda mantiene giro/avance de 40/80 ms.

## Validación final

**12,852 corridas** de 30 s nominales: 12 condiciones del controlador actual y dos lotes anteriores comparables. Se permite completar un escape iniciado antes del límite. Se probaron arranques aleatorios en todo el dojo, junto al borde y una malla de 384 poses. Las tres pruebas nominales suman **2,952 corridas, con 0 caídas**. Cada celda siguiente indica caídas/total y corridas con orden de ataque/total.

| Condiciones | Sin enemigo | Quieto | Móvil |
|---|---:|---:|---:|
| Varios objetos alrededor del dojo | 0/300 · ataque 300/300 | 0/300 · ataque 300/300 | 0/300 · ataque 300/300 |
| Lecturas alternantes · prueba sintética | 0/300 · ataque 0/300 | 0/300 · ataque 0/300 | 0/300 · ataque 0/300 |
| Dos laterales activos · prueba sintética | 0/300 · ataque 0/300 | 0/300 · ataque 0/300 | 0/300 · ataque 0/300 |
| Todo el dojo · arranques aleatorios | 0/300 · ataque 0/300 | 0/300 · ataque 300/300 | 0/300 · ataque 300/300 |
| Malla · 384 posiciones y orientaciones | 0/384 · ataque 0/384 | 0/384 · ataque 384/384 | 0/384 · ataque 384/384 |
| Arranques junto al borde | 0/300 · ataque 0/300 | 0/300 · ataque 300/300 | 0/300 · ataque 300/300 |
| Alcance de 12 cm · junto al borde | 0/300 · ataque 0/300 | 0/300 · ataque 300/300 | 0/300 · ataque 300/300 |
| Batería +30 % · junto al borde | 300/300 · ataque 0/300 | 178/300 · ataque 288/300 | 300/300 · ataque 292/300 |
| Piso resbaloso · junto al borde | 300/300 · ataque 0/300 | 300/300 · ataque 217/300 | 300/300 · ataque 213/300 |
| Extremos combinados | 300/300 · ataque 0/300 | 300/300 · ataque 132/300 | 300/300 · ataque 161/300 |
| Enemigo rápido · todo el dojo | 0/300 · ataque 0/300 | 0/300 · ataque 300/300 | 0/300 · ataque 300/300 |
| Control lento · junto al borde | 68/300 · ataque 0/300 | 6/300 · ataque 300/300 | 6/300 · ataque 300/300 |

Comparación de seguimiento en 300 arranques de todo el dojo, con las mismas semillas y condiciones físicas. «Enemigo al frente» usa la geometría del sensor central; «orden de ataque» usa la telemetría del firmware. Son indicadores de seguimiento, no victorias.

| Enemigo y controlador | Tiempo de enemigo al frente | Orden de ataque por corrida |
|---|---:|---:|
| Quieto · Antes | 15.28 % | 3.23 s |
| Quieto · Continuo | 26.72 % | 5.85 s |
| Móvil · Antes | 27.53 % | 6.05 s |
| Móvil · Continuo | 27.36 % | 6.53 s |

Con enemigo quieto, el tiempo de frente mejora de 15.28 % a 26.72 %. Con el móvil permanece prácticamente igual (27.53 % frente a 27.36 %), mientras el tiempo medio ordenando ataque aumenta de 6.05 a 6.53 s. Esto confirma mayor continuidad de ataque; no demuestra una mejora universal de la persecución móvil ni sustituye la prueba física.

El ataque continuo conserva las frenadas del escape, pero las condiciones extremas siguen produciendo caídas. El visor incluye esos fallos. Dos sensores delanteros no observan el borde trasero; los resultados nominales no garantizan todos los arranques posibles ni la seguridad física a máxima potencia.

## Modelo y reproducción

Dojo circular exterior Ø70 cm, línea blanca 1 cm, motores 750 rpm y masa 300 g. Supuestos: cuerpo 10×10 cm, ruedas Ø3 cm, trocha 8.5 cm, par de bloqueo 0.6 kg·cm por motor, adherencia nominal μ=0.9, negro/blanco ADC 900/100 y alcance de enemigo 40 cm. El freno activo corresponde a ambas entradas HIGH con PWM 255; el modelo distingue frenado eléctrico y rueda libre.

Se compila el código real de `src/` con una interfaz Arduino simulada. La integración física y del reloj usa pasos de 0.1 ms, incluso dentro del escape. El enemigo es cinemático: **no se simulan colisiones, empujones ni victorias**, y los cuerpos pueden solaparse. Una caída significa centro de masa fuera del círculo; las esquinas pueden sobresalir antes. Los objetos externos pueden activar sensores: no hay identificación visual del rival.

Las pruebas de lecturas alternantes y dos laterales fuerzan señales sintéticas; el disco naranja no genera esas señales. Los CSV incluyen pose, semilla, caída, tiempo con enemigo al frente, ataque, velocidad, permanencia cerca del borde y saliente de esquinas. «Cerca del borde» significa centro a más de 26 cm; en una caída se acumula solo hasta ese momento.

Los resultados finales están en `resultados/seguimiento/lotes/`, con parámetros y hashes por lote. La referencia anterior está en `referencias/Robot_ataque_pausado.cpp.txt`. Los primeros ensayos sin corrección durante ataque se conservaron en `resultados/seguimiento-sin-centrado/`. La selección de curvas está en `resultados/persecucion-centrado.json`. Los resultados y ejecutables se ignoran en Git; el código y las referencias necesarias para regenerarlos se conservan.

## Comprobaciones

```sh
python3 -m unittest discover -s test -p 'test_simulacion.py' -v
pio run
```

Pasan 12 pruebas: geometría, poses inválidas, reloj del escape, reproducibilidad, prioridad de blanco, retirada hacia el interior, seguimiento sin inversiones rápidas ni reposicionamiento frontal forzado, desbloqueo lateral y ataque continuo sin pausas periódicas. La API local también se comprobó con enemigo móvil y rechazo de un arranque inválido.

El firmware Nano compila: **146 bytes de RAM y 5120 bytes de flash**. Esta versión no se ha cargado al robot. La polaridad y el umbral de los sensores se ajustan en `Definiciones.h`; `MODO_CALIBRACION=1` permite ver sus lecturas sin mover los motores.
