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
#define FRENO_ACTIVO false

// Control remoto
const int Pin_Control_Remoto         = 4;
const bool REMOTE_ACTIVE_HIGH        = true;
const unsigned long REMOTO_FILTRO_MS = 5;

// Modo calibración: muestra los sensores por Serial sin mover motores
#define MODO_CALIBRACION 0

// Umbral de piso blanco
#define BLANCO 300
#define MARGEN_CERCA_BORDE 35

// Velocidades (PWM 0-255)
#define Velocidad_movimiento_seguir 130
#define Velocidad_estandar 180 // Retroceso
#define Velocidad_normal 130
#define Velocidad_maxima 170 // Giros y búsqueda
#define Velocidad_maxima_Ataque 255 // Ataque frontal
#define Velocidad_borde 100 // Avance inicial hacia el borde

// Tiempos de escape del borde
#define TIEMPO_RETROCESO_MS         150
#define TIEMPO_GIRO_BORDE_FRENTE_MS 220
#define TIEMPO_GIRO_BORDE_LADO_MS   150

// Tiempos de búsqueda
#define TIEMPO_BUSQUEDA_GIRO_MS    200
#define TIEMPO_BUSQUEDA_AVANCE_MS   70
#define TIEMPO_REBUSQUEDA_MS       150

#endif // DEFINICIONES_H
