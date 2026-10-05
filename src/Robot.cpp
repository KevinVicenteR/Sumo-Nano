#include <Arduino.h>
#include "Robot.h"
#if REGISTRO_COMBATE
#include <stdio.h>
#endif
#ifdef SIMULACION
extern void registrarEstadoSim(int estado);
#endif

Robot::Robot() : motores(), sensorPisoIzq(S_PISO_IZQ, BLANCO), sensorPisoDer(S_PISO_DER, BLANCO),
    sensorFrontal(S_FRONT_CEN), sensorFrontalIzq(S_FRONT_IZQ), sensorFrontalDer(S_FRONT_DER),
    sensorLateralIzq(S_LAT_IZQ), sensorLateralDer(S_LAT_DER), direccion(),
    roundActual(ROUND_COMPETENCIA), aperturaActiva(false), aperturaDerecha(true), aperturaDecidida(false), inicioApertura(0),
    estadoAnterior(false), remotoEstable(false), remotoCambioDesde(0),
    escape(Escape::LIBRE), inicioEscape(0), libreDesde(0), ultimoEscape(0),
    pisoLibreEstable(false), giroEscapeDerecha(true), giroAlternadoDerecha(true), escapePrevio(false),
    reorientacionObligatoria(false), reintentosEscape(0),
    pisoPrevioIzq(0), pisoPrevioDer(0), negroIzq(0), negroDer(0),
    pisoPrevioValido(false), negroIzqValido(false), negroDerValido(false), ultimaMuestraPiso(0),
    huboContacto(false), busquedaDerecha(true), centralReciente(false), dobleFrontalActivo(false),
    ultimoContacto(0), ultimoCentral(0), inicioBusqueda(0), inicioDobleFrontal(0),
    ultimaMedida(0), ultimoErrorLateral(0) {}

void Robot::setup() {
    const uint8_t sensores[] = {S_PISO_IZQ,S_PISO_DER,S_FRONT_DER,S_FRONT_CEN,S_FRONT_IZQ,S_LAT_IZQ,S_LAT_DER};
    for (uint8_t i = 0; i < sizeof(sensores); ++i) pinMode(sensores[i], INPUT);
    pinMode(Pin_Control_Remoto, INPUT);
    motores.iniciar();
#if MODO_CALIBRACION
    Serial.begin(9600);
#elif REGISTRO_COMBATE
    Serial.begin(115200);
#endif
}

void Robot::loop() {
    procesarLoop();
#if REGISTRO_COMBATE
    registrarCombate();
#endif
}

void Robot::marcarEstado(uint8_t estado) {
#if REGISTRO_COMBATE
    estadoRegistro = estado;
#endif
#ifdef SIMULACION
    registrarEstadoSim(estado);
#endif
    (void)estado;
}

bool Robot::leerRemoto() {
    const bool crudo = digitalRead(Pin_Control_Remoto) == (REMOTE_ACTIVE_HIGH ? HIGH : LOW);
    const unsigned long ahora = millis();
    if (crudo == remotoEstable) remotoCambioDesde = ahora;
    else if (ahora - remotoCambioDesde >= REMOTO_FILTRO_MS) remotoEstable = crudo;
    return remotoEstable;
}

void Robot::reiniciarEstado() {
    direccion.reiniciar();
    escape = Escape::LIBRE;
    escapePrevio = reorientacionObligatoria = false;
    pisoPrevioValido = negroIzqValido = negroDerValido = false;
    huboContacto = centralReciente = pisoLibreEstable = dobleFrontalActivo = false;
    ultimoErrorLateral = 0;
    inicioBusqueda = inicioApertura = millis();
    aperturaActiva = roundActual != 0;
    aperturaDerecha = roundActual == 1;
    aperturaDecidida = roundActual != 2;
}

bool Robot::pisoIncierto(int valor, int negro, bool valido) const {
    return PISO_FUERA_ADC_ALTO && valido && (PISO_BLANCO_LOW ? valor - negro : negro - valor) > PISO_NEGRO_TOLERANCIA_ADC;
}

