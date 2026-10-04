// Simulador de combate en dohyo circular.
//
// Compila el firmware real (main.cpp y todo src/) contra un Arduino simulado:
// los pines de motores se traducen a velocidades de rueda y los pines de
// sensores se calculan a partir de la geometría del dohyo y del enemigo.
//
// Cada corrida se ejecuta en un proceso hijo (fork) para que el estado global
// del firmware (objetos en main.cpp) arranque limpio, igual que tras un reset.
//
// Salida: una línea CSV por corrida (ver imprimirCabecera()).

#include <Arduino.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <sys/wait.h>
#include <unistd.h>
#include "Definiciones.h"

void setup();
void loop();

SerialSim Serial;

namespace {

constexpr double PI = 3.14159265358979323846;

struct Config {
    // Dohyo
    double radio = 0.35;          // m (70 cm de diámetro, borde incluido)
    double borde = 0.01;          // m de línea blanca
    // Robot
    double largo = 0.10;          // m
    double ancho = 0.10;          // m
    double trocha = 0.085;        // m entre ruedas
    double sensorPisoX = 0.045;   // m hacia adelante desde el eje de ruedas
    double sensorPisoY = 0.040;   // m a cada lado
    double vmax = 0.8;            // m/s con PWM 255
    double tau = 0.05;            // s, constante de tiempo del motor
    double mu = 0.9;              // adherencia rueda-piso (limita aceleración)
    // Modelo de motor DC (se activa con --rpm; si no, se usa vmax/tau)
    double rpm = 0;               // rpm en vacío del motorreductor
    double diametro = 0.03;       // m, diámetro de rueda
    double masa = 0.3;            // kg
    double parBloqueo = 0.6;      // kg·cm por motor con el rotor bloqueado
    double bateria = 1.0;         // tensión de batería / tensión nominal del motor
    double friccionCaja = 0.15;   // fricción de la reductora (fracción de la fuerza de bloqueo)
    double rodadura = 0.03;       // coeficiente de resistencia a la rodadura
    double friccionGiro = 0.5;    // roce lateral al girar en el sitio (ruedas, pala)
    double brazoGiro = 0.012;     // m, brazo efectivo de ese roce
    // Sensores de piso (lecturas ADC) y su mancha de lectura
    double adcNegro = 900;
    double adcBlanco = 100;
    double adcFuera = 1000;       // fuera del dohyo, sin superficie debajo
    double manchaSensor = 0.003;  // m de radio del área que ve el sensor de piso
    // Objetos fuera del dohyo que ven los sensores de enemigo (0 = ninguno)
    double radioPared = 0;        // m desde el centro
    // Posición inicial: radio máximo del centro del robot; el cuerpo entero queda dentro del dohyo
    double radioInicio = 0.35;
    std::string inicio = "todo"; // todo, borde, centro, fijo
    double inicioX = 0, inicioY = 0, inicioTh = 0;
    std::string pruebaSensores = "normal"; // alternante y laterales: estrés sintético
    std::string pruebaPiso = "normal";
    double rangoEnemigo = 0.40;   // m, alcance de los sensores de enemigo
    // Enemigo
    bool rivalFijo = false;
    double rivalX = 0, rivalY = 0, rivalTheta = 0;
    double radioEnemigo = 0.05;   // m
    double velEnemigo = 0.25;     // m/s en modo errante
    // Simulación
    // Configuración física independiente del firmware: giro contrario reportado.
    bool canalesIntercambiados = true;
    bool invertirCanalA = false, invertirCanalB = true;
    double pasoTray = 0.01;       // s entre muestras de telemetría
    double duracion = 30.0;       // s desde RUN; sin demora reglamentaria añadida
    double ruidoPiso = 15.0;      // desviación estándar del ADC
    double stopMs = -1;          // STOP sintético, desactivado por defecto
    double sobrecostoLoopUs = 20; // µs de loop() además de las lecturas
};

enum class Modo { Ninguno, Estatico, Errante };

struct Robot {
    double x, y, th;  // posición del eje de ruedas y orientación (rad, antihorario)
    double vl, vr;    // velocidad real de cada rueda
};

struct Enemigo {
    bool presente;
    double x, y, th;
};

Config cfg;
Modo modo = Modo::Ninguno;
Robot rob;
Enemigo ene;
std::mt19937 rng, rngEnemigo;
std::normal_distribution<double> ruidoEnemigo(0.0, 1.0);
std::normal_distribution<double> normal(0.0, 1.0);

int estadoSim = 0;
double velocidadPico = 0;
double tiempoAtaque = 0;
double tiempoBorde = 0, rachaBorde = 0, rachaBordeMax = 0;
bool ataqueRealizado = false;
double margenFisico = 1e9, salidaFisica = -1;
bool caidaFisica = false;
double maxRadioCuerpo();

double tiempoUs = 0;
double tiempoFisicaUs = 0;
double distanciaFisica = 0, tiempoFrontalFisico = 0, primerFrontalFisico = -1, primeraCaidaUs = -1;
FILE* trayectoriaActual = nullptr;
double inicioTrayUs = 0, proximaTray = 0;
bool enSetup = true;
uint8_t nivelPin[32];
int pwmPin[32];

double aleatorio(double a, double b) {
    return std::uniform_real_distribution<double>(a, b)(rng);
}

void aMundo(double rx, double ry, double& wx, double& wy) {
    const double c = std::cos(rob.th), s = std::sin(rob.th);
    wx = rob.x + c * rx - s * ry;
    wy = rob.y + s * rx + c * ry;
}

// ---------------------------------------------------------------- sensores

double valorPiso(double wx, double wy) {
    const double r = std::hypot(wx, wy);
    if (r <= cfg.radio - cfg.borde) return cfg.adcNegro;
    if (r <= cfg.radio) return cfg.adcBlanco;
    return cfg.adcFuera;
}

// El sensor promedia un área pequeña, así que la transición negro-blanco no es instantánea
int lecturaPiso(double rx, double ry) {
    double wx, wy;
    aMundo(rx, ry, wx, wy);
    const double m = cfg.manchaSensor;
    double valor = (valorPiso(wx, wy) * 2 + valorPiso(wx + m, wy) + valorPiso(wx - m, wy) +
                    valorPiso(wx, wy + m) + valorPiso(wx, wy - m)) / 6;
    valor += normal(rng) * cfg.ruidoPiso;
    return (int)constrain(valor, 0.0, 1023.0);
}

bool sobreBlanco(double rx, double ry) {
    double wx, wy;
    aMundo(rx, ry, wx, wy);
    const double r = std::hypot(wx, wy);
    return r > cfg.radio - cfg.borde && r <= cfg.radio;
}

// Rayo desde (rx, ry) en el marco del robot con ángulo relativo ang
bool rayoVeEnemigo(double rx, double ry, double ang) {
    if (!ene.presente) return false;
    double ox, oy;
    aMundo(rx, ry, ox, oy);
    const double ux = std::cos(rob.th + ang), uy = std::sin(rob.th + ang);
    const double dx = ene.x - ox, dy = ene.y - oy;
    const double t = dx * ux + dy * uy;
    const double perp2 = dx * dx + dy * dy - t * t;
    const double r2 = cfg.radioEnemigo * cfg.radioEnemigo;
    if (perp2 > r2) return false;
    const double entrada = t - std::sqrt(r2 - perp2);
    const double salida = t + std::sqrt(r2 - perp2);
    return salida >= 0 && entrada <= cfg.rangoEnemigo;
}

// Objetos alrededor del dohyo (pared, muebles, personas) como un círculo de radio radioPared
bool rayoVePared(double rx, double ry, double ang) {
    if (cfg.radioPared <= 0) return false;
    double ox, oy;
    aMundo(rx, ry, ox, oy);
    const double ux = std::cos(rob.th + ang), uy = std::sin(rob.th + ang);
    // Distancia hasta salir del círculo: |o + t·u| = R
    const double b = ox * ux + oy * uy;
    const double c = ox * ox + oy * oy - cfg.radioPared * cfg.radioPared;
    const double t = -b + std::sqrt(b * b - c);
    return t <= cfg.rangoEnemigo;
}

bool rayoVe(double rx, double ry, double ang) {
    return rayoVeEnemigo(rx, ry, ang) || rayoVePared(rx, ry, ang);
}

bool sensorEnemigo(uint8_t pin) {
    if (cfg.pruebaSensores == "seguimiento-movil") {
        if (tiempoUs < 80000) return pin == S_FRONT_CEN;
        if (tiempoUs < 140000) return pin == S_FRONT_DER;
        if (tiempoUs < 200000) return pin == S_FRONT_CEN;
        if (tiempoUs < 260000) return pin == S_FRONT_IZQ;
        if (tiempoUs < 380000) return false;
        if (tiempoUs < 460000) return pin == S_FRONT_IZQ;
        return pin == S_FRONT_CEN;
    }
    if (cfg.pruebaSensores == "derecha-central-perdida") {
        if (tiempoUs < 100000) return pin == S_FRONT_DER;
        return tiempoUs < 160000 && pin == S_FRONT_CEN;
    }
    if (cfg.pruebaSensores == "central-intermitente")
        return pin == S_FRONT_CEN && (static_cast<unsigned long>(tiempoUs / 20000) % 3) < 2;
    if (cfg.pruebaSensores == "lateral-a-tres-frontales")
        return tiempoUs < 100000 ? pin == S_LAT_DER : (pin == S_FRONT_IZQ || pin == S_FRONT_CEN || pin == S_FRONT_DER);
    if (cfg.pruebaSensores == "lateral-central-perdida")
        return tiempoUs < 100000 ? pin == S_LAT_DER : (tiempoUs < 160000 && pin == S_FRONT_CEN);
    if (cfg.pruebaSensores == "lateral-derecho-breve")
        return tiempoUs < 100000 && pin == S_LAT_DER;
    if (cfg.pruebaSensores == "empuje-senal-perdida")
        return pin == S_FRONT_CEN && (tiempoUs < 100000 || tiempoUs >= 500000);
    if (cfg.pruebaSensores == "empuje-lateral-transitorio")
        return tiempoUs < 100000 ? pin == S_FRONT_CEN : (tiempoUs < 500000 ? pin == S_LAT_DER : pin == S_FRONT_CEN);
    if (cfg.pruebaSensores == "frontales-dobles")
        return pin == S_FRONT_IZQ || pin == S_FRONT_DER;
    if (cfg.pruebaSensores == "frontal-a-central")
        return pin == (tiempoUs < 100000 ? S_FRONT_DER : S_FRONT_CEN);
    if (cfg.pruebaSensores == "central-a-frontal")
        return pin == (tiempoUs < 100000 ? S_FRONT_CEN : S_FRONT_IZQ);
    if (cfg.pruebaSensores == "central-y-lateral")
        return pin == S_FRONT_CEN || pin == S_LAT_DER;
    if (cfg.pruebaSensores == "central-curva")
        return pin == S_FRONT_CEN || (pin == S_FRONT_DER && tiempoUs >= 60000 && tiempoUs < 120000);
    if (cfg.pruebaSensores == "alternante") {
        const bool derecha = ((unsigned long)(tiempoUs / 10000) % 2) == 0;
        return pin == (derecha ? S_FRONT_DER : S_FRONT_IZQ);
    }
    if (cfg.pruebaSensores == "laterales") return pin == S_LAT_DER || pin == S_LAT_IZQ;
    if (cfg.pruebaSensores == "lateral-izquierdo") return pin == S_LAT_IZQ;
    if (cfg.pruebaSensores == "lateral-derecho") return pin == S_LAT_DER;
    if (cfg.pruebaSensores == "lateral-a-frontal")
        return pin == (tiempoUs < 100000 ? S_LAT_DER : S_FRONT_CEN);
    // Aparición del rival en cada fase del escape desde el borde.
    if (cfg.pruebaSensores == "escape-frontal-retroceso")
        return pin == S_FRONT_CEN;
    if (cfg.pruebaSensores == "escape-frontal-pausa-retroceso")
        return tiempoUs >= 260000 && pin == S_FRONT_CEN;
    if (cfg.pruebaSensores == "escape-frontal-giro")
        return tiempoUs >= 360000 && pin == S_FRONT_CEN;
    if (cfg.pruebaSensores == "escape-frontal-pausa-giro")
        return tiempoUs >= 800000 && pin == S_FRONT_CEN;

    const double fx = cfg.largo / 2, ly = cfg.ancho / 2;
    if (pin == S_FRONT_CEN) return rayoVe(fx, 0, 0);
    if (pin == S_FRONT_IZQ) return rayoVe(fx, ly * 0.6, PI / 4);
    if (pin == S_FRONT_DER) return rayoVe(fx, -ly * 0.6, -PI / 4);
    if (pin == S_LAT_IZQ) return rayoVe(0, ly, PI / 2);
    if (pin == S_LAT_DER) return rayoVe(0, -ly, -PI / 2);
    return false;
}

// ---------------------------------------------------------------- física

int comandoMotor(uint8_t in1, uint8_t in2, uint8_t pwm) {
    const int magnitud = pwmPin[pwm];
    if (nivelPin[in1] == nivelPin[in2]) return 0;  // freno / libre
    const bool invertido = pwm == PWMA ? cfg.invertirCanalA : cfg.invertirCanalB;
    const int signo = nivelPin[in1] == HIGH ? -1 : 1;
    return magnitud * signo * (invertido ? -1 : 1);
}

// Aplica una fricción de Coulomb de magnitud f a un movimiento con velocidad vel
// y fuerza impulsora fuerza. Si está quieto y la fuerza no supera la fricción, no arranca.
double conFriccion(double fuerza, double vel, double f) {
    if (std::fabs(vel) < 1e-4) {
        if (std::fabs(fuerza) <= f) return 0;
        return fuerza - (fuerza > 0 ? f : -f);
    }
    return fuerza - (vel > 0 ? f : -f);
}

// Motor DC: F = Fb·(u·batería − v/v0), menos la fricción de la reductora,
// limitada por la adherencia de cada rueda.
double fuerzaRueda(int comando, double vRueda, bool circuitoCerrado) {
    const double u = comando / 255.0 * cfg.bateria;
    const double v0 = cfg.rpm / 60.0 * PI * cfg.diametro;
    const double fuerzaBloqueo = cfg.parBloqueo * 0.0981 / (cfg.diametro / 2);
    // En rueda libre no hay frenado electromagnético; con puente activo sí.
    const double electrica = circuitoCerrado ? fuerzaBloqueo * (u - vRueda / v0) : 0;
    double f = conFriccion(electrica, vRueda, cfg.friccionCaja * fuerzaBloqueo);
    const double adherencia = cfg.mu * cfg.masa / 2 * 9.81;
    return constrain(f, -adherencia, adherencia);
}

int comandoIzquierdo() {
    return cfg.canalesIntercambiados ? comandoMotor(MA1B,MA2B,PWMB) : comandoMotor(MA1A,MA2A,PWMA);
}
int comandoDerecho() {
    return cfg.canalesIntercambiados ? comandoMotor(MA1A,MA2A,PWMA) : comandoMotor(MA1B,MA2B,PWMB);
}

// Cuerpo rígido: avance v y giro w con rodadura y roce lateral al girar
void avanzarCuerpoDC(int cmdIzq, int cmdDer, double dt) {
    const double b = cfg.trocha / 2;
    double v = (rob.vl + rob.vr) / 2;
    double w = (rob.vr - rob.vl) / cfg.trocha;
    const double fi = fuerzaRueda(cmdIzq, rob.vl, pwmPin[cfg.canalesIntercambiados ? PWMB : PWMA] > 0);
    const double fd = fuerzaRueda(cmdDer, rob.vr, pwmPin[cfg.canalesIntercambiados ? PWMA : PWMB] > 0);
    const double peso = cfg.masa * 9.81;
    const double inercia = cfg.masa * (cfg.largo * cfg.largo + cfg.ancho * cfg.ancho) / 12;
    const double fuerza = conFriccion(fi + fd, v, cfg.rodadura * peso);
    const double par = conFriccion((fd - fi) * b, w, cfg.friccionGiro * peso * cfg.brazoGiro);
    double vNueva = v + fuerza / cfg.masa * dt;
    double wNueva = w + par / inercia * dt;
    // La fricción frena hasta cero, no invierte el movimiento
    if (v != 0 && vNueva * v < 0 && std::fabs(fi + fd) < cfg.rodadura * peso) vNueva = 0;
    if (w != 0 && wNueva * w < 0 && std::fabs((fd - fi) * b) < cfg.friccionGiro * peso * cfg.brazoGiro) wNueva = 0;
    rob.vl = vNueva - wNueva * b;
    rob.vr = vNueva + wNueva * b;
}

void avanzarRueda(double& v, int comando, double dt) {
    const double objetivo = comando / 255.0 * cfg.vmax;
    double dv = (objetivo - v) * dt / cfg.tau;
    const double maxDv = cfg.mu * 9.81 * dt;
    dv = constrain(dv, -maxDv, maxDv);
    v += dv;
}

void avanzarRobot(double dt) {
    if (caidaFisica) return;
    const double xAntes = rob.x, yAntes = rob.y;
    if (cfg.rpm > 0) {
        avanzarCuerpoDC(comandoIzquierdo(), comandoDerecho(), dt);
    } else {
        avanzarRueda(rob.vl, comandoIzquierdo(), dt);
        avanzarRueda(rob.vr, comandoDerecho(), dt);
    }
    const double v = (rob.vl + rob.vr) / 2;
    const double w = (rob.vr - rob.vl) / cfg.trocha;
    rob.x += v * std::cos(rob.th) * dt;
    rob.y += v * std::sin(rob.th) * dt;
    rob.th += w * dt;
    velocidadPico = std::max(velocidadPico, std::fabs(v));
    if (trayectoriaActual && tiempoUs >= inicioTrayUs + proximaTray * 1e6) {
        proximaTray += cfg.pasoTray;
        const bool linea = sobreBlanco(cfg.sensorPisoX, cfg.sensorPisoY) || sobreBlanco(cfg.sensorPisoX, -cfg.sensorPisoY);
        std::fprintf(trayectoriaActual, "%.3f,%.4f,%.4f,%.4f,%.4f,%.4f,%d,%d,%d,%d\n",
                     (tiempoUs - inicioTrayUs) / 1e6, rob.x, rob.y, rob.th,
                     ene.presente ? ene.x : 0., ene.presente ? ene.y : 0.,
                     comandoIzquierdo(), comandoDerecho(), linea ? 1 : 0, estadoSim);
    }

    const double margen = cfg.radio - std::hypot(rob.x, rob.y);
    // Permanecer cerca del borde puede ocultar un escape que se repite sin salir.
    if (std::hypot(rob.x, rob.y) > cfg.radio - 0.09) {
        tiempoBorde += dt;
        rachaBorde += dt;
        rachaBordeMax = std::max(rachaBordeMax, rachaBorde);
    } else rachaBorde = 0;
    margenFisico = std::min(margenFisico, margen);
    salidaFisica = std::max(salidaFisica, maxRadioCuerpo() - cfg.radio);
    if (margen < 0 && !caidaFisica) primeraCaidaUs = tiempoUs;
    caidaFisica = caidaFisica || margen < 0;
    distanciaFisica += std::hypot(rob.x - xAntes, rob.y - yAntes);
    if (rayoVeEnemigo(cfg.largo / 2, 0, 0)) {
        tiempoFrontalFisico += dt;
        if (primerFrontalFisico < 0) primerFrontalFisico = (tiempoUs - inicioTrayUs) / 1e6;
    }
    if (estadoSim == 4) {
        tiempoAtaque += dt;
        ataqueRealizado = true;
    }
}

void avanzarEnemigo(double dt) {
    if (!ene.presente || modo != Modo::Errante) return;
    ene.th += ruidoEnemigo(rngEnemigo) * 3.0 * std::sqrt(dt);
    const double r = std::hypot(ene.x, ene.y);
    if (r > cfg.radio - 0.08) {
        // Se aleja del borde girando hacia el centro
        const double haciaCentro = std::atan2(-ene.y, -ene.x);
        double diff = std::remainder(haciaCentro - ene.th, 2 * PI);
        ene.th += diff * std::min(1.0, 8.0 * dt);
    }
    ene.x += cfg.velEnemigo * std::cos(ene.th) * dt;
    ene.y += cfg.velEnemigo * std::sin(ene.th) * dt;
}

double maxRadioCuerpo() {
    double m = 0;
    const double xs[2] = {-cfg.largo / 2, cfg.largo / 2};
    const double ys[2] = {-cfg.ancho / 2, cfg.ancho / 2};
    for (double rx : xs) {
        for (double ry : ys) {
            double wx, wy;
            aMundo(rx, ry, wx, wy);
            m = std::max(m, std::hypot(wx, wy));
        }
    }
    return m;
}

// El reloj avanza en cada acceso Arduino; integración fija de 0.1 ms.
// Así un escape bloqueante no acumula una integración gigante al volver al loop.
void avanzarTiempo(double us) {
    const double fin = tiempoUs + us;
    while (tiempoFisicaUs + 100 <= fin) {
        tiempoUs = tiempoFisicaUs;
        avanzarRobot(0.0001);
        avanzarEnemigo(0.0001);
        tiempoFisicaUs += 100;
    }
    tiempoUs = fin;
}

// ---------------------------------------------------------------- corrida

struct Resultado {
    bool cayo = false;
    double tCaida = -1;
    double margenMin = 1e9;      // m entre el centro del robot y el borde exterior
    double maxSalidaCuerpo = -1; // m que una esquina sobresale del borde
    int evasiones = 0;
    double tPrimerFrontal = -1;  // s hasta ver al enemigo de frente
    double fracFrontal = 0;      // fracción del tiempo con el enemigo de frente
    double ataque = 0;
    double velocidadMax = 0;
    double borde = 0, rachaBorde = 0;
    double inicialX = 0, inicialY = 0, inicialTh = 0;
    double distancia = 0;        // m recorridos
};

void imprimirCabecera() {
    std::printf("semilla,modo,cayo,t_caida,margen_min_cm,max_salida_cuerpo_cm,evasiones,"
                "t_primer_frontal,frac_frontal,distancia_m,tiempo_ataque_s,x_inicial_cm,y_inicial_cm,orientacion_inicial_deg,velocidad_max_m_s,tiempo_borde_s,racha_borde_max_s\n");
}

const char* nombreModo(Modo m) {
    switch (m) {
    case Modo::Estatico: return "estatico";
    case Modo::Errante: return "errante";
    default: return "ninguno";
    }
}

Resultado correr(int semilla, FILE* trayectoria) {
    rng.seed(semilla);
    rngEnemigo.seed(semilla ^ 0x9e3779b9);
    std::memset(nivelPin, 0, sizeof(nivelPin));
    std::memset(pwmPin, 0, sizeof(pwmPin));
    tiempoUs = 0;

    if (cfg.inicio == "malla") {
        // 4 radios × 12 sectores × 8 orientaciones relativas = 384 arranques.
        const int indice = (semilla - 1) % 384;
        const double ang = 2 * PI * ((indice / 8) % 12) / 12;
        const double relativo = 2 * PI * (indice % 8) / 8;
        const double fracciones[4] = {0., 0.5, 0.9, 0.995};
        double limite = cfg.radio;
        for (double x : {-cfg.largo/2, cfg.largo/2}) {
            for (double y : {-cfg.ancho/2, cfg.ancho/2}) {
                const double dx = x * std::cos(relativo) - y * std::sin(relativo);
                const double dy = x * std::sin(relativo) + y * std::cos(relativo);
                limite = std::min(limite, -dx + std::sqrt(cfg.radio * cfg.radio - dy * dy));
            }
        }
        const double r = fracciones[indice / 96] * limite;
        rob = {r * std::cos(ang), r * std::sin(ang), ang + relativo, 0, 0};
    } else if (cfg.inicio == "fijo") {
        rob = {cfg.inicioX, cfg.inicioY, cfg.inicioTh * PI / 180, 0, 0};
        if (maxRadioCuerpo() > cfg.radio + 1e-9) {
            std::fprintf(stderr, "Posición inicial inválida: el cuerpo de 10x10 cm no cabe en el dojo.\n");
            _exit(2);
        }
    } else {
        // Muestreo uniforme en área; no se excluyen sensores sobre blanco.
        do {
            const double rIni = std::sqrt(aleatorio(0, 1)) * cfg.radioInicio;
            const double aIni = aleatorio(-PI, PI);
            rob = {rIni * std::cos(aIni), rIni * std::sin(aIni), aleatorio(-PI, PI), 0, 0};
        } while (maxRadioCuerpo() > cfg.radio ||
                 (cfg.inicio == "borde" && std::hypot(rob.x, rob.y) < 0.26));
    }
    const double inicialX = rob.x, inicialY = rob.y, inicialTh = rob.th;

    ene.presente = modo != Modo::Ninguno;
    if (ene.presente) {
        const double r = std::sqrt(aleatorio(0, 1)) * (cfg.radio - 0.06);
        const double a = aleatorio(-PI, PI);
        ene = cfg.rivalFijo ? Enemigo{true,cfg.rivalX,cfg.rivalY,cfg.rivalTheta * PI / 180} : Enemigo{true,r * std::cos(a),r * std::sin(a),aleatorio(-PI,PI)};
    }

    enSetup = true;
    setup();
    enSetup = false;
    const double inicioUs = tiempoUs;

    trayectoriaActual = trayectoria;
    inicioTrayUs = inicioUs;
    proximaTray = 0;
    Resultado res;
    res.inicialX = inicialX; res.inicialY = inicialY; res.inicialTh = inicialTh;
    bool lineaAntes = false;


    while (true) {
        const double t = (tiempoUs - inicioUs) / 1e6;
        if (t >= cfg.duracion) break;

        loop();
        avanzarTiempo(cfg.sobrecostoLoopUs);

        const bool linea = sobreBlanco(cfg.sensorPisoX, cfg.sensorPisoY) ||
                           sobreBlanco(cfg.sensorPisoX, -cfg.sensorPisoY);
        if (linea && !lineaAntes) res.evasiones++;
        lineaAntes = linea;

        // El robot cae cuando su centro de masa sale del dohyo
        if (caidaFisica) {
            res.cayo = true;
            res.tCaida = (primeraCaidaUs - inicioUs) / 1e6;
            break;
        }
    }
    res.margenMin = margenFisico;
    res.maxSalidaCuerpo = salidaFisica;
    res.ataque = tiempoAtaque;
    res.velocidadMax = velocidadPico;
    res.borde = tiempoBorde;
    res.rachaBorde = rachaBordeMax;
    res.fracFrontal = tiempoFrontalFisico / cfg.duracion;
    res.tPrimerFrontal = primerFrontalFisico;
    res.distancia = distanciaFisica;
    if (trayectoria) {
        const bool linea = sobreBlanco(cfg.sensorPisoX, cfg.sensorPisoY) || sobreBlanco(cfg.sensorPisoX, -cfg.sensorPisoY);
        std::fprintf(trayectoria, "%.3f,%.4f,%.4f,%.4f,%.4f,%.4f,%d,%d,%d,%d\n",
            (tiempoUs - inicioUs) / 1e6, rob.x, rob.y, rob.th, ene.presente ? ene.x : 0., ene.presente ? ene.y : 0.,
            comandoIzquierdo(), comandoDerecho(), linea ? 1 : 0, estadoSim);
    }
    return res;
}

void uso() {
    std::fprintf(stderr,
                 "uso: sim [--modo ninguno|estatico|errante] [--n N] [--semilla S]\n"
                 "         [--dur s] [--vmax m/s] [--mu μ] [--tau s] [--rango m]\n"
                 "         [--rpm rpm --diam m --masa kg --par kg·cm]  (modelo de motor DC)\n"
                 "         [--bateria Vbat/Vmotor] [--friccion-caja f] [--friccion-giro f]\n"
                 "         [--adc-negro n --adc-blanco n --adc-fuera n] [--pared m] [--sensor-x m]\n"
                 "         [--tray archivo.csv]  (guarda la trayectoria de la primera corrida)\n");
}

}  // namespace

