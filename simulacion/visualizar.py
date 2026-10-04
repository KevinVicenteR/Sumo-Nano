#!/usr/bin/env python3
"""Genera el visor actualizado con los lotes de arranque y telemetría real del firmware."""
import csv
import json
from pathlib import Path

RAIZ=Path(__file__).resolve().parent

def traza(ruta,semilla,nombre):
    rows=[[float(v) for v in r] for r in csv.reader(ruta.open())]
    muestras=rows[::5]
    if muestras[-1]!=rows[-1]:muestras.append(rows[-1])
    return {'filas':muestras,'semilla':semilla,'nombre':nombre}

def generar(base=None):
    datos={}
    if base is None:
        seguro=RAIZ/'resultados/seguridad/lotes'
        agresivo=RAIZ/'resultados/agresivo/lotes'
        base=agresivo if agresivo.exists() else seguro if seguro.exists() else RAIZ/'resultados/laterales/lotes'
    carpetas=sorted(base.glob('*'),key=lambda p:(p.name!='todo',p.name))
    for carpeta in carpetas:
        if not (carpeta/'meta.json').exists():continue
        if not all((carpeta/f'ejemplos_{m}.json').exists() for m in ['ninguno','estatico','errante']):continue
        e=json.loads((carpeta/'meta.json').read_text());e['modos']={}
        if 'laterales' in base.parts and not carpeta.name.startswith(('antes_','previo_')):e['nombre']='Lateral · '+e['nombre']
        for modo in ['ninguno','estatico','errante']:
            filas=list(csv.DictReader((carpeta/f'resultados_{modo}.csv').open()))
            e['modos'][modo]={'stats':{'n':len(filas),'caidas':sum(r['cayo']=='1' for r in filas),'ataques':sum(float(r['tiempo_ataque_s'])>0 for r in filas),'ataque_s':sum(float(r['tiempo_ataque_s']) for r in filas)/len(filas),'frontal':sum(float(r['frac_frontal']) for r in filas)/len(filas),'margen':min(float(r['margen_min_cm']) for r in filas),'saliente':max(float(r['max_salida_cuerpo_cm']) for r in filas),'borde':sum(float(r.get('tiempo_borde_s',0)) for r in filas)/len(filas),'racha':max(float(r.get('racha_borde_max_s',0)) for r in filas),'velocidad':max(float(r.get('velocidad_max_m_s',0)) for r in filas)},'trazas':{},'arranques':[[float(r['x_inicial_cm']),float(r['y_inicial_cm']),float(r['orientacion_inicial_deg']),int(r['cayo']),int(float(r['tiempo_ataque_s'])>0)] for r in filas]}
            for muestra in json.loads((carpeta/f'ejemplos_{modo}.json').read_text()):
                seed=muestra['semilla'];label=muestra['etiqueta']
                nombre={'primera':'Primera corrida','fallo':'Ejemplo de caída','centro':'Arranque central','intermedio':'Arranque intermedio','borde':'Arranque junto al borde'}[label]
                e['modos'][modo]['trazas'][str(seed)]=traza(carpeta/muestra['archivo'],seed,f'{nombre} · semilla {seed}')
                e['modos'][modo]['trazas'][str(seed)]['cayo']=int(next(r for r in filas if int(r['semilla'])==seed)['cayo'])
        datos[carpeta.name]=e
    if not datos:raise RuntimeError('No hay lotes completos en '+str(base))
    salida=RAIZ/'resultados'/'visor.html'
    salida.write_text((RAIZ/'visor.template.html').read_text().replace('__DATOS__',json.dumps(datos,separators=(',',':'))))
    print(salida)
    return datos

if __name__=='__main__':generar()
