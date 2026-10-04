#!/usr/bin/env python3
"""Poses aproximadas de la imagen del usuario; no son medidas reglamentarias."""
import json,math
from pathlib import Path
import simular
POSES={1:(-.055,-.055,225,.055,.055,45),2:(-.055,.055,135,.055,-.055,-45),3:(-.26,0,0,.26,0,180)}
def ejecutar(n=30):
 res=[]
 base=Path(__file__).resolve().parent/'resultados/competencia';base.mkdir(parents=True,exist_ok=True)
 for ronda,p in POSES.items():
  b=simular.compilar({"ROUND_COMPETENCIA":str(ronda)})
  for espejo in (False,True):
   x,y,t,ex,ey,et=p
   if espejo:x,y,t,ex,ey,et=ex,ey,et,x,y,t
   for modo in ('estatico','errante'):
    extra=['--rpm','750','--dur','30','--inicio','fijo','--x',str(x),'--y',str(y),'--theta',str(t),'--rival-x',str(ex),'--rival-y',str(ey),'--rival-theta',str(et)]
    f=simular.ejecutar(b,modo,n,extra,base/f'round{ronda}_{espejo}_{modo}.csv')
    r=simular.resumir(modo,f);r.update(round=ronda,espejo=espejo,opciones=extra)
    res.append(r);print(ronda,espejo,modo,'caidas',r['caidas'],'ataques',r['ataques'],'frontal_s',r['t_ver_mediana'],flush=True)
 (base/'resumen.json').write_text(json.dumps(res,indent=2,ensure_ascii=False));return res
if __name__=='__main__':ejecutar()