void registrarEstadoSim(int estado) { estadoSim = estado; }

// ---------------------------------------------------------------- Arduino simulado

extern "C" {

void delay(unsigned long ms) { avanzarTiempo(ms * 1000.0); }
unsigned long millis(void) { avanzarTiempo(4); return (unsigned long)(tiempoUs / 1000); }
unsigned long micros(void) { avanzarTiempo(4); return (unsigned long)tiempoUs; }

int analogRead(uint8_t pin) {
    avanzarTiempo(112);  // conversión ADC con prescaler 128 a 16 MHz
    if ((pin == S_PISO_IZQ || pin == S_PISO_DER) && cfg.pruebaPiso == "negro-con-ruido")
        return (int)(720 + 190 * ((unsigned long)(tiempoUs / 2000) % 2));
    if ((pin == S_PISO_IZQ || pin == S_PISO_DER) && cfg.pruebaPiso == "borde-persistente")
        return (int)(tiempoUs < 900000 ? cfg.adcBlanco : cfg.adcNegro);
    if ((pin == S_PISO_IZQ || pin == S_PISO_DER) && cfg.pruebaPiso == "escape-repetido-largo")
        return (int)(((tiempoUs < 50000) || (tiempoUs >= 400000 && tiempoUs < 450000)) ? cfg.adcBlanco : cfg.adcNegro);
    if ((pin == S_PISO_IZQ || pin == S_PISO_DER) && cfg.pruebaPiso == "escape-repetido")
        return (int)(((tiempoUs < 50000) || (tiempoUs >= 200000 && tiempoUs < 250000)) ? cfg.adcBlanco : cfg.adcNegro);
    if ((pin == S_PISO_IZQ || pin == S_PISO_DER) && cfg.pruebaPiso == "escape")
        return (int)(tiempoUs < 200000 ? cfg.adcBlanco : cfg.adcNegro);
    if ((pin == S_PISO_IZQ || pin == S_PISO_DER) &&
        (cfg.pruebaPiso == "rampa" || cfg.pruebaPiso == "rampa-fuera")) {
        // Transición sintética hacia blanco entre 50 y 66 ms, negro desde 120 ms.
        const double t = tiempoUs / 1000.0;
        if (t >= 120 && cfg.pruebaPiso == "rampa-fuera") return (int)cfg.adcFuera;
        const double fraccion = t >= 120 ? 0 : constrain((t - 50) / 16, 0.0, 1.0);
        return (int)(cfg.adcNegro + fraccion * (cfg.adcBlanco - cfg.adcNegro));
    }
    if ((pin == S_PISO_IZQ || pin == S_PISO_DER) && cfg.pruebaPiso == "negro")
        return (int)cfg.adcNegro;
    if (pin == S_PISO_IZQ) return lecturaPiso(cfg.sensorPisoX, cfg.sensorPisoY);
    if (pin == S_PISO_DER) return lecturaPiso(cfg.sensorPisoX, -cfg.sensorPisoY);
    return 0;
}

int digitalRead(uint8_t pin) {
    avanzarTiempo(4);
    if (pin == Pin_Control_Remoto) {
        const bool activo = cfg.stopMs < 0 || tiempoUs < cfg.stopMs * 1000;
        return activo == REMOTE_ACTIVE_HIGH ? HIGH : LOW;
    }
    return sensorEnemigo(pin) == ENEMIGO_ACTIVE_HIGH ? HIGH : LOW;
}

void digitalWrite(uint8_t pin, uint8_t value) {
    avanzarTiempo(4);
    if (pin < 32) nivelPin[pin] = value ? HIGH : LOW;
}

void analogWrite(uint8_t pin, int value) {
    avanzarTiempo(6);
    if (pin < 32) pwmPin[pin] = constrain(value, 0, 255);
}

void pinMode(uint8_t, uint8_t) {}

}  // extern "C"

