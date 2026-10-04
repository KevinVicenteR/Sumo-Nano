#!/usr/bin/env python3
"""Valida frenado y giro hacia sensores laterales; compara con el controlador anterior real."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import simular
from arranques import ENTORNOS,guardar
RAIZ=Path(__file__).resolve().parent
ANTES={}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=100);a=ap.parse_args()
    if a.n<1:ap.error('--n positivo requerido')
    base=RAIZ/'resultados'/'laterales'/'lotes'
    fuente=RAIZ/'referencias'/'Robot_lateral_anterior.cpp.txt'
    actual=simular.compilar({});anterior=simular.compilar(ANTES,fuente)
    tareas=[]
    for key,(nombre,desc,extra) in ENTORNOS.items():
        tareas.append((actual,key,nombre,desc,key,extra,384 if key=='malla' else a.n,{},base))
    for key in ['todo','borde']:
        nombre,desc,extra=ENTORNOS[key]
        tareas.append((anterior,'previo_'+key,'Antes · lateral sin freno · '+nombre,desc,key,extra,a.n,ANTES,base,fuente))
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda t:guardar(*t),tareas))
