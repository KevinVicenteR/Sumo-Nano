#!/usr/bin/env python3
"""Simula las posiciones iniciales de los tres rounds con su apertura correspondiente."""
import argparse
import json
from pathlib import Path
import simular

POSES = {
    1: (-.055, -.055, 225, .055, .055, 45),
    2: (-.055, .055, 135, .055, -.055, -45),
    3: (-.26, 0, 0, .26, 0, 180),
}


def correr_pose(binario, ronda, pose, espejo, n, base):
    x, y, t, ex, ey, et = pose[3:] + pose[:3] if espejo else pose
    lado = 'espejo' if espejo else 'normal'
    resultados = []
    for modo in ('estatico', 'errante'):
        extra = ['--rpm', '750', '--dur', '30', '--inicio', 'fijo', '--x', str(x), '--y', str(y), '--theta', str(t),
                 '--rival-x', str(ex), '--rival-y', str(ey), '--rival-theta', str(et)]
        filas = simular.ejecutar(binario, modo, n, extra, base / f'round{ronda}_{lado}_{modo}.csv')
        r = simular.resumir(modo, filas)
        r.update(round=ronda, espejo=espejo)
        resultados.append(r)
        print(f'round {ronda} {lado:<7} {modo:<9} caídas {r["caidas"]}/{r["n"]}  '
              f'ataques {r["ataques"]}/{r["n"]}  ve al rival en {r["t_ver_mediana"]:.2f} s', flush=True)
    return resultados


def ejecutar(n=30):
    base = Path(__file__).resolve().parent / 'resultados' / 'competencia'
    base.mkdir(parents=True, exist_ok=True)
    simular.BUILD.mkdir(parents=True, exist_ok=True)
    resultados = []
    for ronda, pose in POSES.items():
        binario = simular.compilar({'ROUND_COMPETENCIA': str(ronda)})
        for espejo in (False, True):
            resultados += correr_pose(binario, ronda, pose, espejo, n, base)
    (base / 'resumen.json').write_text(json.dumps(resultados, indent=2, ensure_ascii=False))
    return resultados


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n', type=int, default=30, help='combates por pose y modo')
    a = ap.parse_args()
    if a.n < 1:
        ap.error('--n debe ser positivo')
    ejecutar(a.n)