int main(int argc, char** argv) {
    int n = 100;
    int semilla = 1;
    const char* rutaTray = nullptr;
    for (int i = 1; i < argc; i++) {
        const std::string a = argv[i];
        const char* v = (i + 1 < argc) ? argv[i + 1] : nullptr;
        if (!v) { uso(); return 1; }
        if (a == "--modo") {
            const std::string m = v;
            modo = m == "estatico" ? Modo::Estatico : m == "errante" ? Modo::Errante : Modo::Ninguno;
        } else if (a == "--n") n = std::atoi(v);
        else if (a == "--semilla") semilla = std::atoi(v);
        else if (a == "--dur") cfg.duracion = std::atof(v);
        else if (a == "--vmax") cfg.vmax = std::atof(v);
        else if (a == "--mu") cfg.mu = std::atof(v);
        else if (a == "--tau") cfg.tau = std::atof(v);
        else if (a == "--rpm") cfg.rpm = std::atof(v);
        else if (a == "--diam") cfg.diametro = std::atof(v);
        else if (a == "--masa") cfg.masa = std::atof(v);
        else if (a == "--par") cfg.parBloqueo = std::atof(v);
        else if (a == "--bateria") cfg.bateria = std::atof(v);
        else if (a == "--friccion-caja") cfg.friccionCaja = std::atof(v);
        else if (a == "--friccion-giro") cfg.friccionGiro = std::atof(v);
        else if (a == "--adc-negro") cfg.adcNegro = std::atof(v);
        else if (a == "--adc-blanco") cfg.adcBlanco = std::atof(v);
        else if (a == "--adc-fuera") cfg.adcFuera = std::atof(v);
        else if (a == "--pared") cfg.radioPared = std::atof(v);
        else if (a == "--sensor-prueba") cfg.pruebaSensores = v;
        else if (a == "--piso-prueba") cfg.pruebaPiso = v;
        else if (a == "--sensor-x") cfg.sensorPisoX = std::atof(v);
        else if (a == "--inicio-r") cfg.radioInicio = std::atof(v);
        else if (a == "--inicio") cfg.inicio = v;
        else if (a == "--x") cfg.inicioX = std::atof(v);
        else if (a == "--y") cfg.inicioY = std::atof(v);
        else if (a == "--rival-x") { cfg.rivalX = std::atof(v); cfg.rivalFijo = true; }
        else if (a == "--rival-y") { cfg.rivalY = std::atof(v); cfg.rivalFijo = true; }
        else if (a == "--rival-theta") { cfg.rivalTheta = std::atof(v); cfg.rivalFijo = true; }
        else if (a == "--theta") cfg.inicioTh = std::atof(v);
        else if (a == "--rango") cfg.rangoEnemigo = std::atof(v);
        else if (a == "--vel-enemigo") cfg.velEnemigo = std::atof(v);
        else if (a == "--ruido-piso") cfg.ruidoPiso = std::atof(v);
        else if (a == "--stop-ms") cfg.stopMs = std::atof(v);
        else if (a == "--loop-us") cfg.sobrecostoLoopUs = std::atof(v);
        else if (a == "--canales-intercambiados") cfg.canalesIntercambiados = std::string(v) == "true";
        else if (a == "--invertir-canal-a") cfg.invertirCanalA = std::string(v) == "true";
        else if (a == "--invertir-canal-b") cfg.invertirCanalB = std::string(v) == "true";
        else if (a == "--tray-ms") cfg.pasoTray = std::max(0.0001, std::atof(v)/1000.0);
        else if (a == "--tray") rutaTray = v;
        else { uso(); return 1; }
        i++;
    }

    if (cfg.inicio == "centro") cfg.radioInicio = 0.12;
    if (n < 1 || cfg.duracion <= 0 || cfg.radioInicio <= 0 ||
        (cfg.inicio == "borde" && cfg.radioInicio <= 0.26) ||
        (cfg.inicio != "todo" && cfg.inicio != "centro" && cfg.inicio != "borde" && cfg.inicio != "fijo" && cfg.inicio != "malla")) {
        uso(); return 2;
    }
    imprimirCabecera();
    std::fflush(stdout);
    for (int i = 0; i < n; i++) {
        const int s = semilla + i;
        const pid_t pid = fork();
        if (pid < 0) { std::perror("fork"); return 2; }
        if (pid == 0) {
            FILE* tray = (rutaTray && i == 0) ? std::fopen(rutaTray, "w") : nullptr;
            const Resultado r = correr(s, tray);
            if (tray) std::fclose(tray);
            std::printf("%d,%s,%d,%.3f,%.2f,%.2f,%d,%.3f,%.3f,%.2f,%.3f,%.3f,%.3f,%.2f,%.3f,%.3f,%.3f\n", s, nombreModo(modo),
                        r.cayo ? 1 : 0, r.tCaida, r.margenMin * 100, r.maxSalidaCuerpo * 100,
                        r.evasiones, r.tPrimerFrontal, r.fracFrontal, r.distancia, r.ataque, r.inicialX * 100, r.inicialY * 100, r.inicialTh * 180 / PI, r.velocidadMax, r.borde, r.rachaBorde);
            std::fflush(stdout);
            _exit(0);
        }
        int estado = 0;
        waitpid(pid, &estado, 0);
        if (!WIFEXITED(estado) || WEXITSTATUS(estado) != 0) return 2;
    }
    return 0;
}
