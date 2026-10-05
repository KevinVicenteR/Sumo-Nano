#!/usr/bin/env python3
"""Ejecuta lotes de combates con el firmware actual y genera resultados/visor.html."""
import argparse
import csv
import json
import math
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import simular

RAIZ = Path(__file__).resolve().parent
BASE = ['--rpm', '750', '--masa', '0.3', '--dur', '30']
ENTORNOS = {
    'todo': ('Todo el dojo', 'Arranques aleatorios con el cuerpo completo dentro del círculo.', ['--inicio', 'todo']),
    'borde': ('Junto al borde', 'Centro entre 26 cm y el máximo admisible; orientación aleatoria.', ['--inicio', 'borde']),
    'enemigo_rapido': ('Enemigo rápido', 'Enemigo a 0.6 m/s y arranques en todo el dojo.', ['--inicio', 'todo', '--vel-enemigo', '0.6']),
    'resbaloso': ('Piso resbaloso', 'Adherencia μ=0.3, batería +30 % y arranque junto al borde.', ['--inicio', 'borde', '--mu', '0.3', '--bateria', '1.3', '--friccion-caja', '0.08']),
    'objetos': ('Objetos alrededor', 'Objetos exteriores a 50 cm del centro que pueden activar sensores.', ['--inicio', 'borde', '--pared', '0.5']),
}
ETIQUETAS = {'primera': 'Primera corrida', 'fallo': 'Ejemplo de caída', 'centro': 'Arranque central',
             'intermedio': 'Arranque intermedio', 'borde': 'Arranque junto al borde'}


def leer_traza(binario, modo, extra, semilla):
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / 'tray.csv'
        simular.ejecutar(binario, modo, 1, extra + ['--semilla', str(semilla)], ruta)
        filas = [[float(v) for v in r] for r in csv.reader(ruta.open())]
    muestras = filas[::5]
    if muestras[-1] != filas[-1]:
        muestras.append(filas[-1])
    return muestras


def estadisticas(filas):
    n = len(filas)
    return {
        'n': n,
        'caidas': sum(r['cayo'] == '1' for r in filas),
        'ataques': sum(float(r['tiempo_ataque_s']) > 0 for r in filas),
        'ataque_s': sum(float(r['tiempo_ataque_s']) for r in filas) / n,
        'frontal': sum(float(r['frac_frontal']) for r in filas) / n,
        'margen': min(float(r['margen_min_cm']) for r in filas),
        'saliente': max(float(r['max_salida_cuerpo_cm']) for r in filas),
        'borde': sum(float(r['tiempo_borde_s']) for r in filas) / n,
        'racha': max(float(r['racha_borde_max_s']) for r in filas),
        'velocidad': max(float(r['velocidad_max_m_s']) for r in filas),
    }


def correr_entorno(binario, clave, n):
    nombre, descripcion, opciones = ENTORNOS[clave]
    extra = BASE + opciones
    lote = {'nombre': nombre, 'descripcion': descripcion, 'entorno': clave, 'modos': {}}
    for modo in simular.MODOS:
        filas = simular.ejecutar(binario, modo, n, extra)
        semillas = {1: 'primera'}
        fallos = [r for r in filas if r['cayo'] == '1']
        if fallos:
            semillas[int(fallos[0]['semilla'])] = 'fallo'
        for radio, etiqueta in [(0., 'centro'), (15., 'intermedio'), (28., 'borde')]:
            fila = min(filas, key=lambda r: abs(math.hypot(float(r['x_inicial_cm']), float(r['y_inicial_cm'])) - radio))
            semillas.setdefault(int(fila['semilla']), etiqueta)
        cayo = {int(r['semilla']): int(r['cayo']) for r in filas}
        trazas = {str(s): {'filas': leer_traza(binario, modo, extra, s), 'semilla': s, 'cayo': cayo[s],
                           'nombre': f'{ETIQUETAS[e]} · semilla {s}'} for s, e in semillas.items()}
        lote['modos'][modo] = {
            'stats': estadisticas(filas),
            'trazas': trazas,
            'arranques': [[float(r['x_inicial_cm']), float(r['y_inicial_cm']), float(r['orientacion_inicial_deg']),
                           int(r['cayo']), int(float(r['tiempo_ataque_s']) > 0)] for r in filas],
        }
    print(nombre, {m: (d['stats']['caidas'], d['stats']['n']) for m, d in lote['modos'].items()}, flush=True)
    return clave, lote


def generar(n=30, round_competencia='0'):
    simular.BUILD.mkdir(parents=True, exist_ok=True)
    binario = simular.compilar({'ROUND_COMPETENCIA': round_competencia})
    with ThreadPoolExecutor(max_workers=3) as ex:
        datos = dict(ex.map(lambda k: correr_entorno(binario, k, n), ENTORNOS))
    salida = RAIZ / 'resultados' / 'visor.html'
    salida.parent.mkdir(parents=True, exist_ok=True)
    plantilla = (RAIZ / 'visor.template.html').read_text()
    salida.write_text(plantilla.replace('__DATOS__', json.dumps(datos, separators=(',', ':'))))
    print(salida)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=30, help='combates por entorno y modo')
    ap.add_argument('--round', default='0', choices=['0', '1', '2', '3'], help='apertura usada en los lotes')
    a = ap.parse_args()
    if a.n < 1:
        ap.error('--n debe ser positivo')
    generar(a.n, a.round)
