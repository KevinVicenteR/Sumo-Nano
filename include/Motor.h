#ifndef MOTOR_H
#define MOTOR_H

#include <Arduino.h>
#include "Definiciones.h"

class Motor {
    int pinA1, pinA2, pinPWM;
    bool invertido;
    int compensacion;
    int ajustar(int velocidad) const;
#if REGISTRO_COMBATE
    int orden = 0;
#endif
public:
    Motor(int a1, int a2, int pwm, bool invertir = false, int compensacionPct = 100);
    void iniciar();
    void avanzar(int velocidad);
    void retroceder(int velocidad);
    void detener();
#if REGISTRO_COMBATE
    int leerOrden() const { return orden; }
#endif
};

class Motores {
    Motor motorIzq, motorDer;
public:
    Motores();
    void iniciar();
    void adelante(int velocidad);
    void diferencial(int velocidadIzq, int velocidadDer);
    void retroceder(int velocidad);
    void detener();
    void derecha(int velocidad);
    void izquierda(int velocidad);
#if REGISTRO_COMBATE
    int ordenCanalA() const { return motorIzq.leerOrden(); }
    int ordenCanalB() const { return motorDer.leerOrden(); }
#endif
};

#endif
