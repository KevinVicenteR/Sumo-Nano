#include "SensorEnemigo.h"
#include "Definiciones.h"

SensorEnemigo::SensorEnemigo(int pin) : pin(pin) {}

bool SensorEnemigo::detectar() {
    return digitalRead(pin) == (ENEMIGO_ACTIVE_HIGH ? HIGH : LOW);
}
