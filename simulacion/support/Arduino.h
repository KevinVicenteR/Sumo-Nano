#ifndef ARDUINO_H
#define ARDUINO_H

// Arduino simulado: las funciones las implementa simulacion/sim.cpp

#include <stdint.h>
#include <stdlib.h>

#define HIGH 0x1
#define LOW 0x0
#define INPUT 0x0
#define OUTPUT 0x1
#define INPUT_PULLUP 0x2

// Numeración de pines analógicos del Leonardo (ATmega32u4)
#define LED_BUILTIN 13
#define A7 21
#define A0 14
#define A1 15
#define A2 16
#define A3 17
#define A4 18
#define A5 19

#define constrain(x, lo, hi) ((x) < (lo) ? (lo) : ((x) > (hi) ? (hi) : (x)))
#define F(x) (x)

#ifdef __cplusplus
extern "C" {
#endif

void delay(unsigned long ms);
unsigned long millis(void);
unsigned long micros(void);
int analogRead(uint8_t pin);
int digitalRead(uint8_t pin);
void digitalWrite(uint8_t pin, uint8_t value);
void analogWrite(uint8_t pin, int value);
void pinMode(uint8_t pin, uint8_t mode);

#ifdef __cplusplus
}
#endif

// Serial solo se usa en MODO_DIAGNOSTICO; se deja vacío
struct SerialSim {
    void begin(unsigned long) {}
    template <typename T> void print(T) {}
    template <typename T> void println(T) {}
    void println() {}
};
extern SerialSim Serial;

#endif
