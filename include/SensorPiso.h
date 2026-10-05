#ifndef SENSORPISO_H
#define SENSORPISO_H

#include <Arduino.h>
#include "Definiciones.h"

class SensorPiso {
    int pin;
    int umbral;
public:
    SensorPiso(int pin, int umbral);
    int leerValor() const;
    bool esBlanco(int valor) const;
};

#endif
