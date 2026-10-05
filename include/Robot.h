#ifndef ROBOT_H
#define ROBOT_H
#include <Arduino.h>
#include "Definiciones.h"
#include "Motor.h"
#include "SensorPiso.h"
#include "SensorEnemigo.h"
#include "ControlDireccion.h"

class Robot {
    enum class Escape : uint8_t { LIBRE, RETROCESO, GIRO };

    Motores motores;
    SensorPiso sensorPisoIzq, sensorPisoDer;
    SensorEnemigo sensorFrontal, sensorFrontalIzq, sensorFrontalDer, sensorLateralIzq, sensorLateralDer;
    ControlDireccion direccion;

    uint8_t roundActual;
    bool aperturaActiva, aperturaDerecha, aperturaDecidida;
    unsigned long inicioApertura;

    bool estadoAnterior, remotoEstable;
    unsigned long remotoCambioDesde;

    Escape escape;
    unsigned long inicioEscape, libreDesde, ultimoEscape;
    bool pisoLibreEstable, giroEscapeDerecha, giroAlternadoDerecha, escapePrevio, reorientacionObligatoria;
    uint8_t reintentosEscape;

    int pisoPrevioIzq, pisoPrevioDer, negroIzq, negroDer;
    bool pisoPrevioValido, negroIzqValido, negroDerValido;
    unsigned long ultimaMuestraPiso;

    bool huboContacto, busquedaDerecha, centralReciente, dobleFrontalActivo;
    unsigned long ultimoContacto, ultimoCentral, inicioBusqueda, inicioDobleFrontal;
    float ultimaMedida, ultimoErrorLateral;

#if REGISTRO_COMBATE
    bool registroArmado = false;
    unsigned long ultimoRegistro = 0;
    int pisoRegistroIzq = 0, pisoRegistroDer = 0;
    uint8_t sensoresRegistro = 0, estadoRegistro = 0;
    void registrarCombate();
#endif
#if MODO_CALIBRACION
    void calibrar();
#endif

    void marcarEstado(uint8_t estado);
    bool leerRemoto();
    void reiniciarEstado();
    bool pisoIncierto(int valor, int negro, bool valido) const;
    void predecirBorde(int izquierda, int derecha, unsigned long ahora, bool &riesgoIzq, bool &riesgoDer);
    void iniciarEscape(bool izquierda, bool derecha, unsigned long ahora);
    bool actualizarEscape(bool peligroIzq, bool peligroDer, bool enemigo, unsigned long ahora);
    bool actualizarApertura(unsigned long ahora);
    void ordenarDireccion(int correccion, unsigned long ahora);
    void seguirMedida(float medida, float ruido, unsigned long ahora);
    void atacar();
    void retroceder();
    void girar(bool derecha);
    void buscar(unsigned long ahora);
    void procesarLoop();

public:
    Robot();
    void setup();
    void loop();
};
#endif