void Robot::predecirBorde(int izquierda, int derecha, unsigned long ahora, bool &riesgoIzq, bool &riesgoDer) {
    riesgoIzq = riesgoDer = false;
    const unsigned long dt = ahora - ultimaMuestraPiso;
    if (pisoPrevioValido && dt < PREDICCION_MUESTREO_MS) return;
    const int valores[] = {izquierda,derecha};
    const int previos[] = {pisoPrevioIzq,pisoPrevioDer};
    int *negros[] = {&negroIzq,&negroDer};
    bool *validos[] = {&negroIzqValido,&negroDerValido};
    bool *riesgos[] = {&riesgoIzq,&riesgoDer};
    for (uint8_t i = 0; i < 2; ++i) {
        const int distancia = PISO_BLANCO_LOW ? valores[i] - BLANCO : BLANCO - valores[i];
        const int cambio = PISO_BLANCO_LOW ? previos[i] - valores[i] : valores[i] - previos[i];
        if (pisoPrevioValido && dt >= 1 && dt <= 20 && PREDICCION_BORDE_MS > 0) {
            *riesgos[i] = distancia > 0 && distancia <= PREDICCION_MARGEN_ADC && cambio >= PREDICCION_CAMBIO_MIN_ADC &&
                (long)distancia * (long)dt <= (long)cambio * PREDICCION_BORDE_MS;
        }
        if (escape == Escape::LIBRE && distancia > PREDICCION_MARGEN_ADC && !pisoIncierto(valores[i],*negros[i],*validos[i])) {
            *negros[i] = *validos[i] ? ((long)*negros[i] * 7 + valores[i]) / 8 : valores[i];
            *validos[i] = true;
        }
    }
    pisoPrevioIzq = izquierda;
    pisoPrevioDer = derecha;
    ultimaMuestraPiso = ahora;
    pisoPrevioValido = true;
}

void Robot::iniciarEscape(bool izquierda, bool derecha, unsigned long ahora) {
    aperturaActiva = false;
    reorientacionObligatoria = escapePrevio && ahora - ultimoEscape < BORDE_REPETIDO_VENTANA_MS;
    ultimoEscape = inicioEscape = ahora;
    escapePrevio = true;
    escape = Escape::RETROCESO;
    reintentosEscape = 0;
    pisoLibreEstable = false;
    if (izquierda && derecha) {
        giroEscapeDerecha = giroAlternadoDerecha;
        giroAlternadoDerecha = !giroAlternadoDerecha;
    } else giroEscapeDerecha = izquierda;
    centralReciente = dobleFrontalActivo = huboContacto = false;
    ultimoErrorLateral = 0;
    direccion.reiniciar();
}

bool Robot::actualizarEscape(bool peligroIzq, bool peligroDer, bool enemigo, unsigned long ahora) {
    if (escape == Escape::LIBRE) return false;
    const bool peligro = peligroIzq || peligroDer;
    if (peligro) pisoLibreEstable = false;
    else if (!pisoLibreEstable) { pisoLibreEstable = true; libreDesde = ahora; }
    const bool libre = pisoLibreEstable && ahora - libreDesde >= PISO_LIBRE_MS;
    if (enemigo && libre && (escape != Escape::RETROCESO || ahora - inicioEscape >= ESCAPE_RETIRADA_ATAQUE_MS)) {
        escape = Escape::LIBRE;
        pisoPrevioValido = false;
        direccion.reiniciar();
        inicioBusqueda = ahora;
        return false;
    }
    if (escape == Escape::RETROCESO) {
        const unsigned long tiempo = ahora - inicioEscape;
        const unsigned long minimo = reintentosEscape ? ESCAPE_REINTENTO_RETROCESO_MIN_MS : ESCAPE_RETROCESO_MIN_MS;
        const unsigned long maximo = reintentosEscape ? ESCAPE_REINTENTO_RETROCESO_MAX_MS : ESCAPE_RETROCESO_MAX_MS;
        if ((libre && tiempo >= minimo) || tiempo >= maximo) {
            escape = Escape::GIRO;
            inicioEscape = ahora;
        } else {
            retroceder();
            return true;
        }
    }
    const unsigned long tiempo = ahora - inicioEscape;
    const unsigned long minimo = reorientacionObligatoria ? BORDE_REPETIDO_GIRO_MIN_MS : ESCAPE_GIRO_MIN_MS;
    if (libre && tiempo >= minimo && (enemigo || tiempo >= ESCAPE_GIRO_MS)) {
        escape = Escape::LIBRE;
        pisoPrevioValido = false;
        direccion.reiniciar();
        inicioBusqueda = ahora;
        return false;
    }
    if (peligro && tiempo >= ESCAPE_GIRO_MAX_MS) {
        giroEscapeDerecha = peligroIzq != peligroDer ? peligroIzq : !giroEscapeDerecha;
        if (reintentosEscape < 255) ++reintentosEscape;
        escape = Escape::RETROCESO;
        inicioEscape = ahora;
        reorientacionObligatoria = true;
        retroceder();
        return true;
    }
    girar(giroEscapeDerecha);
    marcarEstado(6);
    return true;
}

