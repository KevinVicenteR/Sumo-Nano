# Lecturas reales del Nano · 4 de octubre de 2026

Puerto `/dev/cu.usbserial-1130`, adaptador CH340 (VID 1A86, PID 7523), 9600 baudios. Se cargó y verificó el firmware del entorno `calibracion`, con motores detenidos. Se comenzó con diagnóstico detenido y al finalizar, con autorización explícita del usuario, se cargó el entorno `nano` de combate.

| Posición confirmada por el usuario | Piso izquierdo | Piso derecho | RAW enemigo FI/FC/FD/LI/LD |
|---|---:|---:|---|
| Fuera del dojo | 43–49 | 44–51 | 10111 |
| Negro, sin rival | 797–812 | 859–874 | 00000 en 49/50 muestras; 00100 en 1/50 |
| Negro, rival frente al central | Aproximadamente 795–799 | Aproximadamente 858–860 | 00100 en 64/64 muestras |

El negro está por encima del umbral 300. No se modificaron umbral ni polaridades por estas lecturas; falta medir la franja blanca. Una señal 1 fuera del dojo puede corresponder a objetos del entorno, así que no sirve como referencia de ausencia de enemigo.

Para cargar diagnóstico: `pio run -e calibracion -t upload --upload-port /dev/cu.usbserial-1130`. Para volver a combate después de medir: `pio run -e nano -t upload --upload-port /dev/cu.usbserial-1130`.

Con el rival ubicado frente al centro, se activa la entrada FD (A3), no FC (A4). Al mover el rival al frontal derecho, se activó FC (A4) en 54/54 muestras. Se confirmó el intercambio y se corrigió el mapa: central A3, derecho A4. Se conserva ENEMIGO_ACTIVE_HIGH=true.

## Verificación tras corregir los pines

Se volvió a cargar y verificar el diagnóstico con `S_FRONT_CEN=A3` y `S_FRONT_DER=A4`. Con el rival centrado se recibió `01000` en 54/54 muestras: FC=1 y FD=0. Antes de corregirlo, la misma colocación producía `00100` en 64/64 muestras. Con el rival frente al derecho, el mapa anterior producía `01000` en 54/54 muestras, confirmando el intercambio.

Las 15 regresiones y la compilación de combate pasan con el mapa corregido (189 bytes RAM, 8.116 bytes flash). Aún no se ha observado empuje físico ni se ha medido la franja blanca. El usuario autorizó salir del diagnóstico: se cargaron 8.116 bytes del entorno `nano` y avrdude verificó correctamente toda la flash. El dispositivo quedó con firmware de combate, no con diagnóstico.

## Corrección de seguimiento cargada

Tras reportar el usuario que gira al lado contrario, se invirtió únicamente la dirección de giro (`INVERTIR_SENTIDO_GIRO=true`), conservando las órdenes de avance y retroceso. La dirección física del avance no se confirmó de nuevo. El seguimiento conserva el último lado durante 650 ms y elimina el avance forzado durante detección lateral persistente. Pasan 20 pruebas; compilación: 193 bytes RAM, 8.342 bytes flash. Se cargó por `/dev/cu.usbserial-1130` y avrdude verificó los 8.342 bytes. Falta confirmar el seguimiento con movimiento real del rival.

## Nueva evasión preparada

Nueva revisión: giro persistente acotado a 350 ms y retirada de recuperación de 20 ms, con selección de orientación según sensores de piso. Ataque explícito al detectar los tres frontales. Pasan 22 pruebas y compila con 194 bytes RAM y 8.482 bytes flash. La primera carga falló porque el puerto no existía. Tras reconectar el usuario el Nano, se cargaron y verificaron los 8.482 bytes por `/dev/cu.usbserial-1130`. Simulación: 36/270 caídas frente a 34/270 antes; no demuestra menor riesgo de caída.

## Retroceso, persecución y búsqueda · revisión preparada

