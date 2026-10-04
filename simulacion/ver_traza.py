#!/usr/bin/env python3
"""Imprime los cambios de comando de una trayectoria (últimos N segundos)."""
import csv, math, sys
ruta, ultimos = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
filas = list(csv.reader(open(ruta)))
tfin = float(filas[-1][0])
prev = None
for fila in filas:
    t, x, y, th, ex, ey, l, r, lin = fila[:9]
    if float(t) < tfin - ultimos:
        continue
    clave = (l, r, lin)
    if clave != prev:
        rad = math.hypot(float(x), float(y)) * 100
        dene = math.hypot(float(x) - float(ex), float(y) - float(ey)) * 100
        rene = math.hypot(float(ex), float(ey)) * 100
        print(f"t={t} r={rad:5.1f}cm th={math.degrees(float(th)) % 360:3.0f}° cmd=({l:>4},{r:>4}) "
              f"linea={lin} enemigo: r={rene:4.1f}cm dist={dene:4.1f}cm")
    prev = clave
