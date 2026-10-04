# Estado cargado: competencia round1

Se cargó `round1` en el Nano y avrdude verificó9.122bytes por `/dev/cu.usbserial-1130`. Incluye apertura curva derecha (hasta900ms), búsqueda hacia adelante, retirada240–320ms aPWM160, interrupción por frontal con piso libre, seguimiento/ataque255 y empuje600ms. STOP continúa prioritario. No cambia de round automáticamente:round2/3requieren seleccionar firmware.29pruebas y360corridas de competencia aprobadas; verificación física pendiente.

## Detalle e historial

# Aperturas de competencia vigentes

La revisión actual integra las tres aperturas descritas en [COMPETENCIA.md](COMPETENCIA.md), conservando retirada larga, empuje600ms y búsqueda sin inversión. Selección de round antes de cargar; no incrementa automáticamente porSTOP.29pruebas y seis entornos compilados. Las360corridas con cada round correspondiente dieron0caídas y ataque360/360; supuestos geométricos y modelo sin contacto limitan la conclusión. No cargado porqueNano no aparece porUSB.

## Historial anterior a integrar aperturas

# Revisión actual: retirada más larga y frontal que cancela escape

Retirada inicial240–320ms aPWM160, antes200–280ms; recuperaciones100–150ms, antes80–120ms. Una detección frontal cancela retroceso desde120ms si lleva80ms continuos con piso libre, y cancela giro tan pronto se confirma ese piso libre. No exige completar el giro de borde repetido si hay frontal. Los tiempos de retirada son objetivos/máximos: se acortan expresamente para retomar al rival. Laterales orientan hacia el objetivo, pero no cancelan escape sin frontal.

Ataque/seguimiento255 y memoria de empuje600ms. Si central o ambos frontales confirmados detectan, ataque recto; un frontal descentrado permite corregir hacia él. No ignora piso blanco ni STOP.

Lote actual270corridas:0caídas y ataque180/180 con rival. La variante conPWM180 de retroceso produjo2caídas sin rival y se descartó. Los resultados no garantizan cero físico ni simulan empujones/contactos. Revisión no cargada: Nano ausente porUSB.

## Historial

# Revisión actual: empuje sostenido

Memoria de ataque frontal alineado600ms (antes180). Durante ese intervalo, pérdida completa de enemigo o señal únicamente lateral conserva avance255/255; una detección frontal descentrada permite corregir. La memoria no se renueva a sí misma: requiere detección frontal central o doble confirmada. Borde y STOP cancelan el empuje. Sin una detección alineada previa, un lateral sigue orientando para adquirir frontal.

27pruebas aprobadas, incluidas pérdida frontal400ms y sustitución transitoria por lateral400ms sin interrupción del empuje. Compilación194bytesRAM,8.904bytesflash. Lote270corridas:0caídas y ataque180/180 con rival; no garantiza cero físico ni simula contactos o empujones. No cargada: Nano ausente porUSB. Si el abandono del ataque real se debe a falsa detección de piso, esta memoria no lo resuelve: hace falta registro en movimiento.

## Historial

# Revisión actual: búsqueda hacia adelante y recuperación lateral

Búsqueda con órdenes positivas en ambas ruedas: exterior130/interior60 durante300ms y recto130/130 durante50ms. Alterna dirección cada2.100ms. No invierte las ruedas durante búsqueda; el escape por piso conserva prioridad y sí puede retroceder.

Retroceso de borde200–280ms, recuperaciones80–120ms; PWM160. Giros de escape y lateral140. Seguimiento frontal y ataque255. Memoria de ataque180ms. Una detección lateral persistente orienta hasta que aparezca frontal. Si pierde la señal lateral, pivota como máximo250ms desde la última detección y luego sigue con corrección frontal equivalente durante la recuperación total1.200ms. Central aislado borra la referencia de pivote lateral antigua, para que una pérdida posterior no reinicie ese pivote. No ataca recto a ciegas mientras únicamente ve un lateral.

25pruebas aprobadas;194bytesRAM y8.918bytesflash. Lote270corridas:0caídas y ataque en180/180corridas con rival. Tres entornos,30semillas por modo; no garantiza cero caídas físicas ni cubre todos los extremos, empujones o colisiones. No cargada: no apareceNano porUSB.

## Historial

# Seguimiento máximo y tiempos adaptados · revisión actual

Seguimiento frontal descentrado y ataque recto PWM255; búsqueda130, retroceso160 y giro lateral/escape140. Tiempos ajustados para potencia reducida: retirada160–220ms, recuperación60–90ms, giro normal300ms, giro mínimo ante borde repetido280ms, reintento por peligro persistente500ms. Búsqueda: barrido300ms y avance50ms, cambio de lado cada2.100ms. Persecución perdida1.200ms y memoria de ataque120ms se conservan porque dependen de la señal, no de completar un giro físico.

