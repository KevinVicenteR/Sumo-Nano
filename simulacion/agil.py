#!/usr/bin/env python3
"""Valida escape y ataque más ágiles; compara con el controlador anterior real."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import simular
from arranques import ENTORNOS,guardar
RAIZ=Path(__file__).resolve().parent
ANTES={'RETROCESO_MIN_MS':'120','TIEMPO_RETROCESO_MS':'240','PAUSA_ESCAPE_MS':'100','PAUSA_RETROCESO_MS':'100','PAUSA_GIRO_MS':'100','TIEMPO_GIRO_BORDE_FRENTE_MS':'150','TIEMPO_GIRO_BORDE_LADO_MS':'110','ATAQUE_IMPULSO_MS':'60','ATAQUE_PAUSA_MS':'60'}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=300);a=ap.parse_args()
    if a.n<1:ap.error('--n positivo requerido')
    base=RAIZ/'resultados'/'agil'/'lotes'
    fuente=RAIZ/'referencias'/'Robot_borde_lento.cpp.txt'
    actual=simular.compilar({});anterior=simular.compilar(ANTES,fuente)
    tareas=[]
    for key,(nombre,desc,extra) in ENTORNOS.items():
        tareas.append((actual,key,nombre,desc,key,extra,384 if key=='malla' else a.n,{},base))
    for key in ['todo','borde']:
        nombre,desc,extra=ENTORNOS[key]
        tareas.append((anterior,'previo_'+key,'Antes · escape y ataque lento · '+nombre,desc,key,extra,a.n,ANTES,base,fuente))
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda t:guardar(*t),tareas))
