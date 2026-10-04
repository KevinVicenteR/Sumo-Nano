#!/usr/bin/env python3
"""Compara movimientos y valida arranques en toda el área y en una malla de 384 poses."""
import argparse
import csv
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import simular

RAIZ=Path(__file__).resolve().parent
BASE=['--rpm','750','--masa','0.3','--dur','30']
ENTORNOS={
 'objetos': ('Varios objetos alrededor del dojo','Objetos exteriores a 50 cm del centro; pueden activar varios sensores a la vez.', ['--inicio','borde','--pared','0.5']),
 'alternante': ('Lecturas alternantes · prueba sintética','Frontal izquierdo/derecho alterna cada 10 ms. Estrés de oscilación, no un enemigo físico.', ['--inicio','todo','--sensor-prueba','alternante']),
 'laterales': ('Dos laterales activos · prueba sintética','Ambos laterales detectan continuamente sin frontal central. Estrés de bloqueo.', ['--inicio','todo','--sensor-prueba','laterales']),
 'todo': ('Todo el dojo · arranques aleatorios','Todo el cuerpo dentro del círculo; orientación aleatoria. También se permiten sensores sobre blanco.', ['--inicio','todo']),
 'malla': ('Malla · 384 posiciones y orientaciones','4 radios × 12 sectores × 8 orientaciones. La última corona queda a 1–2 mm del límite donde cabe el cuerpo.', ['--inicio','malla']),
 'borde': ('Arranques junto al borde','Centro entre 26 cm y el máximo admisible; frente hacia cualquier dirección.', ['--inicio','borde']),
 'sensor_corto': ('Alcance de 12 cm · junto al borde','Prueba de cobertura de búsqueda con alcance reducido.', ['--inicio','borde','--rango','0.12']),
 'bateria_alta': ('Batería +30 % · junto al borde','Más velocidad, reductora suave y arranque junto al borde.', ['--inicio','borde','--bateria','1.3','--friccion-caja','0.08','--friccion-giro','0.3']),
 'resbaloso': ('Piso resbaloso · junto al borde','Adherencia μ=0.3, batería +30 % y reductora suave.', ['--inicio','borde','--mu','0.3','--bateria','1.3','--friccion-caja','0.08']),
 'combinado': ('Extremos combinados','μ=0.3, ruedas de 5 cm, batería +60 %, reductora suave y arranque junto al borde.', ['--inicio','borde','--mu','0.3','--diam','0.05','--bateria','1.6','--friccion-caja','0.05']),
 'enemigo_rapido': ('Enemigo rápido · todo el dojo','Enemigo a 0.6 m/s y arranques en toda el área admisible.', ['--inicio','todo','--vel-enemigo','0.6']),
 'control_lento': ('Control lento · junto al borde','8 ms adicionales por ciclo de control.', ['--inicio','borde','--loop-us','8000']),
}
ANTERIOR={'PATRON_BUSQUEDA':'0','VELOCIDAD_BUSQUEDA':'130','Velocidad_maxima':'130','Velocidad_estandar':'180','TIEMPO_RETROCESO_MS':'90','TIEMPO_BUSQUEDA_AVANCE_MS':'70'}

def parametros(params):
    import re
    texto=(simular.RAIZ/'include'/'Definiciones.h').read_text()
    return {k:int(params.get(k,re.search(r'^#define\s+'+k+r'\s+(\d+)',texto,re.M)[1])) for k in ['PATRON_BUSQUEDA','Velocidad_maxima_Ataque','VELOCIDAD_BUSQUEDA','TIEMPO_RETROCESO_MS','Velocidad_estandar','Velocidad_maxima','TIEMPO_BUSQUEDA_AVANCE_MS','TIEMPO_BUSQUEDA_GIRO_MS','ATAQUE_IMPULSO_MS','ATAQUE_PAUSA_MS','PAUSA_ESCAPE_MS','RETROCESO_MIN_MS','GIRO_MAX_SEGUIMIENTO_MS','DESATASCO_AVANCE_MS','VELOCIDAD_CURVA_INTERIOR','VELOCIDAD_ATAQUE_CURVA_INTERIOR','VELOCIDAD_GIRO_ESCAPE','TIEMPO_GIRO_BORDE_FRENTE_MS','TIEMPO_GIRO_BORDE_LADO_MS','PAUSA_RETROCESO_MS','PAUSA_GIRO_MS']}