bool Robot::actualizarApertura(unsigned long ahora) {
    if (!aperturaActiva) return false;
    const unsigned long duracion = roundActual == 3 ? APERTURA_FRENTE_MS :
        roundActual == 1 ? APERTURA_R1_MS : APERTURA_R2_MS;
    if (ahora - inicioApertura >= duracion) {
        aperturaActiva = false;
        inicioBusqueda = ahora;
        return false;
    }
    if (roundActual == 3) {
        motores.adelante(APERTURA_FRENTE_PWM);
        marcarEstado(13);
    } else {
        const int pwm = roundActual == 1 ? APERTURA_R1_PWM : APERTURA_R2_PWM;
        if (aperturaDerecha) motores.diferencial(pwm,0);
        else motores.diferencial(0,pwm);
        marcarEstado(12);
    }
    return true;
}

void Robot::ordenarDireccion(int correccion, unsigned long ahora) {
    correccion = constrain(correccion, -510, 510);
    const unsigned long fase = ahora % DIRECCION_PERIODO_MS;
    const int magnitud = abs(correccion) < PID_ZONA_MUERTA ? 0 : abs(correccion);
    const bool pivote = fase * 510UL < (unsigned long)magnitud * DIRECCION_PERIODO_MS;
    if (!pivote) motores.adelante(VELOCIDAD_SEGUIMIENTO_PWM);
    else if (correccion > 0) motores.derecha(VELOCIDAD_SEGUIMIENTO_PWM);
    else motores.izquierda(VELOCIDAD_SEGUIMIENTO_PWM);
}

void Robot::seguirMedida(float medida, float ruido, unsigned long ahora) {
    ordenarDireccion(direccion.actualizar(medida, ruido, ahora), ahora);
    marcarEstado(3);
}

void Robot::atacar() { direccion.reiniciar(); motores.adelante(255); marcarEstado(4); }
void Robot::retroceder() { motores.retroceder(VELOCIDAD_RETROCESO_PWM); marcarEstado(5); }
void Robot::girar(bool derecha) {
    if (derecha) motores.derecha(VELOCIDAD_GIRO_PWM);
    else motores.izquierda(VELOCIDAD_GIRO_PWM);
}

void Robot::buscar(unsigned long ahora) {
    const unsigned long buscando = ahora - inicioBusqueda;
    const unsigned long fase = buscando % BUSQUEDA_CICLO_MS;
    const bool derecha = busquedaDerecha != ((buscando / BUSQUEDA_CAMBIO_LADO_MS) % 2 != 0);
    if (fase >= BUSQUEDA_ARCO_MS) motores.adelante(VELOCIDAD_BUSQUEDA_PWM);
    else if (derecha) motores.diferencial(VELOCIDAD_BUSQUEDA_PWM,BUSQUEDA_INTERIOR_PWM);
    else motores.diferencial(BUSQUEDA_INTERIOR_PWM,VELOCIDAD_BUSQUEDA_PWM);
    marcarEstado(fase < BUSQUEDA_ARCO_MS ? 1 : 2);
}

