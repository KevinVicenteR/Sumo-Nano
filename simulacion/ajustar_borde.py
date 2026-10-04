#!/usr/bin/env python3
"""Compara tiempos de escape y permanencia junto al borde, con PWM 255."""
import sys,json,itertools,statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
RAIZ=Path(__file__).resolve().parent
sys.path.insert(0,str(RAIZ))
import simular
actual={'RETROCESO_MIN_MS':'100','TIEMPO_RETROCESO_MS':'200','PAUSA_ESCAPE_MS':'100','TIEMPO_GIRO_BORDE_FRENTE_MS':'110','TIEMPO_GIRO_BORDE_LADO_MS':'70'}
ps=[actual]+[{'RETROCESO_MIN_MS':str(r),'TIEMPO_RETROCESO_MS':'240','PAUSA_ESCAPE_MS':str(p),'TIEMPO_GIRO_BORDE_FRENTE_MS':'150','TIEMPO_GIRO_BORDE_LADO_MS':str(g)} for r,p,g in itertools.product([120,150],[60,100],[110,150])]
def run(p):
 b=simular.compilar(p);r={}
 for env,extra in [('todo',['--inicio','todo']),('borde',['--inicio','borde'])]:
  r[env]={}
  for m in simular.MODOS:
   rows=simular.ejecutar(b,m,40,['--dur','30','--rpm','750','--masa','.3']+extra)
   r[env][m]={'caidas':sum(x['cayo']=='1' for x in rows),'ataques':sum(float(x['tiempo_ataque_s'])>0 for x in rows),'borde_s':statistics.mean(float(x['tiempo_borde_s']) for x in rows),'racha_s':statistics.mean(float(x['racha_borde_max_s']) for x in rows),'atascos_5s':sum(float(x['racha_borde_max_s'])>5 for x in rows)}
 return {'parametros':p,'resultados':r}
with ThreadPoolExecutor(max_workers=5) as ex:rs=list(ex.map(run,ps))
rs.sort(key=lambda a:(sum(v['caidas'] for e in a['resultados'].values() for v in e.values()),sum(v['atascos_5s'] for e in a['resultados'].values() for v in e.values()),sum(v['borde_s'] for e in a['resultados'].values() for v in e.values())))
(RAIZ/'resultados'/'borde-tiempos.json').write_text(json.dumps(rs,indent=2))
for a in rs:print(a)
