#!/usr/bin/env python3
"""Visor local y API para simular exactamente el arranque elegido con firmware C++."""
import csv
import io
import json
import math
import subprocess
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import simular
from arranques import ENTORNOS as PRUEBAS

RAIZ = Path(__file__).resolve().parent
BASE = ['--rpm','750','--masa','0.3','--dur','30']
BINARIOS = {}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(RAIZ/'resultados'),**kwargs)

    def responder(self,codigo,contenido):
        datos=json.dumps(contenido,allow_nan=False).encode()
        self.send_response(codigo);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(datos)));self.end_headers();self.wfile.write(datos)

    def do_POST(self):
        if self.path!='/api/simular':self.responder(404,{'error':'Ruta desconocida'});return
        # API exclusivamente local; no aceptar solicitudes desde otros sitios.
        if self.headers.get('Origin') not in (None,'http://127.0.0.1:8765','http://localhost:8765'):
            self.responder(403,{'error':'Origen no permitido'});return
        try:
            longitud=int(self.headers.get('Content-Length',0))
            if not 0<longitud<4096:raise ValueError('Solicitud demasiado grande')
            a=json.loads(self.rfile.read(longitud));x=float(a['x'])/100;y=float(a['y'])/100;theta=float(a['theta'])
            if not all(math.isfinite(v) for v in [x,y,theta]) or abs(x)>.35 or abs(y)>.35 or abs(theta)>360:
                raise ValueError('Coordenadas o ángulo fuera de rango')
            modo=a.get('modo','ninguno');entorno=a.get('entorno','todo');patron=a.get('patron','actual')
            if modo not in simular.MODOS or entorno not in ENTORNOS or patron not in BINARIOS:
                raise ValueError('Opción desconocida')
            semilla=int(a.get('semilla',1))
            if not 1<=semilla<=100000:raise ValueError('La semilla debe estar entre 1 y 100000')
            with tempfile.TemporaryDirectory(prefix='sumo-') as temp:
                ruta=Path(temp)/'tray.csv'
                filas=simular.ejecutar(BINARIOS[patron],modo,1,BASE+ENTORNOS[entorno]+['--inicio','fijo','--x',str(x),'--y',str(y),'--theta',str(theta),'--semilla',str(semilla)],ruta)
                f=filas[0];rows=[[float(v) for v in r] for r in csv.reader(ruta.open())]
                muestras=rows[::5]
                if muestras[-1]!=rows[-1]:muestras.append(rows[-1])
                self.responder(200,{'stats':{'n':1,'caidas':int(f['cayo']),'ataques':int(float(f['tiempo_ataque_s'])>0),'ataque_s':float(f['tiempo_ataque_s']),'frontal':float(f['frac_frontal']),'margen':float(f['margen_min_cm']),'saliente':float(f['max_salida_cuerpo_cm']),'borde':float(f['tiempo_borde_s']),'racha':float(f['racha_borde_max_s']),'velocidad':float(f.get('velocidad_max_m_s',0))},'trazas':{'manual':{'nombre':f'Arranque elegido · semilla {semilla}','semilla':semilla,'cayo':int(f['cayo']),'filas':muestras}},'parametros':PARAMETROS[patron]})
        except (ValueError,KeyError,json.JSONDecodeError) as e:self.responder(400,{'error':str(e)})
        except subprocess.CalledProcessError as e:
            self.responder(400,{'error':e.stderr.strip() if e.stderr else 'La posición inicial no permite colocar todo el robot dentro del dojo.'})
        except Exception as e:self.responder(500,{'error':'No se pudo simular: '+str(e)})

# El arranque manual lo determina la API; quitar solamente opciones de distribución.
ENTORNOS={key:datos[2] for key,datos in PRUEBAS.items()}
PARAMETROS={}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--puerto',type=int,default=8765);a=ap.parse_args()
    if a.puerto!=8765:ap.error('El visor y la política de origen usan el puerto 8765')
    simular.BUILD.mkdir(parents=True,exist_ok=True)
    for nombre,params in [('actual',{}),('giro',{'PATRON_BUSQUEDA':'0'}),('zigzag',{'PATRON_BUSQUEDA':'1'}),('arcos',{'PATRON_BUSQUEDA':'2'})]:
        BINARIOS[nombre]=simular.compilar(params)
        import re
        texto=(simular.RAIZ/'include'/'Definiciones.h').read_text()
        PARAMETROS[nombre]={key:int(params.get(key,re.search(r'^#define\s+'+key+r'\s+(\d+)',texto,re.M)[1])) for key in ['Velocidad_maxima_Ataque','VELOCIDAD_BUSQUEDA','TIEMPO_RETROCESO_MS','Velocidad_estandar','ATAQUE_IMPULSO_MS','ATAQUE_PAUSA_MS','PAUSA_ESCAPE_MS','RETROCESO_MIN_MS','TIEMPO_GIRO_BORDE_FRENTE_MS','TIEMPO_GIRO_BORDE_LADO_MS','PAUSA_RETROCESO_MS','PAUSA_GIRO_MS','VELOCIDAD_CURVA_INTERIOR','VELOCIDAD_ATAQUE_CURVA_INTERIOR']}
    print(f'Visor: http://127.0.0.1:{a.puerto}/visor.html',flush=True)
    ThreadingHTTPServer(('127.0.0.1',a.puerto),Handler).serve_forever()
