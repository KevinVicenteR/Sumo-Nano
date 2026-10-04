#!/usr/bin/env python3
"""Valida PID/Kalman a PWM 255; conserva resultados y snapshots históricos."""
import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import arranques
import simular
import visualizar

RAIZ=Path(__file__).resolve().parent
CLAVES=['ESCAPE_RETIRADA_ATAQUE_MS','BUSQUEDA_INTERIOR_PWM','RECUPERACION_LATERAL_GIRO_MS','VELOCIDAD_BUSQUEDA_PWM','VELOCIDAD_SEGUIMIENTO_PWM','VELOCIDAD_RETROCESO_PWM','VELOCIDAD_GIRO_PWM','BUSQUEDA_CAMBIO_LADO_MS','BUSQUEDA_CICLO_MS','MEMORIA_ATAQUE_MS','ESCAPE_GIRO_MIN_MS','ESCAPE_GIRO_MAX_MS','ESCAPE_REINTENTO_RETROCESO_MIN_MS','ESCAPE_REINTENTO_RETROCESO_MAX_MS','SEGUIMIENTO_PERDIDA_MS','INVERTIR_SENTIDO_GIRO','DOBLE_FRONTAL_CONFIRMACION_MS','ATAQUE_DOBLE_FRONTAL','MOTORES_MAXIMO_SIEMPRE','FILTRO_KALMAN_DIRECCION','PID_DIRECCION_KP','PID_DIRECCION_KI','PID_DIRECCION_KD','ESCAPE_RETROCESO_MIN_MS','ESCAPE_RETROCESO_MAX_MS','ESCAPE_GIRO_MS','PISO_LIBRE_MS','BUSQUEDA_ARCO_MS','BUSQUEDA_CORRECCION_PWM','BORDE_REPETIDO_VENTANA_MS','BORDE_REPETIDO_GIRO_MIN_MS']
def parametros_actuales(params=None):
    p=arranques.parametros(params or {})
    texto=(simular.RAIZ/'include/Definiciones.h').read_text()
    for k in CLAVES:
        v=(params or {}).get(k,re.search(r'^#define\s+'+k+r'\s+([^\s/]+)',texto,re.M)[1])
        p[k]=v=='true' if v in ('true','false') else float(v.rstrip('f'))
    return p

def ejecutar(n=60):
    base=RAIZ/'resultados/agresivo/lotes'
    actual=simular.compilar({})
    previo=RAIZ/'referencias/Robot_antes_pid.cpp.txt'
    texto=(RAIZ/'referencias/Definiciones_antes_pid.h.txt').read_text()
    params={k:v.strip() for k,v in re.findall(r'^#define\s+(\w+)\s+([^\n/]+)',texto,re.M)}
    anterior=simular.compilar(params,previo)
    tareas=[(k,datos,384 if k=='malla' else n,False) for k,datos in arranques.ENTORNOS.items()]
    tareas += [(k,arranques.ENTORNOS[k],n,True) for k in ['todo','borde','resbaloso','combinado']]
    def trabajo(t):
        k,(nombre,desc,extra),cantidad,antes=t
        ident='antes_'+k if antes else k
        r=arranques.guardar(anterior if antes else actual,ident,('Antes · ' if antes else 'PWM 255 · ')+nombre,desc,k,extra,cantidad,params if antes else {},base,previo if antes else None)
        ruta=base/ident/'meta.json';meta=json.loads(ruta.read_text())
        meta['version']='snapshot-antes-pid' if antes else 'ataque-directo-pwm255-v2'
        if not antes:
            meta['parametros']=parametros_actuales()
            for archivo in ['include/Robot.h','include/ControlDireccion.h']:
                meta['fuentes_sha256'][archivo]=hashlib.sha256((simular.RAIZ/archivo).read_bytes()).hexdigest()
        ruta.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
        return ident,r
    with ThreadPoolExecutor(max_workers=3) as ex: resultados=dict(ex.map(trabajo,tareas))
    (base.parent/'resumen.json').write_text(json.dumps(resultados,ensure_ascii=False,indent=2))
    visualizar.generar(base)
    return resultados

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=60);a=ap.parse_args()
    if a.n<1: ap.error('--n debe ser positivo')
    ejecutar(a.n)
