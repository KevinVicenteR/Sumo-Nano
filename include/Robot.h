#ifndef ROBOT_H
#define ROBOT_H

#include <Arduino.h>
#include "Definiciones.h"
#include "Motor.h"
#include "SensorPiso.h"
#include "SensorEnemigo.h"

class Robot {
    Motores motores;
    SensorPiso sensorPisoIzq, sensorPisoDer;
    SensorEnemigo sensorFrontal, sensorFrontalIzq, sensorFrontalDer, sensorLateralIzq, sensorLateralDer;

    // Estado del combate
    bool bordeDetectado;
    bool estadoAnterior;
    bool busquedaDerecha;
    uint8_t faseBusqueda;
    unsigned long inicioFase;
    bool huboContacto;
    unsigned long ultimoContacto;

    // Filtro del control remoto
    bool remotoEstable;
    unsigned long remotoCambioDesde;

    bool leerRemoto();
    bool leerPiso(bool &pisoIzq, bool &pisoDer);
    void reiniciarEstado();
    bool retrocesoSeguro(unsigned long duracionMs);
    bool giroEscape(bool haciaDerecha, unsigned long duracionMs);
    void girarHacia(bool haciaDerecha);
#if MODO_CALIBRACION
    void calibrar();
#endif
public:
    Robot();
    void setup();
    void detenerse();
    void ataqueEnemigo();
    void moverAdelante();
    void retroceder();
    void moverDerecha();
    void moverIzquierda();
    void sensoresPiso(bool pisoIzq, bool pisoDer);
    void sensoresFrontales(bool derecho, bool izquierdo);
    void sensoresLaterales(bool sensorIzquierdo, bool sensorDerecho);
    void loop();
};

#endif // ROBOT_H
