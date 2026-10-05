#ifndef DEFINICIONES_H
#define DEFINICIONES_H

// Pines de sensores: central A3 y derecho A4 verificados por Serial en el robot.
#define S_PISO_IZQ   A0
#define S_PISO_DER   A7
#define S_FRONT_IZQ  A2
#define S_FRONT_CEN  A3
#define S_FRONT_DER  A4
#define S_LAT_IZQ    A1
#define S_LAT_DER    A5

// Ajustar a false si el sensor de enemigo entrega LOW al detectar.
#define ENEMIGO_ACTIVE_HIGH true

// Pines de motores
#define PWMA 5
#define MA1A 7
#define MA2A 6
#define PWMB 10
#define MA1B 8
#define MA2B 9

// Sentido de giro de cada motor
#define INVERTIR_MOTOR_IZQUIERDO false
#define INVERTIR_MOTOR_DERECHO   true
// El robot gira al contrario con la asignación original; conservar avance.
#define INVERTIR_SENTIDO_GIRO true

// Compensación de velocidad por motor (%)
#define COMPENSACION_MOTOR_IZQ 100
#define COMPENSACION_MOTOR_DER 100

// Freno activo al detener
#define FRENO_ACTIVO true

// Control remoto
const int Pin_Control_Remoto         = 4;
const bool REMOTE_ACTIVE_HIGH        = true;
const unsigned long REMOTO_FILTRO_MS = 5;

// Modo calibración: muestra los sensores por Serial sin mover motores
#ifndef REGISTRO_COMBATE
#define REGISTRO_COMBATE 0
#endif

#ifndef MODO_CALIBRACION
#define MODO_CALIBRACION 0
#endif

// Umbral de piso blanco
#define BLANCO 300
// true: blanco entrega ADC bajo; false: blanco entrega ADC alto.
#define PISO_BLANCO_LOW true
#define MARGEN_CERCA_BORDE 35
// Proyecta la tendencia del ADC; solo anticipa dentro de la transición al blanco.
#define PREDICCION_BORDE_MS 15
#define PREDICCION_MUESTREO_MS 2
#define PREDICCION_CAMBIO_MIN_ADC 50
#define PREDICCION_MARGEN_ADC 200
#define PREDICCION_RETIRADA_MIN_MS 40
// Margen respecto al negro aprendido: una lectura más extrema es piso incierto.
#define PISO_NEGRO_TOLERANCIA_ADC 80
// Fuera del dojo medido con ADC bajo; no inferir salida por subidas de negro.
#define PISO_FUERA_ADC_ALTO false

// Velocidades (PWM 0-255)
#define Velocidad_movimiento_seguir 255
#define Velocidad_estandar 255 // Retroceso
#define Velocidad_normal 255
#define Velocidad_maxima 255 // Giros y búsqueda
#define Velocidad_maxima_Ataque 255 // Ataque agresivo a plena potencia
#define Velocidad_borde 255 // Avance inicial hacia el borde

// Parámetros históricos: usados al comparar snapshots del controlador anterior.
// El controlador actual utiliza ESCAPE_* y no introduce pausas.
#define TIEMPO_RETROCESO_MS        60
#define PAUSA_ESCAPE_MS           180
#define PAUSA_RETROCESO_MS        80
#define PAUSA_GIRO_MS             80
#define RETROCESO_MIN_MS          20
#define PISO_LIBRE_MS             80
#define ATAQUE_IMPULSO_MS         90
#define ATAQUE_PAUSA_MS           0
#define TIEMPO_GIRO_BORDE_FRENTE_MS 450
#define TIEMPO_GIRO_BORDE_LADO_MS   450

// Patrones: 0=giro y avance, 1=zigzag, 2=arcos y avance.
#define PATRON_BUSQUEDA 0
#define VELOCIDAD_BUSQUEDA 255
#define BUSQUEDA_FLUIDA true
#define RAMPA_AVANCE_PWM_MS 4
#define MEMORIA_ATAQUE_MS 600

// Ataque continuo sin pausas; los tiempos de impulso solo sirven al comparar
// snapshots anteriores en el simulador.
// Opciones del controlador anterior, conservadas para comparaciones.
// SEGUIMIENTO_PIVOTE=false conserva la alternativa de seguimiento en curva.
// Las lecturas laterales simultáneas pueden pertenecer a objetos distintos.
#define ATAQUE_DOBLE_FRONTAL true
#define DOBLE_FRONTAL_CONFIRMACION_MS 4
#define SEGUIMIENTO_PIVOTE true
#define GIRO_COMPROMISO_MS 90
#define GIRO_MAX_SEGUIMIENTO_MS 150
#define DESATASCO_AVANCE_MS 40
#define VELOCIDAD_DESATASCO 255
#define VELOCIDAD_GIRO_ESCAPE 255
#define VELOCIDAD_ORIENTACION 255
#define FRENO_ORIENTACION_MS 180

