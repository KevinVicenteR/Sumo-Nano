"""Regresiones de arranque, reloj durante escape y telemetría de ataque."""
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'simulacion'))
import simular

class SimulacionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        simular.BUILD.mkdir(parents=True,exist_ok=True)
        cls.binario=simular.compilar({'MARGEN_CERCA_BORDE':'35'})

    def test_malla_cabe_y_cubre_orientaciones(self):
        filas=simular.ejecutar(self.binario,'ninguno',384,['--inicio','malla','--dur','0.02','--rpm','750'])
        self.assertEqual(len(filas),384)
        radios=[]
        for r in filas:
            x,y=float(r['x_inicial_cm'])/100,float(r['y_inicial_cm'])/100
            th=math.radians(float(r['orientacion_inicial_deg']))
            radios.append(math.hypot(x,y))
            for dx in [-.05,.05]:
                for dy in [-.05,.05]:
                    self.assertLessEqual(math.hypot(x+dx*math.cos(th)-dy*math.sin(th),y+dx*math.sin(th)+dy*math.cos(th)),.35002)
        self.assertEqual(min(radios),0)
        self.assertGreater(max(radios),.29)

    def test_escape_no_interrumpe_muestreo_y_blanco_inicial_permitido(self):
        import csv
        with tempfile.TemporaryDirectory() as temp:
            ruta=Path(temp)/'tray.csv'
            simular.ejecutar(self.binario,'ninguno',1,['--inicio','fijo','--x','.295','--y','0','--theta','0','--dur','.8','--rpm','750'],ruta)
            with ruta.open() as archivo:
                filas=[[float(x) for x in r] for r in csv.reader(archivo)]
            self.assertEqual(filas[0][8],1)
            self.assertIn(5,[r[9] for r in filas])
            self.assertIn(6,[r[9] for r in filas])
            self.assertLessEqual(max(b[0]-a[0] for a,b in zip(filas,filas[1:])),.0111)

    def test_busqueda_con_mismo_pwm_no_cuenta_como_ataque(self):
        filas=simular.ejecutar(self.binario,'ninguno',1,['--inicio','fijo','--x','0','--y','0','--theta','0','--dur','1','--rpm','750'])
        self.assertEqual(float(filas[0]['tiempo_ataque_s']),0)
        self.assertGreater(float(filas[0]['distancia_m']),0)

    def test_fuera_de_area_colocacion_rechaza(self):
        import subprocess
        with self.assertRaises(subprocess.CalledProcessError):
            simular.ejecutar(self.binario,'ninguno',1,['--inicio','fijo','--x','.34','--y','0','--theta','0','--dur','.1'])

    def test_semilla_reproducible(self):
        extra=['--inicio','todo','--dur','.8','--rpm','750','--semilla','11']
        self.assertEqual(simular.ejecutar(self.binario,'errante',1,extra),simular.ejecutar(self.binario,'errante',1,extra))

    def test_lecturas_alternantes_avanza_sin_invertir_ruedas(self):
        import csv
        with tempfile.TemporaryDirectory() as temp:
            ruta=Path(temp)/'tray.csv'
            simular.ejecutar(self.binario,'ninguno',1,['--inicio','fijo','--x','0','--y','0','--theta','0','--dur','1','--rpm','750','--sensor-prueba','alternante'],ruta)
            with ruta.open() as f:filas=[[float(v) for v in r] for r in csv.reader(f)]
            seguimiento=[r for r in filas if int(r[9])==3]
            self.assertGreater(len(seguimiento),10)
            self.assertNotIn(7,[int(r[9]) for r in filas])
            self.assertTrue(all(r[6]>0 and r[7]>0 for r in seguimiento))
            cambios=[];prev=0
            for r in seguimiento:
                signo=1 if r[6]>r[7] else -1 if r[6]<r[7] else 0
                if signo and signo!=prev:
                    cambios.append(r[0]);prev=signo
            self.assertTrue(all(b-a>=.079 for a,b in zip(cambios,cambios[1:])))
            self.assertGreater(sum(((b[1]-a[1])**2+(b[2]-a[2])**2)**.5 for a,b in zip(filas,filas[1:])),.05)

    def test_dos_laterales_no_giran_indefinidamente(self):
        import csv
        with tempfile.TemporaryDirectory() as temp:
            ruta=Path(temp)/'tray.csv'
            simular.ejecutar(self.binario,'ninguno',1,['--inicio','fijo','--x','0','--y','0','--theta','0','--dur','1','--rpm','750','--sensor-prueba','laterales'],ruta)
            with ruta.open() as f:filas=[[float(v) for v in r] for r in csv.reader(f)]
            self.assertIn(7,[int(r[9]) for r in filas])
            avance=[r for r in filas if int(r[9])==7]
            self.assertTrue(all(r[6]>0 and r[7]>0 for r in avance))

    def test_alternancia_no_se_confunde_con_ataque_frontal(self):
        filas=simular.ejecutar(self.binario,'ninguno',1,['--inicio','fijo','--x','0','--y','0','--theta','0','--dur','30','--rpm','750','--sensor-prueba','alternante'])
        self.assertEqual(float(filas[0]['tiempo_ataque_s']),0)

    def test_blanco_interrumpe_lecturas_contradictorias(self):
        import csv
        with tempfile.TemporaryDirectory() as temp:
            ruta=Path(temp)/'tray.csv'
            simular.ejecutar(self.binario,'ninguno',1,['--inicio','fijo','--x','.295','--y','0','--theta','0','--dur','.4','--rpm','750','--sensor-prueba','alternante'],ruta)
            with ruta.open() as f:filas=[[float(v) for v in r] for r in csv.reader(f)]
            estados=[int(r[9]) for r in filas if int(r[9])!=0]
            self.assertEqual(estados[0],8)
            self.assertIn(5,estados)

    def test_ataque_continuo_sin_frenadas_periodicas(self):
        import csv
        with tempfile.TemporaryDirectory() as temp:
            ruta=Path(temp)/'tray.csv'
            simular.ejecutar(self.binario,'estatico',1,['--inicio','fijo','--x','0','--y','0','--theta','0','--dur','30'],ruta)
            with ruta.open() as f:filas=[[float(v) for v in r] for r in csv.reader(f)]
            self.assertTrue(all(abs(r[6])<=255 and abs(r[7])<=255 for r in filas))
            self.assertIn(4,[int(r[9]) for r in filas])
            self.assertNotIn(9,[int(r[9]) for r in filas])
            self.assertTrue(any(r[6]!=r[7] for r in filas if int(r[9])==4))
            self.assertTrue(all(r[6]>0 and r[7]>0 and max(r[6],r[7])==255 for r in filas if int(r[9])==4))

    def test_arranque_en_blanco_se_retira_hacia_el_interior(self):
        import csv
        with tempfile.TemporaryDirectory() as temp:
            ruta=Path(temp)/'tray.csv'
            resultado=simular.ejecutar(self.binario,'ninguno',1,['--inicio','fijo','--x','.295','--y','0','--theta','0','--dur','1','--rpm','750'],ruta)[0]
            with ruta.open() as f:filas=[[float(v) for v in r] for r in csv.reader(f)]
            self.assertEqual(filas[0][8],1)
            self.assertEqual(resultado['cayo'],'0')
            self.assertTrue(any(math.hypot(r[1],r[2])<.26 for r in filas))

    def test_primer_ataque_no_espera_una_pausa(self):
        import csv
        with tempfile.TemporaryDirectory() as temp:
            ruta=Path(temp)/'tray.csv'
            resultado=simular.ejecutar(self.binario,'estatico',1,['--inicio','fijo','--x','0','--y','0','--theta','0','--dur','3','--rpm','750'],ruta)[0]
            with ruta.open() as f:filas=[[float(v) for v in r] for r in csv.reader(f)]
            primero=next(r for r in filas if int(r[9])==4)
            self.assertLessEqual(primero[0]-float(resultado['t_primer_frontal']),.02)

if __name__=='__main__':unittest.main()
