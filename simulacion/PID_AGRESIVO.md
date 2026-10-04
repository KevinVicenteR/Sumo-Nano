# Ataque directo a PWM 255

El controlador mantiene PWM 255 en ambos motores durante movimiento. STOP y calibración los detienen. El firmware nuevo se compiló localmente; no se cargó automáticamente al robot.

## Corrección tras el video de 12:19:58

En el video de 52,93 s hay un rival dentro del dojo. El robot rojo se aproxima, gira y se aleja en varias ocasiones; alrededor de 4 s aparece fuera del dojo. Las imágenes no muestran niveles eléctricos ni permiten confirmar la causa física.

Cambios del control:

- El frontal central ordena inmediatamente avance recto (+255,+255), cancelando cualquier salida pendiente del PID. Las detecciones laterales simultáneas no desvían ese ataque.
- Ambos frontales permiten ataque recto solo tras 4 ms de detección conjunta. Esto evita interpretar lecturas tomadas a ambos lados de una transición como una confirmación doble.
- Un lateral ordena pivote completo hacia el rival hasta recuperar un frontal. Mezclar avance en esta etapa podía producir una órbita alrededor del objetivo.
- Un único frontal descentrado conserva PID y Kalman. Su detección interrumpe la memoria de ataque recto; no espera los 60 ms de esa memoria para orientar.
- El escape del borde y STOP conservan prioridad; el escape repetido exige completar el giro de salida. No se introducen pausas programadas.

El PID controla dirección inferida de sensores digitales, no RPM ni velocidad angular medida. No hay encoders. La corrección del frontal descentrado reparte periodos de 12 ms entre avance y pivote; las amplitudes siguen siendo 255 y la velocidad efectiva cambia con las inversiones. La predicción del borde usa tendencia ADC y negro aprendido, sin coordenadas del simulador.

## Validación

15 pruebas correctas: central y frontales adicionales, entrada desde lateral/PID al ataque recto, memoria y cambios de lado, alternancia sin falsos ataques dobles, prioridad del piso, escape repetido, STOP, saturación del PID y ambas polaridades del piso. Una prueba geométrica verifica que un ataque alineado se aproxima a menos de 10 cm del objetivo simulado. El modo de calibración también compila en el simulador y mantiene los motores detenidos.

Nano: compilación correcta, 189 bytes de RAM y 8.116 bytes de flash. Las pruebas del modelo no verifican empuje físico ni el coste real de operaciones float en AVR.

## Comprobación necesaria en el robot

Con `MODO_CALIBRACION=1`, cargar el firmware y abrir Serial a 9600 baudios. Los motores quedan detenidos. `RAW FI/FC/FD/LI/LD` muestra las cinco entradas sin interpretar; el segundo dígito corresponde al central. Comparar sin rival y con el rival a unos 10 cm enfrente:

| Central sin rival → con rival | Configuración |
|---|---|
| 1 → 0 | `ENEMIGO_ACTIVE_HIGH false` |
| 0 → 1 | `ENEMIGO_ACTIVE_HIGH true` |
| No cambia | No se recibe una detección central; comprobar pin, alcance y conexión antes de atribuirlo al PID. |

No se cambió la polaridad por deducción del video. Si la entrada central se activa y el robot se aleja con la orden de avance recto, hay que comprobar el sentido físico de los motores frente a `INVERTIR_MOTOR_*`. Las lecturas de piso sobre negro y blanco permiten comprobar el umbral y su polaridad. Volver a `MODO_CALIBRACION=0` antes de combatir.

## Lotes actuales

Comando: `python3 simulacion/agresivo.py --n 60`. Combates de 30 s; 14 escenarios × 3 modos, con 384 poses por modo en la malla. Las pruebas sintéticas no representan rivales físicos. La caída se define como centro fuera del círculo.

| Escenario | Sin enemigo | Quieto | Móvil |
|---|---:|---:|---:|
| objetos | 0/60 | 0/60 | 0/60 |
| alternante | 0/60 | 0/60 | 0/60 |
| lateral_izquierdo | 0/60 | 0/60 | 0/60 |
| lateral_derecho | 0/60 | 0/60 | 0/60 |
| laterales | 0/60 | 0/60 | 0/60 |
| todo | 0/60 | 13/60 | 5/60 |
| malla | 1/384 | 63/384 | 52/384 |
| borde | 0/60 | 11/60 | 7/60 |
| sensor_corto | 0/60 | 4/60 | 2/60 |
| bateria_alta | 0/60 | 35/60 | 38/60 |
| resbaloso | 11/60 | 58/60 | 59/60 |
| combinado | 8/60 | 59/60 | 59/60 |
| enemigo_rapido | 0/60 | 13/60 | 14/60 |
| control_lento | 0/60 | 10/60 | 11/60 |

**533 caídas en 3.492 corridas, frente a 414 de la versión anterior a este cambio. No se alcanzó cero caídas.** El cambio da prioridad al avance recto confirmado y aumenta las caídas en varios escenarios; no se presenta como una mejora de seguridad. Los lotes incluyen batería alta y adherencia baja, donde el ataque a PWM 255 sigue fallando mucho. El resultado histórico de cero caídas corresponde a menor potencia.

Las filas `antes_*` ejecutan el firmware recibido antes de PID/Kalman con sus velocidades originales inferiores; no son una comparación de algoritmos a potencia igual. El estado «Ataca» significa que se ordenó ataque, no que se produjo un empuje: el enemigo del modelo es cinemático y no se simulan colisiones ni victorias.