// FRENO_LATERAL_MS es histórico; el lateral actual responde sin frenar.
#define FRENO_LATERAL_MS 180
#define GIRO_LATERAL_MAX_MS 220
#define VELOCIDAD_GIRO_LATERAL 255

#define VELOCIDAD_CURVA_INTERIOR 26
#define VELOCIDAD_ATAQUE_CURVA_INTERIOR 30

// Tiempos de búsqueda
#define TIEMPO_BUSQUEDA_GIRO_MS    40
#define TIEMPO_BUSQUEDA_AVANCE_MS  80
#define TIEMPO_REBUSQUEDA_MS       150
// Recuperación dirigida antes de regresar a búsqueda general.
#define SEGUIMIENTO_PERDIDA_MS 1200

// Potencia reducida fuera del ataque; PID corrige mediante avance/pivote.
#define MOTORES_MAXIMO_SIEMPRE false
#define VELOCIDAD_BUSQUEDA_PWM 130
#define VELOCIDAD_SEGUIMIENTO_PWM 255
#define VELOCIDAD_RETROCESO_PWM 160
#define VELOCIDAD_GIRO_PWM 140
#define PID_DIRECCION_KP 200.0f
#define PID_DIRECCION_KI 20.0f
#define PID_DIRECCION_KD 3.0f
#define PID_INTEGRAL_LIMITE 0.8f
#define PID_DERIVADA_TAU_S 0.03f
#define PID_PERIODO_MS 4
#define PID_ZONA_MUERTA 8
#define DIRECCION_PERIODO_MS 12
#define PID_ERROR_CENTRAL_LATERAL 0.20f
#define FILTRO_KALMAN_DIRECCION true
#define KALMAN_DIRECCION_Q 25.0f
#define KALMAN_R_CENTRAL 0.05f
#define KALMAN_R_FRONTAL 0.12f
#define KALMAN_R_LATERAL 0.35f
#define ESCAPE_RETROCESO_MIN_MS 240
#define ESCAPE_RETROCESO_MAX_MS 320
#define ESCAPE_RETIRADA_ATAQUE_MS 120
#define ESCAPE_GIRO_MS 300
#define ESCAPE_GIRO_MIN_MS 0
#define ESCAPE_GIRO_MAX_MS 500
#define ESCAPE_REINTENTO_RETROCESO_MIN_MS 100
#define ESCAPE_REINTENTO_RETROCESO_MAX_MS 150
#define BORDE_REPETIDO_VENTANA_MS 900
#define BORDE_REPETIDO_GIRO_MIN_MS 280
#define BUSQUEDA_CAMBIO_LADO_MS 2100
#define BUSQUEDA_CICLO_MS 350
#define BUSQUEDA_ARCO_MS 300
#define BUSQUEDA_CORRECCION_PWM 510
#define BUSQUEDA_INTERIOR_PWM 60
#define RECUPERACION_LATERAL_GIRO_MS 250

// Round inicial al encender: 1/2 orientan desde el centro; 3 avanza.
// Cada STOP pasa al siguiente round (1->2->3->1); apagar reinicia al inicial.
// 0 desactiva apertura específica y conserva la búsqueda general.
#ifndef ROUND_COMPETENCIA
#define ROUND_COMPETENCIA 1
#endif
#if ROUND_COMPETENCIA < 0 || ROUND_COMPETENCIA > 3
#error ROUND_COMPETENCIA debe estar entre 0 y 3
#endif
#ifndef ROUND_ROTATIVO
#define ROUND_ROTATIVO true
#endif
#define APERTURA_ORIENTACION_MS 900
// Rounds 1/2: los sensores de enemigo no interrumpen el giro inicial en este tiempo.
#define APERTURA_COMPROMISO_MS 700
#define APERTURA_FRENTE_MS 300
#define APERTURA_ORIENTACION_PWM 140
// Round 1 gira más rápido; duración escalada para conservar el ángulo (900*140/200).
#define APERTURA_R1_PWM 200
#define APERTURA_R1_MS 630
// Round 2: gira hacia el lateral que vea al rival (izquierda si ninguno), igual de rápido.
#define APERTURA_R2_PWM 200
#define APERTURA_R2_MS 630
#define APERTURA_FRENTE_PWM 180

#endif // DEFINICIONES_H
