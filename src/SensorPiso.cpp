#include "SensorPiso.h"
#include "Definiciones.h"

SensorPiso::SensorPiso(int pin, int umbral) : pin(pin), umbral(umbral) {}

int SensorPiso::leerValor() {
    return analogRead(pin);
}

bool SensorPiso::esBlanco(int valor) const {
    return PISO_BLANCO_LOW ? valor <= umbral : valor >= umbral;
}

bool SensorPiso::detectar() {
    return esBlanco(leerValor());
}