def guardar(b,identificador,nombre,descripcion,env,extra,n,params, carpeta_base=None,fuente_robot=None):
    carpeta=(carpeta_base or RAIZ/'resultados'/'arranque'/'lotes')/identificador
    carpeta.mkdir(parents=True,exist_ok=True)
    meta={'nombre':nombre,'descripcion':descripcion,'entorno':env,'opciones':extra,'parametros':parametros(params),'version':'reloj-integrado-v2'}
    if carpeta_base:
        anterior=identificador.startswith('antes_')
        meta['version']='anterior-lento-snapshot' if anterior else 'ataque-continuo-curva-v7'
        meta['freno_activo']=False if anterior else '#define FRENO_ACTIVO true' in (simular.RAIZ/'include'/'Definiciones.h').read_text()
        meta['fuentes_sha256']={} if anterior else {str(p):hashlib.sha256((simular.RAIZ/p).read_bytes()).hexdigest() for p in map(Path,['src/Robot.cpp','include/Definiciones.h','src/Motor.cpp','simulacion/sim.cpp'])}
        if anterior:meta['robot_snapshot']='../../Robot_anterior.cpp.txt'
        if fuente_robot:
            meta['robot_snapshot']=str(fuente_robot.relative_to(simular.RAIZ))
            meta['fuentes_sha256']['src/Robot.cpp']=hashlib.sha256(fuente_robot.read_bytes()).hexdigest()
    (carpeta/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    resumen=[]
    for modo in simular.MODOS:
        filas=simular.ejecutar(b,modo,n,BASE+extra,carpeta/f'tray_{modo}.csv')
        with (carpeta/f'resultados_{modo}.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=filas[0].keys());w.writeheader();w.writerows(filas)
        fallos=[r for r in filas if r['cayo']=='1']
        semillas={1:'primera'}
        if fallos:semillas[int(fallos[0]['semilla'])]='fallo'
        for radio,label in [(0.,'centro'),(15.,'intermedio'),(28.,'borde')]:
            fila=min(filas,key=lambda r:abs((float(r['x_inicial_cm'])**2+float(r['y_inicial_cm'])**2)**.5-radio))
            semillas.setdefault(int(fila['semilla']),label)
        muestras=[]
        for seed,label in semillas.items():
            ruta=carpeta/f'tray_{modo}_{seed}.csv'
            simular.ejecutar(b,modo,1,BASE+extra+['--semilla',str(seed)],ruta)
            muestras.append({'semilla':seed,'archivo':ruta.name,'etiqueta':label})
        (carpeta/f'ejemplos_{modo}.json').write_text(json.dumps(muestras))
        resumen.append(simular.resumir(modo,filas))
    print(nombre,[(r['modo'],r['caidas'],r['ataques'],r['n']) for r in resumen],flush=True)
    return resumen

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=300);a=ap.parse_args()
    if a.n<1:ap.error('--n debe ser positivo')
    simular.BUILD.mkdir(parents=True,exist_ok=True)
    b=simular.compilar({})
    trabajos=[]
    for key,(nombre,descripcion,extra) in ENTORNOS.items():
        n=384 if key=='malla' else a.n
        trabajos.append((b,key,nombre,descripcion,key,extra,n,{}))
    # Comparación pareja: mismos motores, sensores, arranques y semillas.
    for key,pattern in [('giro','0'),('zigzag','1'),('arcos','2'),('anterior',None)]:
        params=ANTERIOR if pattern is None else {'PATRON_BUSQUEDA':pattern}
        binario=simular.compilar(params)
        trabajos.append((binario,'movimiento_'+key,'Movimiento · '+key,'Comparación con arranques junto al borde y sensores de 12 cm.','sensor_corto',ENTORNOS['sensor_corto'][2],a.n,params))
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(lambda t:guardar(*t),trabajos))
