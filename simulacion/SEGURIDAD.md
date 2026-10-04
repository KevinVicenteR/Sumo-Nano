# Validación del perfil seguro

Fecha: 4 de octubre de 2026. Resultado final: **0 caídas en 5,052 corridas** de los 14 entornos definidos en `arranques.py`, con semillas nuevas 10001–10100. La malla usa 384 poses por modo de enemigo. Cada corrida dura 30 s nominales. Se conservaron la física, las colocaciones iniciales y el criterio de caída del simulador.

## Cambios del control

- Avance, ataque, retroceso y desbloqueo: **PWM 55**. Orientación, giro de escape y giro lateral: **PWM 100**. El perfil prioriza seguridad y es más lento que el anterior de PWM 190.
- Escape reconstruido: freno inicial 180 ms, retroceso de **20–60 ms**, freno posterior 80 ms y pivote de hasta 450 ms. El giro puede continuar con un sensor todavía sobre blanco después del frenado: así evita encadenar retrocesos hacia un borde trasero invisible para los sensores delanteros.
- Frenado de 180 ms antes de pasar de avance a orientación. El temporizador de búsqueda empieza después del freno para conservar el tiempo efectivo de giro.
- Orientación hacia un frontal lateral mediante pivote; al confirmar el central, ataque recto y continuo. Las curvas a estas potencias bajas se descartaron porque podían dejar al robot casi inmóvil.
- Se conserva la memoria del central de 60 ms, la suavización de las órdenes de avance, el aprendizaje del negro y la predicción ADC del borde. Blanco, piso incierto y STOP mantienen prioridad. El enemigo puede interrumpir el resto del escape cuando el piso esté libre.

El objetivo de cero caídas no se consiguió dejando al robot detenido. En las 100 corridas sin enemigo de «todo el dojo», recorrió al menos **0.39 m** y **0.439 m de media** durante los 30 s. En la malla con enemigo hubo orden de ataque en **766/768 corridas**: 382/384 con enemigo quieto y 384/384 con enemigo móvil. Se miden órdenes y movimiento, no victorias ni capacidad de empuje.

## Resultados por entorno

| Entorno | Corridas | Caídas |
|---|---:|---:|
| Objetos exteriores | 300 | 0 |
| Frontales alternantes, señal sintética | 300 | 0 |
| Lateral izquierdo persistente, señal sintética | 300 | 0 |
| Lateral derecho persistente, señal sintética | 300 | 0 |
| Dos laterales persistentes, señal sintética | 300 | 0 |
| Todo el dojo | 300 | 0 |
| Malla de 384 posiciones/orientaciones × 3 modos | 1152 | 0 |
| Arranques junto al borde | 300 | 0 |
| Alcance de enemigo de 12 cm | 300 | 0 |
| Batería +30 % y reductora suave | 300 | 0 |
| Adherencia μ=0.3 y batería +30 % | 300 | 0 |
| μ=0.3, ruedas de 5 cm y batería +60 % | 300 | 0 |
| Enemigo a 0.6 m/s | 300 | 0 |
| Control con 8 ms adicionales por ciclo | 300 | 0 |
| **Total** | **5052** | **0** |

Los tres modos son sin enemigo, quieto y móvil. En los escenarios de señales sintéticas, las detecciones no proceden del disco del enemigo. No se combinaron todas las perturbaciones de todos los entornos entre sí.

## Qué fallaba y qué se descartó

El perfil anterior caía por dos causas observadas: exceso de distancia de frenado con baja adherencia y retrocesos prolongados hacia un borde trasero que no se podía observar. Bajar únicamente la velocidad a 65 dio 20/5052 caídas. Recortar el retroceso resolvió las caídas de la malla, pero las transiciones entre avance y pivote podían conservar velocidad residual.

La versión de PWM 60 con frenado completo dio 0/5052 con semillas 5001–5100, pero otra validación después de corregir el temporizador de búsqueda encontró **2/5052** con semillas 10001–10100, ambas en el escenario extremo con enemigo móvil. Por eso la configuración entregada es PWM **55**, que volvió a evaluarse en todos los entornos y dio 0/5052. Los resultados descartados se conservan por separado; no se mezclan con la validación final.

## Repetir y actualizar el visor

```sh
python3 simulacion/optimizar_seguridad.py --n 100 --semilla 10001 \
  --velocidades 55 --giro 100 --escape-corto --pivote --freno 180 \
  --entornos objetos alternante lateral_izquierdo lateral_derecho laterales \
  todo malla borde sensor_corto bateria_alta resbaloso combinado \
  enemigo_rapido control_lento --exigir-cero --publicar-visor \
  --salida simulacion/resultados/seguridad/repeticion
python3 -m unittest discover -s test -p 'test_simulacion.py' -v
pio run -e nano
python3 simulacion/servidor.py
```

`--exigir-cero` devuelve un error si aparece una caída. Se guardan CSV completos, resúmenes, parámetros y hashes de fuentes. `--publicar-visor` prepara los lotes y trayectorias del perfil seleccionado y actualiza `resultados/visor.html`. El visor usa los lotes de seguridad cuando existen. Si el servidor estaba abierto con otro firmware, hay que reiniciarlo para las nuevas corridas manuales.

La validación final está en `resultados/seguridad/final55/`; los lotes del visor, en `resultados/seguridad/lotes/`. Estos resultados generados están ignorados en Git. La corrección final de las etiquetas de telemetría marca ataque después de aplicar ambas órdenes y freno antes de cambiar motores; no cambia los movimientos ni la física.

Pasan **26 pruebas**, incluyendo regresiones de poses que antes caían por detrás, límite del retroceso, interrupción por enemigo con piso libre, prioridad del blanco, ataque continuo y detección de lecturas inciertas. El firmware compila para Nano. No se ha cargado al robot.

Cero caídas es el resultado de estos lotes, no una garantía universal ni una prueba sobre hardware. La caída del modelo se declara al salir el centro del círculo; las esquinas pueden sobresalir antes. El enemigo no produce colisiones ni empujones. Las lecturas reales de piso, la batería y la adherencia deben verificarse antes de extrapolar estos resultados al robot. Subir velocidades cambia el margen de frenado y requiere volver a validar.
