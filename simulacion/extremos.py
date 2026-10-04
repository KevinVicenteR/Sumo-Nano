#!/usr/bin/env python3
"""Pruebas reproducibles de sensibilidad; no suponen medidas del hardware real."""
import csv
from pathlib import Path
import simular

CASOS = {
    'nominal': [],
    'enemigo_rapido': ['--vel-enemigo','0.6'],
    'lecturas_ruidosas': ['--ruido-piso','100'],
    'control_lento': ['--loop-us','8000'],
    'bateria_extrema': ['--bateria','1.6','--friccion-caja','0.05','--friccion-giro','0.2'],
    'piso_resbaloso': ['--mu','0.3','--bateria','1.3','--friccion-caja','0.08'],
    'inicio_borde': ['--inicio-r','0.27'],
    'sensor_corto': ['--rango','0.12'],
    'ruedas_grandes': ['--diam','0.05','--bateria','1.3'],
    'pared_exterior': ['--pared','0.5','--bateria','1.3'],
    'adc_invertido': ['--adc-negro','150','--adc-blanco','850','--adc-fuera','150'],
    'combinado': ['--mu','0.3','--diam','0.05','--bateria','1.6','--friccion-caja','0.05','--inicio-r','0.27'],
}
if __name__ == '__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=100);a=ap.parse_args()
    simular.BUILD.mkdir(parents=True,exist_ok=True)
    b=simular.compilar({})
    for caso, opciones in CASOS.items():
        carpeta=Path(__file__).parent/'resultados'/'extremos'/caso;carpeta.mkdir(parents=True,exist_ok=True)
        resumen=[]
        for modo in simular.MODOS:
            filas=simular.ejecutar(b,modo,a.n,['--rpm','750','--masa','0.3','--dur','30',*opciones],carpeta/f'tray_{modo}.csv')
            with (carpeta/f'resultados_{modo}.csv').open('w') as f:
                w=csv.DictWriter(f,fieldnames=filas[0].keys());w.writeheader();w.writerows(filas)
            caidas=[r for r in filas if r['cayo']=='1']
            if caidas:
                simular.ejecutar(b,modo,1,['--rpm','750','--masa','0.3','--dur','30',*opciones,'--semilla',caidas[0]['semilla']],carpeta/f'tray_fallo_{modo}.csv')
            resumen.append(simular.resumir(modo,filas))
        print('\nENTORNO:',caso, ' '.join(opciones),flush=True);simular.imprimir(resumen)
