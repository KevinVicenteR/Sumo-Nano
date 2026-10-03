#ifndef SENSORPISO_H
#define SENSORPISO_H

#include <Arduino.h>
#include "ISensor.h"
#include "Definiciones.h"

class SensorPiso : public ISensor {
    int pin;
    int umbral;
public:
    SensorPiso(int pin, int umbral);
    int leerValor();
    bool esBlanco(int valor) const;
    bool detectar() override;
};

#endif // SENSORPISO_H