Retirada 100–140 ms y recuperaciones 40–60 ms; seguimiento perdido 1.200 ms; memoria central 120 ms. Búsqueda: pivote 220 ms, avance 20 ms y barrido alternante cada 1.280 ms. Compilación: 194 bytes RAM, 8.528 bytes flash; 23 pruebas aprobadas y 21/270 caídas (antes 36/270). La carga falló porque `/dev/cu.usbserial-1130` no está presente; esta revisión no se ha cargado.

## Video 15.08.49 · observación sin telemetría

Video de 23,365 s. Los fotogramas muestran maniobras repetidas próximas al borde aproximadamente entre 3 y 12 s. Se coloca un rival alrededor de 13 s; hay varias orientaciones antes del acercamiento y contacto cerca de 22 s. No puede asignarse ese retraso a un sensor o estado concreto sin lecturas sincronizadas. La revisión de retroceso/persecución/búsqueda no fue cargada por este agente; queda pendiente confirmar si el usuario la cargó por su cuenta. Al revisar el video no aparece ninguna placa USB. No se modificó nuevamente el controlador basándose solo en estas imágenes.

## Carga confirmada de retroceso/persecución/búsqueda

El usuario reconectó el Nano tras revisar el video 15.08.49. Se detectó CH340 en `/dev/cu.usbserial-1130`; avrdude confirmó ATmega328P y escribió y verificó los 8.528 bytes del entorno `nano`. El robot quedó con la revisión de retroceso 100–140 ms, recuperación 40–60 ms, persecución 1.200 ms y búsqueda alternante. Falta verificar físicamente el comportamiento y las señales durante las maniobras; el firmware de combate no emite diagnóstico serial.

## Diagnóstico posterior al video 15.20.54

Tras reconectar el usuario el Nano, se cargó y verificó el entorno `calibracion`: 4.122 bytes flash, motores detenidos. La placa queda temporalmente en diagnóstico. Lectura inicial de 50 muestras: piso izquierdo 811–816, derecho 867–870; RAW FI/FC/FD/LI/LD=00000 en 50/50. La posición de esta primera lectura no se confirmó por el usuario. Se solicitó colocar sobre negro y rival en contacto frente a la pala para investigar el retroceso observado; esa lectura está pendiente. Una lectura detenida no descarta interferencia con motores ni falsos cambios por inclinación.

### Negro con rival pegado frente a la pala

Colocación confirmada por el usuario. Se tomaron 60 muestras en aproximadamente 6 s: piso izquierdo 777–782, derecho 851–856; RAW `01000` en 60/60 (central detecta, restantes no). En reposo el piso no cruza el umbral 300 y el central no pierde al rival. Esto no reproduce la retirada observada en movimiento ni descarta variaciones por vibración, inclinación o interferencia. Se solicitó medir ambos sensores sobre blanco; el robot continúa con diagnóstico y motores detenidos.

### Primera lectura con colocación sobre blanco

El usuario indicó que estaba sobre blanco. En 60 muestras: izquierdo 801–806, derecho 52–57; enemigos RAW00000 en 60/60. El derecho responde al blanco por debajo del umbral300; el izquierdo conserva niveles de negro. No se confirma blanco bajo ambos sensores por separado: se solicitó centrar específicamente el izquierdo en la franja para distinguir colocación de fallo de sensor/cableado. No se modificó el umbral ni se volvió a combate; motores detenidos.

### Blanco confirmado tras centrar el sensor izquierdo

El usuario confirmó el izquierdo centrado sobre blanco. En 50 muestras, izquierdo39–47 y derecho45–52. Ambos responden al blanco por debajo del umbral300; frente al negro medido777–782/851–856 existe separación amplia. La lectura anterior no demuestra fallo del izquierdo; al recolocarlo sí responde. No se cambió umbral ni polaridad. El retroceso en contacto aún no se reproduce en reposo; falta telemetría durante movimiento. Continúa diagnóstico con motores detenidos.

### Lectura tras encender con alimentación externa

El usuario indicó que lo encendió, sin confirmar aún voltaje ni conexión de batería. El puerto CH340 `/dev/cu.usbserial-1130` sigue presente. Primera captura: 0 líneas válidas durante 8 s después de reiniciar por apertura serial. Segunda captura sin filtrar: 0 bytes en 6 s. No existen muestras para evaluar sensores en esta condición. No se accionaron motores ni se reflasheó. Se solicitó volver a USB solo e identificar alimentación. La ausencia de datos no prueba una avería ni una causa eléctrica concreta.