#if MODO_CALIBRACION
void Robot::calibrar() {
    motores.detener();
    static unsigned long ultimo = 0;
    if (millis() - ultimo < 100) return;
    ultimo = millis();
    Serial.print(F("Piso I:")); Serial.print(sensorPisoIzq.leerValor());
    Serial.print(F(" D:")); Serial.print(sensorPisoDer.leerValor());
    Serial.print(F(" | Frente I/C/D:")); Serial.print(sensorFrontalIzq.detectar());
    Serial.print(sensorFrontal.detectar()); Serial.print(sensorFrontalDer.detectar());
    Serial.print(F(" | Laterales I/D:")); Serial.print(sensorLateralIzq.detectar()); Serial.print(sensorLateralDer.detectar());
    Serial.print(F(" | Remoto:")); Serial.print(digitalRead(Pin_Control_Remoto));
    Serial.print(F(" | Round:")); Serial.println(roundActual);
}
#endif

#if REGISTRO_COMBATE
void Robot::registrarCombate() {
    const unsigned long ahora = millis();
    if (ahora - ultimoRegistro < 20) return;
    char fila[64];
    const int largo = snprintf(fila,sizeof(fila),"%lu,%d,%d,%u,%u,%u,%d,%d,%u,%u\n",
        ahora,pisoRegistroIzq,pisoRegistroDer,sensoresRegistro,estadoRegistro,
        (unsigned)escape,motores.ordenCanalA(),motores.ordenCanalB(),remotoEstable ? 1 : 0,registroArmado ? 1 : 0);
    if (largo > 0 && largo < (int)sizeof(fila) && Serial.availableForWrite() >= largo) {
        Serial.write((const uint8_t*)fila,largo);
        ultimoRegistro = ahora;
    }
}
#endif

