#!/usr/bin/env python3
"""Evalúa velocidades y escape sin alterar física ni colocaciones."""
import argparse,csv,json,hashlib,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import simular
from arranques import ENTORNOS
VELOCIDADES=['Velocidad_estandar','VELOCIDAD_GIRO_ESCAPE','VELOCIDAD_BUSQUEDA','Velocidad_maxima','Velocidad_maxima_Ataque','Velocidad_movimiento_seguir','VELOCIDAD_DESATASCO','VELOCIDAD_GIRO_LATERAL','VELOCIDAD_ORIENTACION']
def params(v):
    return {**{k:str(v) for k in VELOCIDADES},'VELOCIDAD_CURVA_INTERIOR':str(round(89*v/190)),'VELOCIDAD_ATAQUE_CURVA_INTERIOR':str(round(104*v/190))}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--n',type=int,default=30);ap.add_argument('--semilla',type=int,default=501);ap.add_argument('--escape-corto',action='store_true');ap.add_argument('--pivote',action='store_true');ap.add_argument('--freno',type=int);ap.add_argument('--exigir-cero',action='store_true');ap.add_argument('--publicar-visor',action='store_true');ap.add_argument('--giro',type=int);ap.add_argument('--velocidades',nargs='+',type=int,default=[80,100,120]);ap.add_argument('--entornos',nargs='+',choices=ENTORNOS,default=['todo','borde','bateria_alta','resbaloso','combinado']);ap.add_argument('--salida',type=Path,default=Path(__file__).parent/'resultados/seguridad/exploracion');a=ap.parse_args()
    if a.n<1 or any(v<1 or v>255 for v in a.velocidades):ap.error('n y PWM inválidos')
    if a.giro is not None and not 1<=a.giro<=255:ap.error('--giro entre 1 y 255')
    if a.freno is not None and not 0<=a.freno<=2000:ap.error('--freno entre 0 y 2000 ms')
    if a.publicar_visor and len(a.velocidades)!=1:ap.error('--publicar-visor requiere una sola velocidad')
    a.salida.mkdir(parents=True,exist_ok=True)
    configuraciones={v:params(v) for v in a.velocidades}
    if a.giro:
        for ps in configuraciones.values():ps.update({k:str(a.giro) for k in ['VELOCIDAD_ORIENTACION','VELOCIDAD_GIRO_ESCAPE','VELOCIDAD_GIRO_LATERAL']})
    if a.escape_corto:
        for ps in configuraciones.values():ps.update({'RETROCESO_MIN_MS':'20','TIEMPO_RETROCESO_MS':'60','TIEMPO_GIRO_BORDE_FRENTE_MS':'450','TIEMPO_GIRO_BORDE_LADO_MS':'450'})
    if a.pivote:
        for ps in configuraciones.values():ps.update({'SEGUIMIENTO_PIVOTE':'true','PATRON_BUSQUEDA':'0'})
    if a.freno is not None:
        for ps in configuraciones.values():ps.update({k:str(a.freno) for k in ['FRENO_ORIENTACION_MS','FRENO_LATERAL_MS','PAUSA_ESCAPE_MS']})
    fuentes=simular.FUENTES+sorted((simular.RAIZ/'include').glob('*.h'))+[simular.RAIZ/'simulacion/support/Arduino.h']
    (a.salida/'meta.json').write_text(json.dumps({'n':a.n,'semilla':a.semilla,'duracion_s':30,'parametros':configuraciones,'entornos':{e:ENTORNOS[e][2] for e in a.entornos},'fuentes_sha256':{str(p.relative_to(simular.RAIZ)):hashlib.sha256(p.read_bytes()).hexdigest() for p in fuentes}},indent=2))
    bs={v:simular.compilar(configuraciones[v]) for v in a.velocidades}
    def correr(t):
        v,e,m=t;p=a.salida/f'pwm{v}_{e}_{m}.csv'
        fs=simular.ejecutar(bs[v],m,384 if e=='malla' else a.n,['--rpm','750','--dur','30','--semilla',str(a.semilla)]+ENTORNOS[e][2])
        with p.open('w') as f:
            w=csv.DictWriter(f,fieldnames=fs[0].keys());w.writeheader();w.writerows(fs)
        r=simular.resumir(m,fs);print(v,e,m,r['caidas'],r['ataques'],flush=True)
        return {'pwm':v,'entorno':e,'n':len(fs),**r}
    with ThreadPoolExecutor(max_workers=3) as pool:rs=list(pool.map(correr,[(v,e,m) for v in bs for e in a.entornos for m in simular.MODOS]))
    (a.salida/'resumen.json').write_text(json.dumps(rs,indent=2))
    for v in bs:
        fs=[r for r in rs if r['pwm']==v];print(v,'TOTAL',sum(r['caidas'] for r in fs),'/',sum(r['n'] for r in fs),flush=True)
    if a.exigir_cero and any(r['caidas'] for r in rs):raise SystemExit('La validación encontró caídas')
    if a.publicar_visor:
        import arranques,visualizar
        v=a.velocidades[0];ps=configuraciones[v];lotes=Path(__file__).parent/'resultados/seguridad/lotes'
        for e in a.entornos:
            carpeta=lotes/e;carpeta.mkdir(parents=True,exist_ok=True)
            nombre,desc,extra=ENTORNOS[e]
            (carpeta/'meta.json').write_text(json.dumps({'nombre':'Seguro · '+nombre,'descripcion':desc,'entorno':e,'opciones':extra,'parametros':{**arranques.parametros(ps),'SEGUIMIENTO_PIVOTE':ps.get('SEGUIMIENTO_PIVOTE','true')=='true'},'version':f'escape-corto-pwm{v}'},ensure_ascii=False,indent=2))
            for m in simular.MODOS:
                origen=a.salida/f'pwm{v}_{e}_{m}.csv';shutil.copyfile(origen,carpeta/f'resultados_{m}.csv')
                with origen.open() as f:seed=int(next(csv.DictReader(f))['semilla'])
                ruta=carpeta/f'tray_{m}_{seed}.csv'
                simular.ejecutar(bs[v],m,1,['--rpm','750','--dur','30','--semilla',str(seed)]+extra,ruta)
                (carpeta/f'ejemplos_{m}.json').write_text(json.dumps([{'semilla':seed,'archivo':ruta.name,'etiqueta':'primera'}]))
        visualizar.generar(lotes)
if __name__=='__main__':main()