### Aclaración USB y recuperación de Serial

El usuario aclaró que solo usa USB; no estaba confirmada alimentación externa en la captura anterior. Se repitió captura8s:0bytes. Se restauró `calibracion` y avrdude verificó4.122bytes. Luego se recibieron4.648bytes y56muestras en7s: pisoI776–780,D857–860. RAW:00010=14,00011=3,11011=1,10000=1,11010=2,11000=2,11001=1,00000=29,10010=2,00001=1. La colocación del rival/manos no se confirmó, por lo que los cambios no demuestran ruido ni fallo de sensores. Se solicitó repetir sobre negro con entorno despejado. Continúa diagnóstico detenido. La recuperación tras recarga no identifica la causa previa del silencio.

### Negro con entorno despejado confirmado

80muestras durante8s: pisoI786–790,D840–844; RAW00000 en80/80. Ningún sensor de enemigo activo. No se reprodujeron las señales variables observadas en la captura anterior; no existe evidencia de falsas detecciones en esta condición estática. Se solicitó comprobar frontal izquierdo con rival a10cm (mirando desde atrás). El robot permanece en diagnóstico, motores detenidos; falta diagnóstico en movimiento y mapa izquierdo/laterales.

### Primer intento de aislar frontal izquierdo

Usuario confirmó rival frente al izquierdo.60muestras: pisoI767–770,D843–848; RAW01000 en60/60: activa centralA3 y no izquierdoA2. Es discrepancia entre colocación y entrada esperada; puede ser solapamiento de campos, ubicación física o mapa de pines. No se intercambiaron pines. Se solicitó desplazar rival más hacia izquierda para excluir central y aislar sensor.

### Frontal izquierdo aislado confirmado

Tras desplazar el rival para aislar izquierdo,60muestras: pisoI767–770,D845–848; RAW10000 en60/60. Frontal izquierdoA2 responde correctamente. La primera colocación activaba central; no requiere cambio de mapa. Se solicitó comprobar lateral derecho aislado; continúa diagnóstico detenido.

### Primer intento de lateral derecho

Usuario confirmó rival en posición lateral derecha.60muestras: pisoI766–770,D844–848; RAW00100 en60/60 (frontal derechoA4, lateral derechoA5 inactivo). No confirma inversión de pines: se solicitó aislar lateral fuera del campo frontal, hacia el costado y detrás de pala. No se modificó firmware. Continúa diagnóstico con motores detenidos.

### Lateral derecho aislado confirmado

Tras mover rival fuera del campo frontal,60muestras: pisoI774–778,D859–862; RAW00001 en60/60. Lateral derechoA5 correcto y frontales inactivos. No requiere cambio de pin. Se solicitó comprobar lateral izquierdo aislado; sigue diagnóstico detenido.

### Lateral izquierdo y mapa completo

Usuario confirmó rival aislado frente al lateral izquierdo.60muestras: pisoI777–780,D856–860; RAW00010 en60/60. Lateral izquierdoA1 correcto. Las pruebas aisladas confirman el mapa vigente FI=A2,FC=A3,FD=A4,LI=A1,LD=A5, con detección activaHIGH. Piso blanco responde en ambos canales y negro despejado no genera enemigo en80/80muestras. No hay evidencia de inversión actual de pines ni ruido en reposo despejado. No se han verificado las señales durante movimiento ni sentido físico de motores con órdenes registradas. Continúa `calibracion`, motores detenidos; no se cargó combate al cerrar esta comprobación.

## Round1 cargado y verificado

El usuario aclaró que el robot avanza después deSTART, no antes. Tras indicar conexión ySTOP, se detectó CH340; se cargó entorno `round1` y avrdude confirmóATmega328P y verificó9.122bytes. Quedó firmware de combate con apertura round1, no calibración. Falta comprobar en físico que sin detección inicia curva derecha y que frontal cancela apertura para atacar.
