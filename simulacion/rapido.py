#!/usr/bin/env python3
"""Verifica velocidad y seguimiento ante lecturas contradictorias; conserva la comparación lenta."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import simular
from arranques import ENTORNOS,guardar

RAIZ=Path(__file__).resolve().parent
ANTERIOR={'FRENO_ACTIVO':'false','Velocidad_maxima_Ataque':'110','Velocidad_maxima':'110','VELOCIDAD_BUSQUEDA':'110','Velocidad_estandar':'100','TIEMPO_RETROCESO_MS':'320','PATRON_BUSQUEDA':'1','TIEMPO_BUSQUEDA_AVANCE_MS':'180','TIEMPO_BUSQUEDA_GIRO_MS':'200'}
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=300)
    ap.add_argument('--salida',type=Path,default=RAIZ/'resultados'/'maximo'/'lotes');a=ap.parse_args()
    if a.n<1:ap.error('--n positivo requerido')
    base=a.salida
    simular.BUILD.mkdir(parents=True,exist_ok=True)
    actual=simular.compilar({})
    anterior=simular.compilar(ANTERIOR,RAIZ/'resultados'/'rapido'/'Robot_anterior.cpp.txt')
    trabajos=[]
    for key,(nombre,desc,extra) in ENTORNOS.items():
        n=384 if key=='malla' else a.n
        trabajos.append((actual,key,nombre,desc,key,extra,n,{},base))
    for key in ['todo','objetos','alternante','laterales']:
        nombre,desc,extra=ENTORNOS[key]
        trabajos.append((anterior,'antes_'+key,'Anterior lento · '+nombre,desc,key,extra,a.n,ANTERIOR,base))
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda t:guardar(*t),trabajos))
