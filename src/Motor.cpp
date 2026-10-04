#include "Motor.h"
#include "Definiciones.h"

namespace {
enum class PatronLed {
    APAGADO,
    AVANCE,
    RETROCESO,
    GIRO_DER,
    GIRO_IZQ
};

void setLedMovimiento(PatronLed patron) {
    unsigned long periodo = 0;
    switch (patron) {
        case PatronLed::APAGADO:
            digitalWrite(LED_BUILTIN, LOW);
            return;
        case PatronLed::AVANCE:
            digitalWrite(LED_BUILTIN, HIGH);
            return;
        case PatronLed::RETROCESO: periodo = 260; break;
        case PatronLed::GIRO_DER:  periodo = 120; break;
        case PatronLed::GIRO_IZQ:  periodo = 50;  break;
    }
    digitalWrite(LED_BUILTIN, ((millis() / periodo) % 2) ? HIGH : LOW);
}
} // namespace

Motor::Motor(int a1, int a2, int pwm, bool invertir, int compensacionPct)
    : pinA1(a1), pinA2(a2), pinPWM(pwm), invertido(invertir), compensacion(compensacionPct) {}

void Motor::iniciar() {
    pinMode(pinA1, OUTPUT);
    pinMode(pinA2, OUTPUT);
    pinMode(pinPWM, OUTPUT);
    detener();
}

int Motor::ajustar(int velocidad) const {
    return constrain((long)velocidad * compensacion / 100, 0, 255);
}

void Motor::avanzar(int velocidad) {
    const uint8_t pin1 = invertido ? HIGH : LOW;
    const uint8_t pin2 = invertido ? LOW : HIGH;
    digitalWrite(pinA1, pin1);
    digitalWrite(pinA2, pin2);
    analogWrite(pinPWM, ajustar(velocidad));
}

void Motor::retroceder(int velocidad) {
    const uint8_t pin1 = invertido ? LOW : HIGH;
    const uint8_t pin2 = invertido ? HIGH : LOW;
    digitalWrite(pinA1, pin1);
    digitalWrite(pinA2, pin2);
    analogWrite(pinPWM, ajustar(velocidad));
}

void Motor::detener() {
#if FRENO_ACTIVO
    digitalWrite(pinA1, HIGH);
    digitalWrite(pinA2, HIGH);
    analogWrite(pinPWM, 255);
#else
    digitalWrite(pinA1, LOW);
    digitalWrite(pinA2, LOW);
    analogWrite(pinPWM, 0);
#endif
}

// Motores
Motores::Motores() :
    motorIzq(MA1A, MA2A, PWMA, INVERTIR_MOTOR_IZQUIERDO, COMPENSACION_MOTOR_IZQ),
    motorDer(MA1B, MA2B, PWMB, INVERTIR_MOTOR_DERECHO, COMPENSACION_MOTOR_DER) {}

void Motores::iniciar() {
    pinMode(LED_BUILTIN, OUTPUT);
    motorIzq.iniciar();
    motorDer.iniciar();
}

void Motores::adelante(int velocidad) {
    motorIzq.avanzar(velocidad);
    motorDer.avanzar(velocidad);
    setLedMovimiento(PatronLed::AVANCE);
}

void Motores::retroceder(int velocidad) {
    motorIzq.retroceder(velocidad);
    motorDer.retroceder(velocidad);
    setLedMovimiento(PatronLed::RETROCESO);
}

void Motores::detener() {
    motorIzq.detener();
    motorDer.detener();
    setLedMovimiento(PatronLed::APAGADO);
}

void Motores::derecha(int velocidad) {
    motorIzq.avanzar(velocidad);
    motorDer.retroceder(velocidad);
    setLedMovimiento(PatronLed::GIRO_DER);
}

void Motores::izquierda(int velocidad) {
    motorIzq.retroceder(velocidad);
    motorDer.avanzar(velocidad);
    setLedMovimiento(PatronLed::GIRO_IZQ);
}

void Motores::curvaDerecha(int velocidad) {
    motorIzq.avanzar(velocidad);
    motorDer.detener();
    setLedMovimiento(PatronLed::GIRO_DER);
}

void Motores::curvaIzquierda(int velocidad) {
    motorIzq.detener();
    motorDer.avanzar(velocidad);
    setLedMovimiento(PatronLed::GIRO_IZQ);
}

// Permite avanzar orientándose hacia un frontal sin girar siempre en el sitio.
void Motores::diferencial(int velocidadIzq, int velocidadDer) {
    if (velocidadIzq == 0) motorIzq.detener();
    else if (velocidadIzq < 0) motorIzq.retroceder(-velocidadIzq);
    else motorIzq.avanzar(velocidadIzq);
    if (velocidadDer == 0) motorDer.detener();
    else if (velocidadDer < 0) motorDer.retroceder(-velocidadDer);
    else motorDer.avanzar(velocidadDer);
    setLedMovimiento(velocidadIzq >= velocidadDer ? PatronLed::GIRO_DER : PatronLed::GIRO_IZQ);
}
