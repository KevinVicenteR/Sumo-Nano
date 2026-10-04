#ifndef DEFINICIONES_H
#define DEFINICIONES_H

// Pines de sensores
#define S_PISO_IZQ   A0
#define S_PISO_DER   A7
#define S_FRONT_IZQ  A2
#define S_FRONT_CEN  A4
#define S_FRONT_DER  A3
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
#define MODO_CALIBRACION 0

// Umbral de piso blanco
#define BLANCO 300
// true: blanco entrega ADC bajo; false: blanco entrega ADC alto.
#define PISO_BLANCO_LOW true
#define MARGEN_CERCA_BORDE 35

// Velocidades (PWM 0-255)
#define Velocidad_movimiento_seguir 255
#define Velocidad_estandar 255 // Retroceso
#define Velocidad_normal 255
#define Velocidad_maxima 255 // Giros y búsqueda
#define Velocidad_maxima_Ataque 255 // Ataque rápido; conservar prioridad del borde
#define Velocidad_borde 255 // Avance inicial hacia el borde

// Tiempos de escape del borde
#define TIEMPO_RETROCESO_MS        240
#define PAUSA_ESCAPE_MS           100
#define PAUSA_RETROCESO_MS        80
#define PAUSA_GIRO_MS             80
#define RETROCESO_MIN_MS          120
#define PISO_LIBRE_MS             20
#define ATAQUE_IMPULSO_MS         90
#define ATAQUE_PAUSA_MS           0
#define TIEMPO_GIRO_BORDE_FRENTE_MS 150
#define TIEMPO_GIRO_BORDE_LADO_MS   110

// Patrones: 0=giro y avance, 1=zigzag, 2=arcos y avance.
#define PATRON_BUSQUEDA 1
#define VELOCIDAD_BUSQUEDA 255

// Ataque continuo sin pausas; los tiempos de impulso solo sirven al comparar
// snapshots anteriores en el simulador.
// Seguimiento en curva: ambas ruedas avanzan; limita giros laterales ambiguos.
// Las lecturas laterales simultáneas pueden pertenecer a objetos distintos.
#define ATAQUE_DOBLE_FRONTAL false
#define GIRO_COMPROMISO_MS 90
#define GIRO_MAX_SEGUIMIENTO_MS 150
#define DESATASCO_AVANCE_MS 40
#define VELOCIDAD_DESATASCO 255
#define VELOCIDAD_GIRO_ESCAPE 255
#define VELOCIDAD_CURVA_INTERIOR 60
#define VELOCIDAD_ATAQUE_CURVA_INTERIOR 140

// Tiempos de búsqueda
#define TIEMPO_BUSQUEDA_GIRO_MS    40
#define TIEMPO_BUSQUEDA_AVANCE_MS  80
#define TIEMPO_REBUSQUEDA_MS       150

#endif // DEFINICIONES_H
