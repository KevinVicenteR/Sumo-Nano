#!/usr/bin/env python3
"""Barrido de parámetros: prueba combinaciones y las ordena por caídas.

Cada combinación se evalúa en los 3 escenarios y en todos los entornos dados,
para elegir parámetros que funcionen aunque el robot real no sea exactamente
como el simulado.

  python3 simulacion/barrido.py TiempoRetroceso=80,120 VelocidadAtaque=130,160
  python3 simulacion/barrido.py VelocidadAtaque=130,160 --entorno="--bateria 1.3" --entorno="--pared 0.5"
  python3 simulacion/barrido.py VelocidadAtaque=130,160 --robusto      # entornos típicos
"""
import argparse
import json
from pathlib import Path
import itertools
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
import simular

ROBOT = ["--rpm", "750", "--diam", "0.03", "--masa", "0.3"]

# Variaciones plausibles del robot real que no se conocen con exactitud
ENTORNOS_ROBUSTOS = [
    "",                                              # robot nominal
    "--bateria 1.3 --friccion-caja 0.08 --friccion-giro 0.3",  # batería alta y motores suaves (rápido)
    "--friccion-caja 0.3 --friccion-giro 1.0",       # motores duros y mucho roce al girar
    "--pared 0.5 --bateria 1.15",                    # objetos a 15 cm del borde
    "--adc-negro 150 --adc-blanco 850 --adc-fuera 150",  # sensor de piso invertido
]


def evaluar(params, n, entornos, dur):
    b = simular.compilar(params)
    por_entorno = []
    for ent in entornos:
        extra = ROBOT + ["--dur", str(dur)] + ent.split()
        por_entorno.append([simular.resumir(m, simular.ejecutar(b, m, n, extra)) for m in simular.MODOS])
    return params, por_entorno


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("opciones", nargs="+", help="Nombre=v1,v2,...")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--dur", type=float, default=30)
    ap.add_argument("--entorno", action="append", default=[])
    ap.add_argument("--robusto", action="store_true")
    ap.add_argument("--salida", type=Path, help="JSON con todos los resultados")
    ap.add_argument("--mostrar", type=int, default=12)
    a = ap.parse_args()

    entornos = a.entorno or ([*ENTORNOS_ROBUSTOS] if a.robusto else [""])
    opciones = {k: v.split(",") for k, v in (o.split("=", 1) for o in a.opciones)}
    combos = [dict(zip(opciones, vals)) for vals in itertools.product(*opciones.values())]
    simular.BUILD.mkdir(parents=True, exist_ok=True)
    print(f"{len(combos)} combinaciones × {len(entornos)} entornos × 3 escenarios × {a.n} combates")
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        resultados = list(ex.map(lambda p: evaluar(p, a.n, entornos, a.dur), combos))

    def metricas(por_entorno):
        todos = [r for ent in por_entorno for r in ent]
        caidas = sum(r["caidas"] for r in todos)
        peor_margen = min(r["margen_p10"] for r in todos)
        con_enemigo = [r for ent in por_entorno for r in ent[1:]]
        frente = sum(r["frac_frontal"] for r in con_enemigo) / len(con_enemigo)
        ver = sorted(r["t_ver_mediana"] for r in con_enemigo)[len(con_enemigo) // 2]
        ataques = sum(r["ataques"] for r in con_enemigo)
        return caidas, peor_margen, frente, ver, ataques

    filas = sorted(((p, metricas(pe), pe) for p, pe in resultados),
                   key=lambda f: (f[1][0], -f[1][4], -f[1][2]))
    if a.salida:
        a.salida.parent.mkdir(parents=True, exist_ok=True)
        a.salida.write_text(json.dumps([{"parametros": p, "metricas": m, "entornos": e} for p,m,e in filas], indent=2))
    print(f"{'parámetros':<70}{'caídas':>8}{'p10 margen':>12}{'% frente':>10}{'ve':>8}")
    for params, (caidas, margen, frente, ver, ataques), pe in filas[:a.mostrar]:
        txt = " ".join(f"{k}={v}" for k, v in params.items() if len(opciones[k]) > 1)
        print(f"{txt:<70}{caidas:>8}{margen:>9.1f} cm{100 * frente:>8.0f} %{ver:>7.2f}s")
    if len(entornos) > 1:
        params, _, pe = filas[0]
        print("\nMejor combinación por entorno (caídas sin/est/err):")
        for ent, res in zip(entornos, pe):
            print(f"  {ent or 'nominal':<52}" + "/".join(str(r["caidas"]) for r in res))


if __name__ == "__main__":
    main()
