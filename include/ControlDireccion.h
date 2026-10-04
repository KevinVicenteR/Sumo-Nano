#ifndef CONTROL_DIRECCION_H
#define CONTROL_DIRECCION_H
#include <Arduino.h>
#include <math.h>
#include "Definiciones.h"

// Estado angular aproximado, estimado exclusivamente con sensores de enemigo.
class ControlDireccion {
    float estimacion, covarianza, integral, derivada;
    unsigned long ultimaActualizacion;
    bool iniciado;
    int salida;
public:
    ControlDireccion() { reiniciar(); }
    void reiniciar() {
        estimacion = integral = derivada = 0;
        covarianza = 1;
        ultimaActualizacion = 0;
        iniciado = false;
        salida = 0;
    }
    int actualizar(float medida, float ruido, unsigned long ahora) {
        if (!iniciado) {
            estimacion = medida;
            covarianza = ruido;
            ultimaActualizacion = ahora;
            iniciado = true;
            salida = (int)constrain(PID_DIRECCION_KP * medida, -510.0f, 510.0f);
            return salida;
        }
        const unsigned long transcurrido = ahora - ultimaActualizacion;
        if (transcurrido < PID_PERIODO_MS) return salida;
        const float dt = constrain(transcurrido * 0.001f, 0.001f, 0.05f);
        ultimaActualizacion = ahora;
        const float previa = estimacion;
#if FILTRO_KALMAN_DIRECCION
        covarianza += KALMAN_DIRECCION_Q * dt;
        const float ganancia = covarianza / (covarianza + ruido);
        estimacion += ganancia * (medida - estimacion);
        covarianza *= 1.0f - ganancia;
#else
        estimacion = medida;
#endif
        derivada += dt / (PID_DERIVADA_TAU_S + dt) * ((estimacion - previa) / dt - derivada);
        const float candidata = constrain(integral + estimacion * dt, -PID_INTEGRAL_LIMITE, PID_INTEGRAL_LIMITE);
        const float provisional = PID_DIRECCION_KP * estimacion + PID_DIRECCION_KI * candidata + PID_DIRECCION_KD * derivada;
        // Anti-windup: aceptar integración solo sin saturación o al salir de ella.
        if (fabsf(provisional) < 510 || provisional * estimacion < 0) integral = candidata;
        const float control = PID_DIRECCION_KP * estimacion + PID_DIRECCION_KI * integral + PID_DIRECCION_KD * derivada;
        salida = (int)constrain(control, -510.0f, 510.0f);
        return salida;
    }
};
#endif
