#ifndef SENSORENEMIGO_H
#define SENSORENEMIGO_H

#include <Arduino.h>
#include "Definiciones.h"

class SensorEnemigo {
    int pin;
public:
    explicit SensorEnemigo(int pin);
    bool detectar() const;
};

#endif
