#!/usr/bin/env python3
"""Sirve resultados/visor.html y simula arranques elegidos en el visor con el firmware actual."""
import argparse
import json
import math
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import simular
from lotes import BASE, ENTORNOS, estadisticas, leer_traza

RAIZ = Path(__file__).resolve().parent
PUERTO = 8765
ORIGENES = (None, f'http://127.0.0.1:{PUERTO}', f'http://localhost:{PUERTO}')
BINARIOS = {}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(RAIZ / 'resultados'), **kwargs)

    def responder(self, codigo, contenido):
        datos = json.dumps(contenido, allow_nan=False).encode()
        self.send_response(codigo)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_POST(self):
        if self.path != '/api/simular':
            self.responder(404, {'error': 'Ruta desconocida'})
            return
        if self.headers.get('Origin') not in ORIGENES:
            self.responder(403, {'error': 'Origen no permitido'})
            return
        try:
            longitud = int(self.headers.get('Content-Length', 0))
            if not 0 < longitud < 4096:
                raise ValueError('Solicitud demasiado grande')
            a = json.loads(self.rfile.read(longitud))
            x, y, theta = float(a['x']) / 100, float(a['y']) / 100, float(a['theta'])
            if not all(math.isfinite(v) for v in (x, y, theta)) or abs(x) > .35 or abs(y) > .35 or abs(theta) > 360:
                raise ValueError('Coordenadas o ángulo fuera de rango')
            modo = a.get('modo', 'ninguno')
            entorno = a.get('entorno', 'todo')
            ronda = str(a.get('round', '0'))
            semilla = int(a.get('semilla', 1))
            if modo not in simular.MODOS or entorno not in ENTORNOS or ronda not in BINARIOS:
                raise ValueError('Opción desconocida')
            if not 1 <= semilla <= 100000:
                raise ValueError('La semilla debe estar entre 1 y 100000')
            extra = BASE + ENTORNOS[entorno][2] + ['--inicio', 'fijo', '--x', str(x), '--y', str(y), '--theta', str(theta)]
            filas = simular.ejecutar(BINARIOS[ronda], modo, 1, extra + ['--semilla', str(semilla)])
            cayo = int(filas[0]['cayo'])
            self.responder(200, {
                'stats': estadisticas(filas),
                'trazas': {'manual': {'nombre': f'Arranque elegido · semilla {semilla}', 'semilla': semilla,
                                      'cayo': cayo, 'filas': leer_traza(BINARIOS[ronda], modo, extra, semilla)}},
            })
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            self.responder(400, {'error': str(e)})
        except subprocess.CalledProcessError:
            self.responder(400, {'error': 'La posición inicial no permite colocar todo el robot dentro del dojo.'})


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    if not (RAIZ / 'resultados' / 'visor.html').exists():
        raise SystemExit('Primero genera el visor: python3 simulacion/lotes.py')
    simular.BUILD.mkdir(parents=True, exist_ok=True)
    for ronda in ('0', '1', '2', '3'):
        BINARIOS[ronda] = simular.compilar({'ROUND_COMPETENCIA': ronda})
    print(f'Visor: http://127.0.0.1:{PUERTO}/visor.html', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PUERTO), Handler).serve_forever()
