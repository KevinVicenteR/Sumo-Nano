#!/usr/bin/env python3
"""Compara avance fluido con el controlador predictivo anterior."""
import argparse
import csv
import json
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import simular
from arranques import ENTORNOS

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n',type=int,default=100)
    ap.add_argument('--semilla',type=int,default=501)
    ap.add_argument('--salida',type=Path,default=Path(__file__).parent/'resultados/fluidez')
    a=ap.parse_args()
    if a.n<1:ap.error('--n positivo requerido')
    a.salida.mkdir(parents=True,exist_ok=True)
    fuente=Path(__file__).parent/'referencias/Robot_prediccion_sin_fluidez.cpp.txt'
    archivos=simular.FUENTES+sorted((simular.RAIZ/'include').glob('*.h'))+[fuente,simular.RAIZ/'simulacion/support/Arduino.h']
    (a.salida/'meta.json').write_text(json.dumps({'semilla':a.semilla,'n':a.n,'duracion_s':30,'variantes':{'antes':str(fuente.relative_to(simular.RAIZ)),'fluido':{},'sin_arcos':{'BUSQUEDA_FLUIDA':'false'}},'fuentes_sha256':{str(p.relative_to(simular.RAIZ)):hashlib.sha256(p.read_bytes()).hexdigest() for p in archivos}},indent=2))
    bs={'antes':simular.compilar({},fuente),'fluido':simular.compilar({}),'sin_arcos':simular.compilar({'BUSQUEDA_FLUIDA':'false'})}
    def correr(t):
        c,e,m=t;p=a.salida/f'{c}_{e}_{m}.csv';tray=a.salida/f'tray_{c}_{e}_{m}.csv'
        fs=simular.ejecutar(bs[c],m,a.n,['--rpm','750','--dur','30','--semilla',str(a.semilla)]+ENTORNOS[e][2],tray)
        with p.open('w') as f:
            w=csv.DictWriter(f,fieldnames=fs[0].keys());w.writeheader();w.writerows(fs)
        r=simular.resumir(m,fs);print(c,e,m,r['caidas'],r['ataques'],flush=True)
        return {'controlador':c,'entorno':e,'n':a.n,**r}
    with ThreadPoolExecutor(max_workers=3) as pool:
        rs=list(pool.map(correr,[(c,e,m) for c in bs for e in ['todo','borde','bateria_alta','resbaloso'] for m in simular.MODOS]))
    (a.salida/'resumen.json').write_text(json.dumps(rs,indent=2))
    for c in bs:
        fs=[r for r in rs if r['controlador']==c]
        print(c,'TOTAL',sum(r['caidas'] for r in fs),'/',sum(r['n'] for r in fs),flush=True)
if __name__=='__main__':main()