23pruebas aprobadas;194bytesRAM y8.658bytesflash. Lote de270corridas:0caídas, igual que el perfil de seguimiento180. Ataque en179/180corridas con rival; en el perfil previo176/180. Esto no garantiza cero caídas físicas ni valida todos los entornos extremos. No cargada: no aparece el Nano porUSB.

## Historial de revisiones

# Revisión actual: velocidad reducida, ataque máximo

Configuración: búsqueda130, seguimiento180, retroceso160, giros140, ataque recto255. Compilación Nano:194bytesRAM y8.646bytesflash;23pruebas pasan. No cargada: apareceArduinoLeonardo porUSB, noNano.

En las mismas270corridas del lote anterior obtuvo0caídas (antes21). Detección de ataque en176/180corridas con rival. Los cuatro casos sin ataque son dos semillas de rival estático en todo el dojo y dos en enemigo rápido. Son tres entornos y30semillas por combinación, sin colisiones ni empujones; no garantiza cero caídas físicas ni valida todo el conjunto de entornos extremos. Reproducir con `python3 simulacion/seguimiento.py --n 30`.

## Informe de la versión anterior

# Seguimiento cargado · 4 de octubre de 2026

La versión actual corrige el giro contrario reportado por el usuario, conserva avance y retroceso, sigue la detección lateral sin avance forzado y recuerda el último lado durante 1.200 ms tras perder al rival. Central aislado activa avance; central con un frontal descentrado corrige mediante PID/Kalman. PWM 255 en ambos motores durante movimiento; STOP y protección del borde conservan prioridad.

Compilación verificada: 8.528 bytes flash, 194 bytes RAM. Carga verificada por avrdude: 8.528 bytes por `/dev/cu.usbserial-1130`, tras reconectar el usuario el Nano. Pasan 23 pruebas de regresión. Falta verificar físicamente el seguimiento y medir la franja blanca.

## Simulación actual

Reproducción: `python3 simulacion/seguimiento.py --n 30`. Son 270 corridas: tres entornos, tres modos de rival y 30 semillas por combinación.

| Entorno | Sin rival | Rival estático | Rival errante |
|---|---:|---:|---:|
| Todo el dojo | 0/30 | 1/30 | 3/30 |
| Arranque junto al borde | 1/30 | 1/30 | 7/30 |
| Enemigo rápido | 0/30 | 1/30 | 7/30 |

La tabla indica caídas: 21/270 en total, frente a 36/270 en la versión inmediatamente anterior, con las mismas semillas y entornos. No se ha alcanzado cero caídas a máxima potencia.

El modelo físico usa canales de motor intercambiados para representar el giro contrario observado sin alterar el avance; el cableado no se ha medido independientemente. Esta hipótesis debe confirmarse en el robot. Los informes históricos usan otros perfiles o modelos y no constituyen comparaciones exactas con esta versión. El rival simulado no empuja ni colisiona físicamente.

## Escape acotado y tres frontales

El giro con peligro persistente dura como máximo 350 ms; después se retira 40–60 ms y selecciona el giro según el sensor de piso activo, alternando si ambos ven peligro. Reevalúa STOP y piso en cada ciclo, sin pausas bloqueantes. El borde repetido conserva 200 ms mínimos de orientación. Solo retoma ataque tras 80 ms de piso libre. Los tres frontales simultáneos ordenan avance recto inmediatamente después de liberar el escape y reinician el PID y la referencia lateral. No se garantiza que esta maniobra elimine un atasco mecánico.

## Retroceso, persecución y búsqueda ampliados

Retirada inicial: 100–140 ms, antes 80–100 ms. Recuperación de giro persistente: 40–60 ms, antes 20 ms. La memoria del ataque central aumenta de 60 a 120 ms y la recuperación hacia el último lado de 650 a 1.200 ms. La búsqueda pivota 220 ms y avanza 20 ms, cambiando el barrido cada 1.280 ms; detección frontal cancela búsqueda en el mismo ciclo. Se reinicia el reloj de búsqueda al terminar la recuperación del rival. PWM 255 y prioridad de STOP y piso se conservan.

Una configuración preliminar con retirada 160–220 ms y mayor avance de búsqueda produjo 169/270 caídas y se descartó sin cargar. La seleccionada dio 21/270; todavía requiere comprobar salida del borde y ataque físicos. El usuario aclaró que cuando no ataca está girando o retrocediendo, no detenido: eso es compatible con orientación o escape, pero no prueba qué sensores lo activaron.
