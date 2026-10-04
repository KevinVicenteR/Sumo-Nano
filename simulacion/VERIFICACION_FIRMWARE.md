# Comparación de firmware y prueba física

Con STOP confirmado por el usuario, se leyó la flashATmega328P por avrdude sin escritura (`-n -U flash:r:...:r`). Se compararon las direcciones de los9.122bytes de `.pio/build/round1/firmware.hex` con la flash leída:0diferencias. SHA256de ambos segmentos: `1e9fa1be3107350820c9a7d4049de441b3f5e4db1372dea40dee75d5d184a1bc`. Esto confirma que antes de instrumentarlo el Nano tenía el artefacto round1 cargado por el agente.

Las pruebas de control general compilan `ROUND_COMPETENCIA=0`; un caso separado prueba aperturas1/2/3, expiración y cancelación por sensores/STOP. Los lotes de competencia sí compilan cada round correspondiente. El simulador usaADCnegro900/blanco100, mientras las mediciones reales varían por sensor; su rival no colisiona ni empuja, y no reproduce inclinación ni ruido eléctrico durante motores. Los resultados0caídas y adquisición no garantizan comportamiento físico.

Se cargó y verificó `registro`:12.188bytesflash,421bytesRAM, round1por defecto. Conserva algoritmo y parámetros de round1; añade CSV115200y guardia STOPantesdeRUN tras reset. Registra señales y órdenes solicitadas a canales, no velocidad real. Captura en `/tmp/sumo-combate-real.csv`; se solicitó reproducir abandono de empuje sobre negro cerca del centro, rival enfrente, STARTy luegoSTOP. Pendiente de recibir prueba y analizar captura.

La primera ventana física150s terminó sinSTART: 7425muestras, todas estado0/STOPy órdenesA/B0. No se comprobó ataque en movimiento. Se requiere nueva ventana coordinada antesdeSTART. El registro permanece cargado.
