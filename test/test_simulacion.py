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
        cls.binario = simular.compilar({"ROUND_COMPETENCIA":"0"})

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
        for sensor in ['frontal-a-central','lateral-a-frontal','central-y-lateral','frontales-dobles']:
            filas = self.traza(['--piso-prueba','negro','--sensor-prueba',sensor])
            activo = [r for r in filas if r[0] >= .12]
            self.assertTrue(activo)
            self.assertTrue(all(r[6:8] == [255,255] and r[9] == 4 for r in activo),sensor)

    def test_frontal_lateral_interrumpe_memoria_del_central(self):
        filas = self.traza(['--piso-prueba','negro','--sensor-prueba','central-a-frontal'])
        self.assertTrue(all(r[9] == 3 for r in filas if .10 < r[0] < .19))
        self.assertTrue(any(r[6:8] == [-255,255] for r in filas if .10 < r[0] < .19))

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

    def test_seguimiento_conserva_lado_al_centrar_y_perder_enemigo(self):
        filas=self.traza(['--piso-prueba','negro','--sensor-prueba','derecha-central-perdida','--rpm','100'],dur='1.6')
        self.assertTrue(all(r[6:8]==[255,255] for r in filas if .12<r[0]<.26))
        self.assertTrue(all(r[9]==3 for r in filas if .80<r[0]<1.30))
        self.assertTrue(any(r[6:8]==[255,-255] for r in filas if .80<r[0]<1.30))
        self.assertFalse(any(r[6:8]==[-255,255] for r in filas if .80<r[0]<1.30))
        self.assertTrue(any(r[9] in (1,2) for r in filas if r[0]>1.4))

    def test_lateral_persistente_no_interrumpe_seguimiento_para_avanzar(self):
        filas=self.traza(['--piso-prueba','negro','--sensor-prueba','lateral-derecho'],dur='.7')
        self.assertTrue(all(r[9]==11 and r[6:8]==[140,-140] for r in filas if r[0]>.02))

    def test_central_corrige_cuando_frontal_descentrado_tambien_detecta(self):
        filas=self.traza(['--piso-prueba','negro','--sensor-prueba','central-curva','--tray-ms','1'])
        self.assertTrue(any(r[9]==3 and r[6:8]==[255,-255] for r in filas if .06<r[0]<.12))
        self.assertTrue(all(r[9]==4 and r[6:8]==[255,255] for r in filas if .13<r[0]<.2))

    def test_sigue_cambios_de_lado_y_recupera_objetivo_tras_hueco(self):
        filas=self.traza(['--piso-prueba','negro','--sensor-prueba','seguimiento-movil'],dur='.6')
        self.assertTrue(any(r[6:8]==[255,-255] for r in filas if .09<r[0]<.14))
        self.assertTrue(any(r[6:8]==[-255,255] for r in filas if .21<r[0]<.38))
        self.assertTrue(all(r[9] not in (1,2) for r in filas if .28<r[0]<.37))
        self.assertTrue(all(r[9]==4 and r[6:8]==[255,255] for r in filas if r[0]>.48))

    def test_calibracion_de_giro_corrige_modelo_fisico_sin_invertir_avance(self):
        anterior=simular.compilar({'INVERTIR_SENTIDO_GIRO':'false','ROUND_COMPETENCIA':'0'})
        extra=['--piso-prueba','negro','--sensor-prueba','lateral-derecho']
        mal=self.traza(extra,anterior,dur='.1')
        bien=self.traza(extra,dur='.1')
        self.assertTrue(all(r[6:8]==[-140,140] for r in mal if r[0]>.02))
        self.assertTrue(all(r[6:8]==[140,-140] for r in bien if r[0]>.02))
        for b in [anterior,self.binario]:
            frente=self.traza(['--piso-prueba','negro','--sensor-prueba','escape-frontal-retroceso'],b,dur='.1')
            self.assertTrue(all(r[6:8]==[255,255] for r in frente if r[0]>.02))

    def test_memoria_evita_cortes_del_central(self):
        filas = self.traza(['--piso-prueba','negro','--sensor-prueba','central-intermitente'])
        self.assertTrue(all(r[6:8] == [255,255] for r in filas if r[0] >= .02))

    def test_lateral_pivota_en_sentido_correcto_a_140(self):
        for sensor, orden in [('lateral-derecho',[140,-140]),('lateral-izquierdo',[-140,140])]:
            filas = self.traza(['--piso-prueba','negro','--sensor-prueba',sensor], dur='.2')
            self.assertTrue(all(r[6:8] == orden for r in filas if .02 < r[0] < .20))
            self.assertTrue(all(abs(v) in (0,140) for r in filas for v in r[6:8]))
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
        self.assertGreaterEqual(retro[-1][0] - retro[0][0], .19)
        self.assertLessEqual(retro[-1][0] - retro[0][0], .285)
        self.assertTrue(any(r[9] == 4 for r in filas))
        self.assertFalse(any(r[9] == 4 for r in filas if .02 < r[0] < .20))
        self.assertTrue(any(r[9] == 4 for r in filas if r[0] > .30))
        self.assertLessEqual(max(b[0]-a[0] for a,b in zip(filas,filas[1:])), .0111)

    def test_frontal_interrumpe_escape_repetido_al_confirmar_negro(self):
        filas = self.traza(['--piso-prueba','escape-repetido-largo','--sensor-prueba','escape-frontal-retroceso','--rpm','100'],dur='1.2')
        self.assertTrue(any(r[9] == 4 for r in filas if .30 < r[0] < .38))
        self.assertTrue(any(r[9] == 5 for r in filas if .45 < r[0] < .52))
        self.assertFalse(any(r[9] == 4 for r in filas if .41 < r[0] < .52))
        self.assertTrue(any(r[9] == 4 for r in filas if r[0] > .55))
        self.assertFalse(any(r[9] in (8,9,10) for r in filas))

    def test_tres_frontales_cancelan_giro_y_atacan_recto(self):
        filas=self.traza(['--piso-prueba','negro','--sensor-prueba','lateral-a-tres-frontales','--tray-ms','1'])
        self.assertTrue(any(r[9]==11 for r in filas if r[0]<.1))
        self.assertTrue(all(r[9]==4 and r[6:8]==[255,255] for r in filas if r[0]>.102))

    def test_borde_persistente_no_queda_pivotando_y_retoma_tres_frontales(self):
        filas=self.traza(['--piso-prueba','borde-persistente','--sensor-prueba','lateral-a-tres-frontales','--rpm','100'],dur='1.5')
        self.assertTrue(any(r[9]==5 for r in filas if .83<r[0]<.95))
        self.assertTrue(any(r[9]==6 for r in filas if .65<r[0]<.80))
        self.assertFalse(any(r[9]==4 for r in filas if r[0]<.98))
        self.assertTrue(all(r[9]==4 and r[6:8]==[255,255] for r in filas if r[0]>1.32))
        self.assertTrue(all(abs(v)<255 for r in filas if r[0]>.02 and r[9] in (5,6) for v in r[6:8]))

    def test_busqueda_barre_ambos_lados_y_alterna_avance(self):
        filas=self.traza(['--piso-prueba','negro','--rpm','30','--tray-ms','1'],dur='2.6')
        self.assertTrue(all(v>=0 for r in filas for v in r[6:8]))
        self.assertTrue(any(r[6:8]==[130,60] for r in filas if .02<r[0]<.2))
        self.assertTrue(all(r[6:8]==[130,130] for r in filas if .31<r[0]<.34))
        self.assertTrue(any(r[6:8]==[60,130] for r in filas if 2.12<r[0]<2.35))

    def test_lateral_alineado_no_vuelve_al_pivote_tras_perder_central(self):
        f=self.traza(['--piso-prueba','negro','--sensor-prueba','lateral-central-perdida','--rpm','100'],dur='.65')
        self.assertTrue(all(r[9]==4 and r[6:8]==[255,255] for r in f if .12<r[0]<.33))
        self.assertFalse(any(r[9]==11 for r in f if r[0]>.35))

    def test_perdida_lateral_limita_pivote_y_continua_aproximacion(self):
        f=self.traza(['--piso-prueba','negro','--sensor-prueba','lateral-derecho-breve','--rpm','100'],dur='.65')
        self.assertTrue(all(r[9]==11 for r in f if .12<r[0]<.33))
        self.assertTrue(all(r[9]==3 for r in f if r[0]>.36))
        self.assertTrue(any(r[6:8]==[255,255] for r in f if r[0]>.36))

    def test_sostiene_empuje_durante_perdida_frontal_de_400ms(self):
        f=self.traza(['--piso-prueba','negro','--sensor-prueba','empuje-senal-perdida','--rpm','100'],dur='.8')
        self.assertTrue(all(r[9]==4 and r[6:8]==[255,255] for r in f if r[0]>.02))

    def test_lateral_transitorio_no_corta_empuje_reciente(self):
        f=self.traza(['--piso-prueba','negro','--sensor-prueba','empuje-lateral-transitorio','--rpm','100'],dur='.8')
        self.assertTrue(all(r[9]==4 and r[6:8]==[255,255] for r in f if r[0]>.02))

    def test_arranque_competencia_sin_espera_y_rival_fijo(self):
        f=self.traza(['--x','-.26','--theta','0','--rival-x','.26','--rival-y','0','--rival-theta','180'],dur='.08',modo='estatico')
        self.assertAlmostEqual(f[0][4],.26,places=3)
        self.assertAlmostEqual(f[0][5],0,places=3)
        self.assertTrue(all(r[9]!=0 for r in f if r[0]>.01))
        self.assertTrue(any(r[6]>0 and r[7]>0 for r in f if r[0]>.01))

    def test_aperturas_por_round_y_corte_por_enemigo(self):
        for ronda,orden in [(1,[140,0]),(2,[0,140]),(3,[180,180])]:
            b=simular.compilar({'ROUND_COMPETENCIA':str(ronda)})
            f=self.traza(['--piso-prueba','negro','--rpm','30'],b,dur='.12')
            self.assertTrue(all(r[6:8]==orden for r in f if r[0]>.01),ronda)
            f=self.traza(['--piso-prueba','negro','--rpm','30'],b,dur='1.1')
            fin=.32 if ronda==3 else .92
            self.assertTrue(all(r[9] in (1,2) and r[6]>=0 and r[7]>=0 for r in f if r[0]>fin),ronda)
            f=self.traza(['--piso-prueba','negro','--sensor-prueba','escape-frontal-retroceso'],b,dur='.8')
            corte=.01 if ronda==3 else .71
            if ronda!=3: self.assertTrue(all(r[6:8]==orden for r in f if .01<r[0]<.69),ronda)
            self.assertTrue(all(r[9]==4 and r[6:8]==[255,255] for r in f if r[0]>corte),ronda)
            f=self.traza(['--piso-prueba','escape','--stop-ms','30'],b,dur='.12')
            self.assertTrue(any(r[9]==5 for r in f if r[0]<.03),ronda)
            self.assertTrue(all(r[9]==0 for r in f if r[0]>.04),ronda)

    def test_variaciones_de_negro_no_interrumpen_ataque(self):
        f=self.traza(['--piso-prueba','negro-con-ruido','--sensor-prueba','escape-frontal-retroceso','--rpm','100'],dur='.8')
        self.assertTrue(all(r[9]==4 and r[6:8]==[255,255] for r in f if r[0]>.02))

    def test_stop_cancela_escape_sin_esperar_temporizador(self):
        filas = self.traza(['--piso-prueba','escape','--stop-ms','30'])
        self.assertTrue(any(r[9] == 5 for r in filas if r[0] < .03))
        self.assertTrue(all(r[9] == 0 and r[6:8] == [0,0] for r in filas if r[0] >= .04))

    def test_prediccion_anticipa_transicion_con_ambas_polaridades(self):
        for params,adc in [({},[]),({'PISO_BLANCO_LOW':'false','BLANCO':'700'},['--adc-negro','100','--adc-blanco','900'])]:
            b = simular.compilar(params) if params else self.binario
            f = self.traza(['--piso-prueba','rampa','--sensor-prueba','escape-frontal-retroceso']+adc,b)
            self.assertLess(next(r[0] for r in f if r[9] == 5), .066)

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
