#include "SensorEnemigo.h"

SensorEnemigo::SensorEnemigo(int pin) : pin(pin) {}

bool SensorEnemigo::detectar() const {
    return digitalRead(pin) == (ENEMIGO_ACTIVE_HIGH ? HIGH : LOW);
}
