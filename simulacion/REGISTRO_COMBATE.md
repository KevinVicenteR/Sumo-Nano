# Registro cargado para comprobación física

Se cargó y verificó el entornoregistro (round1predeterminado):421bytesRAM,12.188bytesflash. Captura115200abierta y prueba solicitada al usuario. La guardia exigeSTOPantesdeRUN tras cadareset. Las notas siguientes son historial.

# Registro durante combate

Entorno `registro`: mismo controlador que `nano`, con CSV a115200baudios cada20ms como máximo. Solo envía una fila si cabe completa en el búfer Serial; si no cabe, la omite. Tras cada reset/carga/apertura Serial, exige observar STOP antes de permitir RUN. Motores se habilitan con RUN y se detienen con STOP. No cargado todavía: falta aclarar alimentación de motores y preparar STOP.

Columnas: `ms,pisoI,pisoD,enemigoMask,estado,escape,ordenA,ordenB,RUN,armado`.

Máscara: FI16,FC8,FD4,LI2,LD1. Estados:0STOP,1barrido,2avance de búsqueda,3seguimiento,4ataque,5retroceso,6giro de escape,11lateral. Escape:0libre,1retroceso,2giro. ÓrdenesA/B: signo según configuración lógica de cada canal, amplitud de PWM solicitada tras compensación;0significa detener/frenar. No mide velocidad real ni confirma qué rueda física corresponde a cada canal. Durante STOP las columnas de sensores conservan la última muestra activa; no deben interpretarse como lectura nueva.

Carga: `pio run -e registro -t upload --upload-port /dev/cu.usbserial-1130`. Compilación verificada:416bytesRAM,11.604bytesflash. Para comprobar causas, capturar el instante de retirada sobre negro y comparar piso/máscara/estado/escape/órdenes; una fila tras procesamiento corresponde al estado y órdenes de ese ciclo. Pérdidas de señal de menos de20ms pueden no aparecer; el registro no detecta todos los transitorios ni mide alimentación.

El usuario confirmó batería7,8V al regulador/controlador y Nano soloUSB. Se intentó cargar el registro con interbloqueo, pero el puerto Nano ya no aparece. La revisión continúa sin cargar; la última carga confirmada es el diagnóstico detenido.
