#!/usr/bin/env python3
"""Lotes del seguimiento actual con dirección de giro corregida."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import simular, arranques, agresivo, visualizar

def ejecutar(n=30):
    b=simular.compilar({})
    base=Path(__file__).resolve().parent/'resultados/seguimiento/lotes'
    def correr(key):
        nombre,desc,extra=arranques.ENTORNOS[key]
        extra=extra+['--canales-intercambiados','true']
        r=arranques.guardar(b,key,'Seguimiento · '+nombre,desc,key,extra,n,{},base)
        ruta=base/key/'meta.json';m=json.loads(ruta.read_text())
        m['version']='retirada-larga-frontal-interrumpe-v10';m['parametros']=agresivo.parametros_actuales()
        ruta.write_text(json.dumps(m,ensure_ascii=False,indent=2))
        return key,r
    with ThreadPoolExecutor(max_workers=3) as ex:
        resumen=dict(ex.map(correr,['todo','borde','enemigo_rapido']))
    (base.parent/'resumen.json').write_text(json.dumps(resumen,ensure_ascii=False,indent=2))
    visualizar.generar(base)
    return resumen

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--n',type=int,default=30);a=p.parse_args()
    if a.n<1:p.error('--n debe ser positivo')
    ejecutar(a.n)
