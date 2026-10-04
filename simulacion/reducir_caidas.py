#!/usr/bin/env python3
"""Compara ajustes con semillas iguales; no modifica el firmware."""
import argparse
import csv
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import simular
from arranques import ENTORNOS

CANDIDATOS = {
    'actual': {},
    'prediccion_busqueda_moderada': {'VELOCIDAD_BUSQUEDA': '190', 'Velocidad_maxima': '190', 'VELOCIDAD_GIRO_LATERAL': '190', 'VELOCIDAD_DESATASCO': '190', 'Velocidad_estandar': '180', 'VELOCIDAD_GIRO_ESCAPE': '180'},
    'sin_prediccion': {},
    'prediccion_rapida_escape': {'PREDICCION_MUESTREO_MS': '1', 'PREDICCION_BORDE_MS': '25', 'Velocidad_estandar': '180', 'VELOCIDAD_GIRO_ESCAPE': '180'},
    'prediccion_rapida': {'PREDICCION_MUESTREO_MS': '1', 'PREDICCION_BORDE_MS': '25'},
    'prediccion_larga': {'PREDICCION_RETIRADA_MIN_MS': '100'},
    'prediccion_rapida_larga': {'PREDICCION_MUESTREO_MS': '1', 'PREDICCION_BORDE_MS': '25', 'PREDICCION_RETIRADA_MIN_MS': '100'},
    **{f'limite_{v}': {**{'VELOCIDAD_CURVA_INTERIOR': str(round(120*v/255)), 'VELOCIDAD_ATAQUE_CURVA_INTERIOR': str(round(140*v/255))}, **{k: str(v) for k in ['Velocidad_estandar', 'VELOCIDAD_GIRO_ESCAPE', 'VELOCIDAD_BUSQUEDA', 'Velocidad_maxima', 'Velocidad_maxima_Ataque', 'Velocidad_movimiento_seguir', 'VELOCIDAD_DESATASCO', 'VELOCIDAD_GIRO_LATERAL']}} for v in [120, 160, 190]},
    'piso_estable_60': {'PISO_LIBRE_MS': '60'},
    'escape_moderado_piso60': {'Velocidad_estandar': '180', 'VELOCIDAD_GIRO_ESCAPE': '180', 'PISO_LIBRE_MS': '60'},
    'escape_lento': {'Velocidad_estandar': '150', 'VELOCIDAD_GIRO_ESCAPE': '150'},
    'retroceso_largo': {'RETROCESO_MIN_MS': '200', 'TIEMPO_RETROCESO_MS': '300'},
    'escape_moderado_largo': {'Velocidad_estandar': '180', 'VELOCIDAD_GIRO_ESCAPE': '180', 'RETROCESO_MIN_MS': '200', 'TIEMPO_RETROCESO_MS': '300'},
    'freno_largo': {'PAUSA_ESCAPE_MS': '150'},
    'escape_y_ataque_moderados': {'Velocidad_estandar': '180', 'VELOCIDAD_GIRO_ESCAPE': '180', 'Velocidad_maxima_Ataque': '180'},
    'retroceso_corto': {'RETROCESO_MIN_MS': '60', 'TIEMPO_RETROCESO_MS': '120'},
    'escape_moderado': {'Velocidad_estandar': '180', 'VELOCIDAD_GIRO_ESCAPE': '180'},
    'busqueda_moderada': {'VELOCIDAD_BUSQUEDA': '160', 'Velocidad_maxima': '180'},
    'ataque_moderado': {'Velocidad_maxima_Ataque': '180'},
    'deteccion_temprana': {'BLANCO': '500', 'MARGEN_CERCA_BORDE': '80'},
    'pausas_cortas': {'PAUSA_ESCAPE_MS': '40', 'PAUSA_RETROCESO_MS': '30', 'PAUSA_GIRO_MS': '30'},
    'conservador': {'RETROCESO_MIN_MS': '60', 'TIEMPO_RETROCESO_MS': '120', 'Velocidad_estandar': '180', 'VELOCIDAD_GIRO_ESCAPE': '180', 'VELOCIDAD_BUSQUEDA': '160', 'Velocidad_maxima': '180', 'Velocidad_maxima_Ataque': '180', 'BLANCO': '500', 'MARGEN_CERCA_BORDE': '80', 'PAUSA_ESCAPE_MS': '40', 'PAUSA_RETROCESO_MS': '30', 'PAUSA_GIRO_MS': '30'},
}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n', type=int, default=30)
    ap.add_argument('--semilla', type=int, default=1)
    ap.add_argument('--candidatos', nargs='+', choices=CANDIDATOS, default=['sin_prediccion','actual','escape_moderado','limite_190','prediccion_busqueda_moderada'])
    ap.add_argument('--entornos', nargs='+', choices=ENTORNOS, default=['todo', 'borde'])
    ap.add_argument('--salida', type=Path, default=Path(__file__).parent/'resultados'/'reducir_caidas')
    a = ap.parse_args()
    if a.n < 1: ap.error('--n debe ser positivo')
    a.salida.mkdir(parents=True, exist_ok=True)
    fuentes = simular.FUENTES + sorted((simular.RAIZ/'include').glob('*.h')) + [simular.RAIZ/'simulacion/support/Arduino.h']
    referencia = simular.RAIZ/'simulacion/referencias/Robot_sin_prediccion.cpp.txt'
    if 'sin_prediccion' in a.candidatos:
        configuracion = referencia.with_name('Definiciones_sin_prediccion.h.txt')
        CANDIDATOS['sin_prediccion'] = {k:v.strip() for k,v in re.findall(r'^#define[ \t]+(\w+)[ \t]+([^\n/]+)', configuracion.read_text(), re.M)}
        fuentes.extend([referencia, configuracion])
    (a.salida/'meta.json').write_text(json.dumps({'n':a.n, 'semilla':a.semilla, 'duracion_s':30, 'parametros':{c:CANDIDATOS[c] for c in a.candidatos}, 'entornos':{e:ENTORNOS[e][2] for e in a.entornos}, 'fuentes_sha256':{str(p.relative_to(simular.RAIZ)):hashlib.sha256(p.read_bytes()).hexdigest() for p in fuentes}}, indent=2))
    binarios = {c:simular.compilar(CANDIDATOS[c], referencia if c == 'sin_prediccion' else None) for c in a.candidatos}
    def ejecutar(tarea):
        c,e,m = tarea
        filas = simular.ejecutar(binarios[c],m,a.n,['--rpm','750','--masa','0.3','--dur','30','--semilla',str(a.semilla)]+ENTORNOS[e][2])
        with (a.salida/f'{c}_{e}_{m}.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=filas[0].keys());w.writeheader();w.writerows(filas)
        r=simular.resumir(m,filas)
        print(f"{c} {e} {m}: {r['caidas']}/{a.n} caídas, {r['ataques']}/{a.n} ataques",flush=True)
        return {'candidato':c,'entorno':e,**r,'n':a.n}
    tareas=[(c,e,m) for c in a.candidatos for e in a.entornos for m in simular.MODOS]
    with ThreadPoolExecutor(max_workers=3) as pool:
        resultados=list(pool.map(ejecutar,tareas))
    (a.salida/'resumen.json').write_text(json.dumps(resultados,indent=2))
    for c in a.candidatos:
        filas=[r for r in resultados if r['candidato']==c]
        print(c, 'TOTAL',sum(r['caidas'] for r in filas),'/',sum(r['n'] for r in filas),flush=True)

if __name__ == '__main__': main()
