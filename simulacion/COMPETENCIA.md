# Aperturas de competencia integradas en el firmware

`ROUND_COMPETENCIA` selecciona1,2o3 (predeterminado1);0desactiva apertura. No avanza automáticamente de round al recibirSTOP, porqueSTOP también puede abortar/reiniciar una prueba. Seleccionar el round antes de cargar: `pio run -e round1 -t upload`, `round2` o `round3`. `nano` usa round1. No requiere pines ni controles físicos adicionales.

| Round | Apertura sin detección | Fin por tiempo |
|---|---|---|
| 1 | Curva cerrada derecha, exterior140/interior0 | 900ms |
| 2 | Curva cerrada izquierda, exterior140/interior0 | 900ms |
| 3 | Avance rectoPWM180 hacia el rival | 300ms |

Empieza desdeRUN, sin espera5s. Durante curva ninguna rueda recibe orden de retroceso; la interior frena. Cualquier enemigo detectado termina definitivamente la apertura de ese arranque y pasa al seguimiento apropiado. Un frontal alineado ataca255; lateral orienta. Piso y STOP prevalecen; un escape cancela la apertura para que no vuelva a ejecutarse después de salir del borde. Al agotarse tiempo pasa a búsqueda general hacia adelante. Los tiempos limitan maniobra, no miden ángulo ni garantizan180grados reales.

Se ejecutó `python3 simulacion/competencia.py` compilando cada round con su apertura real.360corridas:0caídas, ataque360/360. Medianas de adquisición frontal: round1estático0,560s/errante0,578s; round2estático0,560s/errante0,546s; round3estático0,077s/errante0,051s. El modelo usa distancias supuestas de la imagen y no simula contactos, empujones o rivales autónomos. Son resultados de adquisición, no garantía de victoria física. Comparación previa sin aperturas: aproximadamente1,5s para1/2y1–1,3s para3.

29regresiones aprobadas, incluidas orden inicial de cada round, expiración sin pausa, adquisición frontal que cancela apertura y prioridad piso/STOP. Compilan nano,round1,round2,round3,calibracion,registro. Nano/round1:199bytesRAM,9.122bytesflash. Round1 cargado y verificado por avrdude:9.122bytes en `/dev/cu.usbserial-1130`, tras confirmar el usuario conexión ySTOP. Falta comprobar apertura físicamente.

## Interpretación y mediciones previas

# Posiciones de la competencia proporcionadas por el usuario

Fuente: imagen de tres rounds adjunta en la conversación. Indica comenzar inmediatamente la rutina de ataque al inicio del combate. No se añade espera5s: el firmware reacciona aRUN tras el filtro5ms.

Interpretación de las flechas como frente: primeros dos rounds con robots próximos, espaldas próximas y orientados en sentidos opuestos; tercer round enfrentados desde lados opuestos. La imagen no fija dimensiones ni separación real. No se usa como fuente de voltaje, motores ni tamaño del dojo.

Se añadió `simulacion/competencia.py`, con poses aproximadas y ambos papeles intercambiados. Primeros rounds: centros(-5,5;-5,5)/(5,5;5,5)cm o(-5,5;5,5)/(5,5;-5,5)cm, mirando hacia afuera. Tercero: centros±26cm sobreX, orientados hacia el centro. Dojo modeloØ70cm. CLI nueva del simulador: `--rival-x`, `--rival-y`, `--rival-theta` (metros, grados).

Reproducir: `python3 simulacion/competencia.py`. Son360corridas:3rounds×2papeles×2modos(estático/errante)×30semillas. Resultado:0caídas, ataque360/360. Mediana hasta detección frontal: round1/2~1,50s estático y1,52s errante; round3~1,29s estático y1,00s errante. La rutina de movimiento comienza inmediatamente; esos tiempos incluyen adquisición geométrica del rival, no una pausa programada.

Se comprobó la revisión vigente de retirada240–320ms con cancelación por frontal y empuje600ms. No se alteró de nuevo el firmware ni se cargó otra revisión durante esta comprobación. El modelo no incluye colisiones, empuje ni orientación física de un rival con controlador propio; no prueba victoria ni garantiza cero caídas reales. El rival errante parte de la pose indicada y después sigue el movimiento cinemático del simulador. Los primeros dos layouts son rotaciones equivalentes en el modelo circular.

Prioridad operativa: adquirir frontal al iniciar próximos mirando afuera; atacar al detectar alineación, orientar hacia señales laterales, y conservar protección de piso. En el tercero no se ordena255 a ciegas fuera del alcance de sensores. Para ajustar con precisión se necesitan separación real y confirmar que las flechas representan el frente.
