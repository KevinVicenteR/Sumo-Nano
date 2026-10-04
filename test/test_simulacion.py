"""Regresiones del controlador no bloqueante y a PWM máximo."""
import csv
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'simulacion'))
import simular

class SimulacionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        simular.BUILD.mkdir(parents=True, exist_ok=True)
        cls.binario = simular.compilar({})

    def traza(self, opciones, binario=None, dur='.4', modo='ninguno'):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp)/'tray.csv'
            simular.ejecutar(binario or self.binario, modo, 1,
                ['--inicio','fijo','--x','0','--y','0','--theta','0','--dur',dur,'--rpm','750'] + opciones, ruta)
            with ruta.open() as f:
                return [[float(v) for v in r] for r in csv.reader(f)]

    def test_central_avanza_a_plena_potencia_sin_pausas(self):
        filas = self.traza(['--piso-prueba','negro','--sensor-prueba','escape-frontal-retroceso'])
        activo = [r for r in filas if r[0] >= .02]
        self.assertTrue(activo)
        self.assertTrue(all(r[6:8] == [255,255] and r[9] == 4 for r in activo))

    def test_central_no_gira_por_estado_pid_o_detecciones_adicionales(self):
        for sensor in ['frontal-a-central','lateral-a-frontal','central-y-lateral','central-curva','frontales-dobles']:
            filas = self.traza(['--piso-prueba','negro','--sensor-prueba',sensor])
            activo = [r for r in filas if r[0] >= .12]
            self.assertTrue(activo)
            self.assertTrue(all(r[6:8] == [255,255] and r[9] == 4 for r in activo),sensor)

    def test_frontal_lateral_interrumpe_memoria_del_central(self):
        filas = self.traza(['--piso-prueba','negro','--sensor-prueba','central-a-frontal'])
        self.assertTrue(all(r[9] == 3 for r in filas if .10 < r[0] < .15))
        self.assertTrue(any(r[6:8] == [-255,255] for r in filas if .10 < r[0] < .15))

    def test_ataque_alineado_se_aproxima_al_objetivo_fisico_del_modelo(self):
        inicial = self.traza([],dur='.02',modo='estatico')[0]
        theta = math.degrees(math.atan2(inicial[5],inicial[4]))
        filas = self.traza(['--theta',str(theta),'--piso-prueba','negro'],dur='.4',modo='estatico')
        distancias = [math.hypot(r[1]-r[4],r[2]-r[5]) for r in filas]
        self.assertGreater(distancias[0],.1)
        self.assertLess(min(distancias),.1)
        self.assertTrue(any(r[9] == 4 for r in filas))

    def test_alternancia_no_inventa_doble_frontal_ni_ataque(self):
        filas = simular.ejecutar(self.binario,'ninguno',1,['--inicio','centro','--dur','30','--rpm','750','--sensor-prueba','alternante'])
        self.assertEqual(float(filas[0]['tiempo_ataque_s']),0)

    def test_memoria_evita_cortes_del_central(self):
        filas = self.traza(['--piso-prueba','negro','--sensor-prueba','central-intermitente'])
        self.assertTrue(all(r[6:8] == [255,255] for r in filas if r[0] >= .02))

    def test_lateral_pivota_en_sentido_correcto_a_255(self):
        for sensor, orden in [('lateral-derecho',[255,-255]),('lateral-izquierdo',[-255,255])]:
            filas = self.traza(['--piso-prueba','negro','--sensor-prueba',sensor], dur='.2')
            self.assertTrue(all(r[6:8] == orden for r in filas if .02 < r[0] < .20))
            self.assertTrue(all(abs(v) in (0,255) for r in filas for v in r[6:8]))
            self.assertFalse(any(r[9] in (8,9,10) for r in filas))

    def test_frontal_cancela_orientacion_lateral(self):
        filas = self.traza(['--piso-prueba','negro','--sensor-prueba','lateral-a-frontal'])
        self.assertTrue(any(r[9] == 11 for r in filas if r[0] < .1))
        self.assertTrue(all(r[9] == 4 for r in filas if r[0] > .12))
        self.assertTrue(all(r[6:8] == [255,255] for r in filas if r[0] > .25))

    def test_borde_tiene_prioridad_y_retroceso_acotado(self):
        filas = self.traza(['--piso-prueba','escape','--sensor-prueba','escape-frontal-retroceso'])
        retro = [r for r in filas if r[9] == 5]
        self.assertTrue(retro)
        self.assertLessEqual(retro[-1][0] - retro[0][0], .105)
        self.assertTrue(any(r[9] == 6 for r in filas))
        self.assertFalse(any(r[9] == 4 for r in filas if .02 < r[0] < .20))
        self.assertTrue(any(r[9] == 4 for r in filas if r[0] > .30))
        self.assertLessEqual(max(b[0]-a[0] for a,b in zip(filas,filas[1:])), .0111)

    def test_borde_repetido_completa_giro_aunque_haya_enemigo(self):
        filas = self.traza(['--piso-prueba','escape-repetido','--sensor-prueba','escape-frontal-retroceso'],dur='.7')
        self.assertTrue(any(r[9] == 4 for r in filas if .14 < r[0] < .20))
        self.assertTrue(any(r[9] == 6 for r in filas if .34 < r[0] < .52))
        self.assertFalse(any(r[9] == 4 for r in filas if .21 < r[0] < .49))
        self.assertTrue(any(r[9] == 4 for r in filas if r[0] > .55))
        self.assertFalse(any(r[9] in (8,9,10) for r in filas))

    def test_stop_cancela_escape_sin_esperar_temporizador(self):
        filas = self.traza(['--piso-prueba','escape','--stop-ms','30'])
        self.assertTrue(any(r[9] == 5 for r in filas if r[0] < .03))
        self.assertTrue(all(r[9] == 0 and r[6:8] == [0,0] for r in filas if r[0] >= .04))

    def test_prediccion_anticipa_transicion_con_ambas_polaridades(self):
        for params,adc in [({},[]),({'PISO_BLANCO_LOW':'false','BLANCO':'700'},['--adc-negro','100','--adc-blanco','900'])]:
            b = simular.compilar(params) if params else self.binario
            f = self.traza(['--piso-prueba','rampa','--sensor-prueba','escape-frontal-retroceso']+adc,b)
            self.assertLess(next(r[0] for r in f if r[9] == 5), .062)

    def test_busqueda_no_se_contabiliza_como_ataque(self):
        filas = simular.ejecutar(self.binario,'ninguno',1,['--inicio','centro','--dur','1','--rpm','750'])
        self.assertEqual(float(filas[0]['tiempo_ataque_s']),0)
        self.assertGreater(float(filas[0]['distancia_m']),0)

    def test_malla_cuerpo_dentro_del_dojo(self):
        filas = simular.ejecutar(self.binario,'ninguno',384,['--inicio','malla','--dur','.02','--rpm','750'])
        self.assertEqual(len(filas),384)
        for r in filas:
            x,y = float(r['x_inicial_cm'])/100,float(r['y_inicial_cm'])/100
            th = math.radians(float(r['orientacion_inicial_deg']))
            for dx in [-.05,.05]:
                for dy in [-.05,.05]:
                    self.assertLessEqual(math.hypot(x+dx*math.cos(th)-dy*math.sin(th),y+dx*math.sin(th)+dy*math.cos(th)),.35002)

    def test_pid_limite_reloj_y_recuperacion_de_saturacion(self):
        fuente = '''#include "ControlDireccion.h"
#include <cassert>
int main() {
 ControlDireccion c;
 assert(c.actualizar(2,.35,0)>0);
 int anterior=c.actualizar(2,.35,0);
 assert(c.actualizar(-2,.35,1)==anterior);
 for(unsigned long t=4;t<10000;t+=4) assert(c.actualizar(20,.35,t)<=510);
 int salida=0;
 for(unsigned long t=10000;t<12000;t+=4) salida=c.actualizar(0,.05,t);
 assert(abs(salida)<=16);
 c.reiniciar(); assert(c.actualizar(-2,.35,12000)<0);
 c.reiniciar(); c.actualizar(1,.12,0xfffffff0UL);
 assert(c.actualizar(0,.05,4)<200);
}'''
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'pid.cpp').write_text(fuente)
            subprocess.run(['c++','-std=c++17', '-I'+str(simular.RAIZ/'include'),'-I'+str(simular.RAIZ/'simulacion/support'),str(p/'pid.cpp'),'-o',str(p/'pid')],check=True)
            subprocess.run([str(p/'pid')],check=True)

if __name__ == '__main__': unittest.main()