void Robot::procesarLoop() {
#if MODO_CALIBRACION
    calibrar();
    return;
#endif
#if REGISTRO_COMBATE
    if (!registroArmado) {
        if (digitalRead(Pin_Control_Remoto) != (REMOTE_ACTIVE_HIGH ? HIGH : LOW)) registroArmado = true;
        motores.detener();
        marcarEstado(0);
        estadoAnterior = false;
        return;
    }
#endif
    if (!leerRemoto()) {
        motores.detener();
        marcarEstado(0);
        if (estadoAnterior && ROUND_ROTATIVO && roundActual != 0) roundActual = roundActual % 3 + 1;
        estadoAnterior = false;
        return;
    }
    if (!estadoAnterior) { reiniciarEstado(); estadoAnterior = true; }

    const int valorIzq = sensorPisoIzq.leerValor(), valorDer = sensorPisoDer.leerValor();
    const bool blancoIzq = sensorPisoIzq.esBlanco(valorIzq) || pisoIncierto(valorIzq,negroIzq,negroIzqValido);
    const bool blancoDer = sensorPisoDer.esBlanco(valorDer) || pisoIncierto(valorDer,negroDer,negroDerValido);
    const bool central = sensorFrontal.detectar(), frenteIzq = sensorFrontalIzq.detectar(), frenteDer = sensorFrontalDer.detectar();
    const bool lateralIzq = sensorLateralIzq.detectar(), lateralDer = sensorLateralDer.detectar();
#if REGISTRO_COMBATE
    pisoRegistroIzq = valorIzq; pisoRegistroDer = valorDer;
    sensoresRegistro = (frenteIzq ? 16 : 0) | (central ? 8 : 0) | (frenteDer ? 4 : 0) |
        (lateralIzq ? 2 : 0) | (lateralDer ? 1 : 0);
#endif
    const bool frontal = central || frenteIzq || frenteDer;
    const bool enemigo = frontal || lateralIzq || lateralDer;
    const unsigned long ahora = millis();

    bool riesgoIzq, riesgoDer;
    predecirBorde(valorIzq,valorDer,ahora,riesgoIzq,riesgoDer);
    if (escape == Escape::LIBRE && (blancoIzq || blancoDer || riesgoIzq || riesgoDer))
        iniciarEscape(blancoIzq || riesgoIzq,blancoDer || riesgoDer,ahora);
    if (actualizarEscape(blancoIzq,blancoDer,frontal,ahora)) return;

    if (aperturaActiva && !aperturaDecidida && lateralIzq != lateralDer) {
        aperturaDerecha = lateralDer;
        aperturaDecidida = true;
    }
    if (aperturaActiva && roundActual != 3 && ahora - inicioApertura < APERTURA_COMPROMISO_MS &&
        actualizarApertura(ahora)) return;

    if (enemigo) {
        aperturaActiva = false;
        huboContacto = true;
        ultimoContacto = ahora;
        inicioBusqueda = ahora + SEGUIMIENTO_PERDIDA_MS;
        if (central) {
            centralReciente = true;
            ultimoCentral = ahora;
            if (!frenteIzq && !frenteDer && fabsf(ultimoErrorLateral) > 1) ultimoErrorLateral = 0;
        }
        if (frenteDer != frenteIzq) ultimoErrorLateral = frenteDer ? 0.8f : -0.8f;
        else if (!frontal && lateralDer != lateralIzq) ultimoErrorLateral = lateralDer ? 2.0f : -2.0f;
        if (ultimoErrorLateral != 0) busquedaDerecha = ultimoErrorLateral > 0;
    }

    if (!(frenteIzq && frenteDer)) dobleFrontalActivo = false;
    else if (!dobleFrontalActivo) { dobleFrontalActivo = true; inicioDobleFrontal = ahora; }
    const bool frenteConfirmado = central || (ATAQUE_DOBLE_FRONTAL && dobleFrontalActivo &&
        ahora - inicioDobleFrontal >= DOBLE_FRONTAL_CONFIRMACION_MS);
    const bool memoriaRecta = centralReciente && ahora - ultimoCentral < MEMORIA_ATAQUE_MS && !frenteIzq && !frenteDer;

    if (central && frenteIzq && frenteDer) {
        ultimoErrorLateral = ultimaMedida = 0;
        atacar();
        return;
    }
    if (frenteConfirmado || memoriaRecta) {
        if (frenteConfirmado) { centralReciente = true; ultimoCentral = ahora; }
        if (central && frenteDer != frenteIzq) {
            if (fabsf(ultimaMedida) > PID_ERROR_CENTRAL_LATERAL) direccion.reiniciar();
            ultimaMedida = frenteDer ? PID_ERROR_CENTRAL_LATERAL : -PID_ERROR_CENTRAL_LATERAL;
            seguirMedida(ultimaMedida,KALMAN_R_CENTRAL,ahora);
        } else {
            ultimaMedida = 0;
            atacar();
        }
        return;
    }
    if (frenteIzq || frenteDer) {
        ultimaMedida = frenteDer == frenteIzq ? 0 : frenteDer ? 0.8f : -0.8f;
        seguirMedida(ultimaMedida,KALMAN_R_FRONTAL,ahora);
        return;
    }
    if (lateralIzq || lateralDer) {
        const bool derecha = lateralIzq == lateralDer ? busquedaDerecha : lateralDer;
        ultimaMedida = derecha ? 2.0f : -2.0f;
        girar(derecha);
        marcarEstado(11);
        return;
    }
    if (huboContacto && ahora - ultimoContacto < SEGUIMIENTO_PERDIDA_MS) {
        if (fabsf(ultimoErrorLateral) > 1 && ahora - ultimoContacto < RECUPERACION_LATERAL_GIRO_MS) {
            girar(ultimoErrorLateral > 0);
            marcarEstado(11);
        } else {
            const float medida = ultimoErrorLateral != 0 ? constrain(ultimoErrorLateral,-0.8f,0.8f) : (busquedaDerecha ? 0.8f : -0.8f);
            seguirMedida(medida,KALMAN_R_FRONTAL,ahora);
        }
        return;
    }
    if (actualizarApertura(ahora)) return;
    buscar(ahora);
}
