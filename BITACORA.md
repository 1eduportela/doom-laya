# Bitácora de experimentos

Registro de lo que se ha probado en el proyecto, por qué y qué resultado dio.
Incluye también los experimentos que **fallaron**, porque explican las decisiones del código actual.

Entorno de pruebas: Raspberry Pi 5 de 16 GB (CPU ARM Cortex-A76 de 4 núcleos), Python 3.13, modelo `convaiinnovations/laya`. Escenarios de ViZDoom: `basic` (una sala con un monstruo) y, desde el 26/09, `defend_the_center` (monstruos que llegan desde todas partes, 26 balas).

> Para rellenar los commits: `git log --oneline` muestra el identificador corto de cada uno.

---

## 2026-09-24

**Objetivo del día:** montar el proyecto y conseguir que LAYA juegue en la Raspberry Pi.

**Resumen del día:**

| # | Experimento | Resultado |
|---|---|---|
| 1 | Estructura del proyecto (cuerpo / cerebro) | ✅ Montada |
| 2 | Carga rápida con `fast=True` | ✅ Arranque mucho más rápido |
| 3 | Modelo GGUF cuantizado a 4 bits | ❌ No se puede cargar con la librería `laya` |
| 4 | Cuantización dinámica a 8 bits con PyTorch | ❌ Error `cannot pickle '_thread.lock' object` |
| 5 | Media precisión FP16 (`.half()`) | ❌ Inferencia mucho más lenta; se queda bloqueada |
| 6 | Fijar 4 hilos con `torch.set_num_threads(4)` | ✅ Sistema estable |

---

### Exp. 1: Arquitectura del proyecto

**Objetivo:** separar el "cuerpo" (el juego) del "cerebro" (la IA) para que el código sea modular.
**Cambio:**
- `~/projects/IA/` como raíz, controlada con git para poder deshacer experimentos (`git restore .`).
- `venv/`: entorno virtual para aislar las dependencias de IA del sistema.
- `src/environment.py`: arranca ViZDoom (escenario `basic`), activa el *labels buffer* y traduce la pantalla a datos: munición y posición del enemigo (izquierda / delante / derecha según la coordenada X del Cacodemon).
- `src/agent.py`: clase `DoomAgent`. Carga LAYA, guarda el contexto (las reglas del bot), convierte el estado en texto y traduce la respuesta a una acción.
- `src/main.py`: bucle de la partida (leer estado → decidir → ejecutar).
- `src/detective.py`: script auxiliar que imprime la firma de `modelo.predict()` con `inspect.signature` para descubrir qué parámetros acepta (`state`, `questions`).

**Herramientas:** Python 3.13, `laya` (modelo `convaiinnovations/laya`, basado en ModernBERT), PyTorch, ViZDoom, `nano` como editor.
**Commit:** —

---

### Exp. 2: Arranque rápido con `fast=True`

**Problema:** cargar el modelo tardaba unos 20 segundos en cada ejecución.
**Cambio:** `laya.load("convaiinnovations/laya", fast=True)`.
**Resultado:** el modelo carga casi al instante.
**Conclusión:** ✅ Mejora adoptada.
**Nota (revisado el 26/09):** revisando el código de la librería `laya` se descubrió que `fast=True` **solo funciona con GPU NVIDIA (CUDA)**; en la Raspberry no tiene ningún efecto. La carga más rápida se debió seguramente a que los archivos ya estaban en la caché del disco. Ver 26/09, exp. 1.
**Commit:** —

---

### Exp. 3: Modelo GGUF cuantizado a 4 bits

**Hipótesis:** una versión cuantizada a 4 bits ocuparía menos memoria y sería más rápida.
**Cambio:** descargar manualmente (con `wget`) una versión GGUF desde HuggingFace, en la carpeta `models/`.
**Resultado:** errores 404 al buscar los archivos de configuración.
**Conclusión:** ❌ La librería `laya` no sabe cargar un GGUF. Además, las versiones GGUF publicadas solo contienen el *backbone* (ModernBERT) para llama.cpp; la cabeza de decisión de LAYA va en un archivo aparte y hay que ejecutarla fuera. Se borra `models/` y se restaura el código.
**Commit:** —

---

### Exp. 4: Cuantización dinámica a 8 bits con PyTorch

**Hipótesis:** `torch.quantization.quantize_dynamic` comprime los pesos de 32 a 8 bits al vuelo, sin descargar nada.
**Resultado:** error `cannot pickle '_thread.lock' object`.
**Conclusión:** ❌ Por defecto, `quantize_dynamic` hace una **copia** del modelo (`copy.deepcopy`), y el objeto de LAYA contiene un candado de hilos (`_thread.lock`) que Python no puede copiar.
**Idea para reintentar:** pasar `inplace=True` (cuantiza sin copiar) y aplicarlo solo a la red interna de PyTorch, no al objeto `Agent` completo.
**Commit:** —

---

### Exp. 5: Media precisión FP16

**Hipótesis:** pasar los pesos a 16 bits con `.half()` reduce el tamaño sin necesidad de copiar el modelo.
**Resultado:** la inferencia se vuelve mucho más lenta hasta parecer bloqueada.
**Conclusión:** ❌ En CPU, PyTorch apenas tiene operaciones optimizadas para FP16, así que en la Raspberry es más lento que FP32. FP16 compensa en GPU, no en CPU.
**Commit:** —

---

### Exp. 6: Fijar el número de hilos

**Problema:** inestabilidad al ejecutar el modelo.
**Cambio:** `torch.set_num_threads(4)` al principio de `main.py`, para usar exactamente los 4 núcleos de la Raspberry.
**Resultado:** sistema estable, con **~1 s de latencia por turno** según la medición de ese día.
**Conclusión:** ✅ Se mantiene el modelo base en FP32.
**Nota (revisado el 25/09):**
- El `main.py` usado el 25/09 no contiene esta línea. Hay que comprobar si sigue en el código.
- Ese día se concluyó que 1 s por turno era el límite de este hardware. El 25/09 se midió ~1,5 s por llamada, y se vio que el problema se podía atacar por otro lado: **llamar menos al modelo** (caché + frame skip), en vez de hacer cada llamada más rápida.

---

### Lecciones del día

1. **Git permite experimentar sin miedo:** los intentos fallidos se deshicieron con `git restore .`.
2. **No todos los modelos se cuantizan igual.** LAYA tiene una estructura propia (encoder + cabeza de decisión), así que las herramientas estándar (GGUF, `quantize_dynamic` por defecto) no funcionan directamente.
3. **FP16 no es más rápido en CPU.** Menos bits no siempre significa más velocidad: depende de si el hardware tiene operaciones optimizadas para ese formato.

---

## 2026-09-25

**Objetivo del día:** reducir el tiempo que tarda LAYA en decidir (~1,5 s por turno).

**Resumen del día:**

| # | Experimento | Resultado |
|---|---|---|
| 0 | Versión inicial (prompt en español) | ✅ Decide bien, pero ~1,5 s por turno |
| 1 | Prompt en inglés y más corto | ⚠️ Más rápido (~1,2 s), pero decide mal |
| 2 | Caché + frame skip (sobre el prompt en inglés) | ❌ Se queda disparando al aire hasta agotar el tiempo |
| 3 | Banco de pruebas: versiones A y B | ❌ Siempre elige disparar |
| 4 | Banco de pruebas: versiones C y D | ❌ Siempre elige disparar |
| 5 | Vuelta al prompt en español, sin caché | ✅ Gana la partida |
| 6 | Prompt en inglés sin caché, en el juego | ❌ Siempre dispara → el culpable era el idioma |
| 7 | Español + caché | ✅ Gana con 3-4 llamadas a LAYA por partida |
| 8 | Español + caché + frame skip | ✅ Gana en 7 turnos con 2 llamadas a LAYA |

---

### Exp. 0: Medir el punto de partida

**Problema:** LAYA tarda mucho en decidir y el agente va a trompicones.
**Cambio:** se añade un cronómetro (`time.perf_counter()`) alrededor de `modelo.predict()`.
**Resultado:** **~1,5 s por decisión**, y se llama a LAYA en cada turno (1 tic).
**Conclusión:** este es el valor de referencia para comparar las mejoras.
**Commit:** —

---

### Exp. 1: Prompt en inglés y más corto

**Hipótesis:** LAYA procesa todo el texto en una sola pasada, así que menos texto debería tardar menos. Además, el modelo principal está entrenado en inglés.
**Cambio:**
- Contexto reescrito en inglés como reglas cortas ("Enemy LEFT: choose LEFT...").
- Opciones `LEFT`, `RIGHT`, `SHOOT`.
- Munición resumida como "You have ammo" / "No ammo" en vez del número exacto.

**Resultado:** **~1,2 s por decisión** (un 20 % más rápido).
**Conclusión:** el tamaño del texto sí influye en la velocidad. **Error:** en este paso solo se midió la velocidad, no si decidía bien. Ver exp. 2 y 6.
**Commit:** — (no se guardó)

---

### Exp. 2: Caché + frame skip

**Hipótesis:**
- **Caché:** en el escenario `basic` hay muy pocas situaciones posibles. Si se guarda la decisión de cada una, no hace falta volver a preguntar a LAYA.
- **Frame skip:** si cada decisión dura 4 tics en lugar de 1, hacen falta 4 veces menos decisiones.

**Cambio:** diccionario `cache` con clave `(posición, munición)` y `make_action(accion, 4)`.
**Resultado:**
- LAYA solo pensó **1 vez** (1,21 s)... pero decidió `Enemy is LEFT → SHOOT`.
- Como no se movía, la situación nunca cambiaba y la caché repetía el mismo error.
- La partida acabó por tiempo: 75 turnos × 4 tics = 300 tics, el límite del escenario.
- Recompensas: `-4` por turno (tics vivo) y `-9` cuando fallaba un disparo (-4 − 5).

**Conclusión:** la caché hace rápido al agente **tanto si acierta como si se equivoca**: si la primera decisión es mala, se repite para siempre.
**Lección:** en el exp. 1 se cambiaron varias cosas a la vez (idioma, reglas, opciones) sin comprobar que seguía decidiendo bien.
**Commit:** — (no se guardó)

---

### Exp. 3: Banco de pruebas, versiones A y B

**Objetivo:** probar a LAYA sin arrancar el juego, con las 4 situaciones posibles (izquierda, derecha, delante, nada).
**Cambio:** nuevo script `src/test_laya.py`.
- **A:** el prompt en inglés del exp. 1, con opciones cortas.
- **B:** opciones descriptivas ("Turn left toward the enemy on the left"...).

**Resultado:** las dos versiones eligen **disparar en las 4 situaciones**. Con el enemigo a la izquierda, las probabilidades eran:

| LEFT | RIGHT | SHOOT |
|---|---|---|
| 0,07 | 0,04 | **0,90** |

**Conclusión:** el modelo no duda: está muy seguro de disparar, y se equivoca. Además, se descubre que `predict()` devuelve las probabilidades de cada opción, lo cual es muy útil para analizar sus decisiones.
**Nota:** al cargar el modelo aparece un aviso (`RuntimeWarning ... uncalibrated`). Indica que las probabilidades no son exactas como porcentaje, pero la opción elegida sigue siendo válida.
**Commit:** —

---

### Exp. 4: Banco de pruebas, versiones C y D

**Hipótesis:** puede que las reglas ("si X, elige Y") confundan al modelo y funcione mejor si solo se describe la escena.
**Cambio:**
- **C:** solo la descripción de la escena, sin reglas.
- **D:** la escena metida dentro de la propia pregunta.

**Resultado:** las dos eligen **disparar siempre**.
- En **C**, la probabilidad de disparar cambia con la situación: 0,88 si el monstruo está delante y 0,55 si no hay monstruo. Detecta algo, pero no distingue izquierda de derecha (`Turn right` sale algo más alto que `Turn left` en ambos casos).
- En **D**, las probabilidades apenas cambian entre situaciones.

**Conclusión:** con prompts en inglés, el modelo no convierte "el monstruo está a la izquierda" en "gira a la izquierda".
**Commit:** —

---

### Exp. 5: Vuelta al prompt original en español

**Hipótesis:** antes de los cambios del exp. 1 el agente parecía jugar bien.
**Cambio:** se recupera el prompt original en español, sin caché y sin frame skip, añadiendo un registro de lo que ve y lo que elige en cada turno.
**Resultado:**
- Enemigo a la IZQUIERDA → `IZQUIERDA` (turnos 0-16).
- Enemigo JUSTO DELANTE → `DISPARAR` (turnos 17-21).
- **Recompensa 100 en el turno 21**: monstruo eliminado.
- ~1,53 s por decisión.

**Conclusión:** el prompt original en español funciona. La hipótesis era correcta.
**Commit:** —

---

### Exp. 6: Inglés sin caché, en el juego

**Objetivo:** separar las dos variables. ¿El fallo del exp. 2 venía de la caché o del idioma?
**Cambio:** prompt en inglés del exp. 1, **sin caché** y sin frame skip.
**Resultado:** `Enemy is RIGHT → SHOOT` en todos los turnos. No gira nunca hacia el enemigo.
**Conclusión:** **el culpable era el prompt en inglés, no la caché.** Una posible explicación es que en la versión en español las opciones (`IZQUIERDA`, `DERECHA`) aparecen escritas igual que en la frase de la situación ("El enemigo está a la IZQUIERDA"), aunque no está comprobado.
**Commit:** —

---

### Exp. 7: Español + caché

**Cambio:** caché con clave `(posición, munición exacta)` sobre el prompt en español, **sin cambiar ni una palabra del prompt**. Sin frame skip.
**Resultado:**

| Partida | Situación inicial | Llamadas a LAYA | Turnos | ¿Gana? |
|---|---|---|---|---|
| 1 | Delante | 4 | 34 | ✅ (turno 32) |
| 2 | Derecha | 3 | 21 | ✅ (turno 19) |
| 3 | Derecha | 4 | 25 | ✅ (turno 23) |

- Sin caché habrían sido tantas llamadas como turnos (≈ 9 veces más tiempo pensando).
- LAYA vuelve a pensar cuando cambia la munición, porque forma parte de la clave.
- Tiempo total de la partida 3, medido con `time`: **13,8 s** (unos 7,5 s son de arrancar DOOM y cargar el modelo).
- Algunos disparos fallan (`-6` = -1 por el tic − 5 por fallar) aunque el enemigo está "JUSTO DELANTE".

**Conclusión:** la caché funciona y no cambia las decisiones.
**Commit:** —

---

### Exp. 8: Frame skip

**Cambio:** `make_action(accion, 4)` en `environment.py`.
**Predicción:** con la caché, LAYA solo piensa cuando cambia la situación, así que el frame skip apenas debería mejorar el tiempo.
**Resultado:**

| | Sin frame skip | Con frame skip |
|---|---|---|
| Tiempo total | 13,8 s | **10,4-10,6 s** |
| Llamadas a LAYA | 4 | **2** |
| Turnos hasta ganar | 24 | **7** |
| Disparos fallados | 1 | **0** |

Probado con el enemigo a la izquierda y a la derecha: gana las dos veces, sin oscilar alrededor del centro.

**Conclusión:** la predicción **falló**. El frame skip sí reduce las llamadas a LAYA porque el agente ya no falla disparos: cada disparo fallado gastaba una bala y la munición forma parte de la clave de la caché, así que cada fallo creaba una situación nueva.
**Commit:** «Agente con caché y frame skip: gana en ~7 turnos, 2 llamadas a LAYA»

---

### Lecciones del día

1. **Primero medir, luego cambiar.** Sin el cronómetro del exp. 0 no habría con qué comparar.
2. **Cambiar una sola cosa cada vez.** El exp. 1 cambió varias a la vez y rompió el agente sin que se notara.
3. **Medir la calidad, no solo la velocidad.** Un agente rápido que decide mal no sirve.
4. **Un banco de pruebas ahorra tiempo.** Probar las 4 situaciones sin arrancar el juego es mucho más rápido.
5. **Las probabilidades dicen más que la elección.** Muestran si el modelo duda o está seguro.
6. **Comprobar las predicciones.** La del exp. 8 falló, y entender por qué enseñó cómo interactúan la caché y la munición.

---

## 2026-09-26

**Objetivo del día:** cuantizar LAYA para que cada decisión sea más rápida, y probar el agente en un escenario más difícil (`defend_the_center`).

**Resumen del día:**

| # | Experimento | Resultado |
|---|---|---|
| 1 | Revisar el código de la librería `laya` | 💡 `fast=True` solo sirve con CUDA; existe `ONNXAgent` |
| 2 | Exportar a ONNX con el exportador clásico | ❌ Longitud del texto fijada en 16 tokens |
| 3 | Exportar con el exportador nuevo (`dynamo=True`) | ✅ Acepta cualquier longitud |
| 4 | Comparar original / ONNX fp32 / ONNX int8 | ✅ int8: 0,43 s por llamada (3,5x) y decide igual con 50 balas |
| 5 | ONNX int8 en el cubo | ✅ Partida completa en 7,9 s |
| 6 | Contador de munición y salud | ✅ Munición y salud leídas por nombre y después de actuar |
| 7 | Explorar `defend_the_center` | 💡 Nombres de los enemigos; el ancho indica la distancia |
| 8 | Primer intento en `defend_the_center` (int8) | ❌ Peor que un jugador al azar |
| 9 | Banco de pruebas con todas las municiones | 💡 int8 falla el 17 % apuntando; el original, 0 % |
| 10 | Añadir las opciones ESPERAR / BUSCAR | ⚠️ Menos disparos al aire, pero no fiable |
| 11 | Frase que contiene la opción ("hay que BUSCAR") | ✅ 6/6: LAYA decide por coincidencia de palabras |
| 12 | ONNX fp32 + BUSCAR en el juego | ✅ 13 enemigos, sin daño mientras tuvo balas |
| 13 | int8 por canal (`per_channel=True`) | ❌ 63/78 apuntando |
| 14 | Cuantización solo de pesos (w8, w8_acc4, w4_acc4) | ✅ **w8_acc4: 78/78 y 0,69 s** |
| 15 | Puntería según el tamaño del enemigo + giro fino | ✅ 24 enemigos con 26 balas |
| 16 | Tolerancia mínima de 5 px | ✅ Acaba con el micro-baile |
| 17 | Evaluador de varias partidas | ✅ ~23 enemigos de media; tolerancia 5 px, 30 % menos turnos |
| 18 | Reorganizar `src/` en carpetas | ✅ Funciona con `python -m` |

---

### Exp. 1: Revisar el código de la librería `laya`

**Objetivo:** antes de volver a intentar la cuantización (que falló el 24/09), entender cómo está hecha la librería.
**Cambio:** descargar el paquete `laya` (versión 0.3.20) y el repositorio oficial y leer su código.
**Resultado:**
- `fast=True` activa una ruta optimizada con kernels de TileLang que **solo funciona con CUDA** (GPU NVIDIA). En la Raspberry no hace nada.
- La librería incluye un **`ONNXAgent`** (`laya/onnx_agent.py`): una versión de LAYA que usa **ONNX Runtime**, un motor optimizado para CPU. Tiene la misma interfaz (`predict(state=..., questions=...)`) y se encarga del tokenizador; solo necesita un archivo `.onnx`.
- El repositorio tiene un script oficial de exportación (`scripts/export_onnx.py`). Los `.onnx` publicados por otras personas no encajan: por ejemplo, el de `receptron` tiene una salida con otro nombre (`act_probs` en vez de `act_logits`).

**Conclusión:** 💡 La vía para cuantizar es exportar **solo la red neuronal** (`agent.model`) a ONNX. Así se evita el candado de hilos que causó el error `pickle` del 24/09.
**Commit:** —

---

### Exp. 2: Exportar a ONNX con el exportador clásico

**Cambio:** `src/exportar_onnx.py` basado en el script oficial, con `torch.onnx.export(..., dynamo=False)` y `dynamic_axes`. Datos de ejemplo de 16 tokens.
**Resultado:** la exportación termina en 16 s (1,6 GB), pero al usarlo:

```
Reshape node '/layers.0/self_attn/Reshape_4': Input shape:{122,1,1024}, requested shape:{16,16,64}
```

**Conclusión:** ❌ El exportador clásico "graba" el modelo mientras procesa el ejemplo, y en las capas de atención de la cabeza de decisión de LAYA se quedó con la longitud del ejemplo (16) como si fuera fija. El prompt real tiene 122 tokens. El problema se reprodujo con una capa `nn.TransformerEncoderLayer` aislada.
**Commit:** —

---

### Exp. 3: Exportar con el exportador nuevo

**Cambio:** `torch.onnx.export(..., dynamo=True)` indicando las dimensiones variables con `torch.export.Dim` (longitud del texto entre 4 y 8192; número de opciones entre 2 y 256). Hace falta instalar `onnxscript`.
**Resultado:** exportado en 58 s. El modelo se guarda en dos archivos: `laya_fp32.onnx` (3 MB, el grafo) y `laya_fp32.onnx.data` (1,6 GB, los pesos). Acepta textos de cualquier longitud.
**Nota:** para poder cuantizarlo hay que borrar antes las anotaciones de tamaño que deja el exportador (`del modelo.graph.value_info[:]`); si no, el cuantizador falla con `Inferred shape and existing shape differ`.
**Conclusión:** ✅ El exportador nuevo analiza el código en lugar de grabarlo, y entiende que la longitud es variable.
**Commit:** —

---

### Exp. 4: Comparar original, ONNX fp32 y ONNX int8

**Cambio:**
- `src/cuantizar_onnx.py`: `quantize_dynamic(..., weight_type=QInt8)` de ONNX Runtime. Tamaño: 1,6 GB → 405 MB.
- `src/comparar_modelos.py`: los tres modelos con el prompt en español, las 4 posiciones, 50 balas y 5 repeticiones por situación.

**Resultado:**

| Modelo | Tiempo por llamada | Mejora | Decide igual que el original |
|---|---|---|---|
| Original (PyTorch) | 1,51 s | — | — |
| ONNX fp32 | 1,02 s | 1,5x | 4/4, probabilidades idénticas |
| ONNX int8 | **0,43 s** | **3,5x** | 4/4, pero con menos margen |

Con el enemigo a la DERECHA, el original daba DERECHA 0,61 frente a 0,20 y 0,18; el int8, DERECHA 0,38 frente a 0,31 y 0,32. Acierta, pero por poco.

**Conclusión:** ✅ ONNX Runtime ya es más rápido que PyTorch sin cuantizar, e int8 da 3,5 veces más velocidad. ⚠️ El poco margen del int8 era una señal de alarma (ver exp. 9).
**Commit:** —

---

### Exp. 5: ONNX int8 en el cubo

**Cambio:** `agent.py` con una variable `MODELO` para elegir el modelo, usando `ONNXAgent`.
**Resultado:** gana a izquierda y a derecha, en 7-9 turnos, con 2 llamadas a LAYA de 0,43 s.

| | Original | ONNX int8 |
|---|---|---|
| Partida completa (`real`) | ~10,5 s | **7,9 s** |
| Trabajo total de CPU (`user`) | ~19 s | **10 s** |

**Conclusión:** ✅ En el cubo LAYA ya casi no cuenta: de 7,9 s, solo 0,86 s son de pensar. El resto es arrancar DOOM y cargar librerías.
**Commit:** —

---

### Exp. 6: Contador de munición y salud

**Problema:** el agente disparaba dos veces y la munición no parecía bajar.
**Causas:**
1. `main.py` imprimía la munición leída **antes** de actuar.
2. La pistola de DOOM tarda unos tics en disparar desde que se pulsa el botón, y la partida del cubo termina justo al matar al monstruo.

**Cambio:**
- `environment.py`: munición y salud leídas **por nombre** con `get_game_variable(AMMO2 / HEALTH)`, en vez de por posición. Así funciona en cualquier escenario y también después de actuar. El escenario pasa a ser un parámetro.
- `main.py`: se lee de nuevo tras actuar y se muestra *antes → después*, más un resumen final.

**Resultado:** se ve `Munición: 50 -> 49` en el turno del disparo.
**Conclusión:** ✅ Resuelto.
**Commit:** —

---

### Exp. 7: Explorar `defend_the_center`

**Cambio:** `src/explorar_escenario.py` juega sin IA (gira y dispara a ratos) y apunta todo lo que aparece.
**Resultado:**
- Botones `TURN_LEFT, TURN_RIGHT, ATTACK`, en el mismo orden que las acciones del agente. Resolución 320×240. Duración máxima: 2100 tics.
- Enemigos: **`MarineChainsawVzd`** y **`Demon`** (ninguno se llama `Cacodemon`).
- Objetos que hay que ignorar: `DoomPlayer` (es el propio jugador, siempre en el centro), `BulletPuff` y `Blood`.
- **El ancho en pantalla indica la distancia**: 5 px lejos, más de 60 px encima.
- Puede haber varios enemigos a la vez.
- Referencia del jugador al azar: muerto en el turno 110, ~4 enemigos, recompensa 3.

**Conclusión:** 💡 Explorar antes de programar evitó un agente que nunca habría visto a ningún enemigo.
**Commit:** —

---

### Exp. 8: Primer intento en `defend_the_center`

**Cambio:** `environment.py` reconoce los tres tipos de enemigo y apunta al más cercano (el más ancho). Prompt sin cambios. Modelo int8.
**Resultado:** **peor que el jugador al azar**: 69 y 107 turnos, 2 enemigos, recompensa 1.
- Partida 1: con 24 balas, `JUSTO DELANTE → IZQUIERDA` y `DERECHA → IZQUIERDA`. La caché congeló esos errores y el agente **giró a la izquierda 42 turnos seguidos** mientras le atacaban.
- Partida 2: con 20 balas, `JUSTO DELANTE → DERECHA`, lo que produjo **50 turnos de baile** izquierda-derecha.

**Conclusión:** ❌ El número de balas parecía cambiar las decisiones de LAYA. Había dos sospechosos: la cuantización o el propio modelo.
**Commit:** —

---

### Exp. 9: Banco de pruebas con todas las municiones

**Cambio:** `src/test_municion.py`: municiones de 26 a 0 × 4 posiciones, con el original y con int8.
**Resultado:**

| | Apuntar (IZQ, DER, DEL con 1-26 balas) | Sin enemigos |
|---|---|---|
| Original | **78/78 (100 %)** | Dispara siempre |
| int8 | 65/78 (83 %), errores repartidos al azar | Dispara casi siempre |

Los fallos del int8 coinciden con los del juego (24 y 20 balas). Además, con 0 balas y un enemigo delante, los dos eligen DISPARAR.
**Conclusión:** 💡 El culpable principal era la **cuantización**: el original no es sensible al número de balas. Con 50 balas el int8 tuvo suerte. **Hay que probar todo el rango, no un solo caso.** Aparte, los dos modelos **disparan al aire** cuando no ven enemigos.
**Commit:** —

---

### Exp. 10: Añadir una opción de "no hacer nada"

**Hipótesis:** LAYA siempre tiene que elegir una opción aunque ninguna encaje, y cuando no hay enemigo "disparar" es la que más tirón tiene.
**Cambio:** `src/test_opciones.py` (ONNX fp32): 3 opciones frente a + ESPERAR frente a + BUSCAR.
**Resultado:**

| Versión | Sin enemigos correcto | Probabilidad de DISPARAR sin enemigos |
|---|---|---|
| 3 opciones | 0/6 | 0,56 |
| + ESPERAR | 3/6 | 0,29 |
| + BUSCAR | 1/6 | 0,30 |

Añadir una opción **no estropea** IZQ, DER ni DEL.
**Conclusión:** ⚠️ La hipótesis era correcta: con una alternativa, disparar pierde la mitad de la probabilidad. Pero la opción nueva gana por poco y no es fiable.
**Commit:** —

---

### Exp. 11: Que la frase contenga la opción

**Hipótesis:** el español funcionaba porque la frase *"El enemigo está a la IZQUIERDA"* contiene la opción `IZQUIERDA`. La frase de "no hay enemigos" no contenía ninguna.
**Cambio:** `src/test_opciones2.py`: *"No hay enemigos a la vista, hay que ESPERAR."* / *"...hay que BUSCAR."*
**Resultado:**

| Versión | Sin enemigos correcto | Probabilidades (20 balas) |
|---|---|---|
| ESPERAR + frase | 6/6 | ESPERAR 0,65 · DISPARAR 0,15 |
| BUSCAR + frase | 6/6 | **BUSCAR 0,72** · DISPARAR 0,10 |

**Conclusión:** ✅ **Teoría confirmada: LAYA decide sobre todo por coincidencia de palabras** entre la situación y las opciones. Gran parte de la "inteligencia" está en cómo `environment.py` describe la situación. Se elige BUSCAR (girar), porque en este escenario los enemigos llegan también por la espalda.
**Commit:** —

---

### Exp. 12: ONNX fp32 + BUSCAR en el juego

**Cambio:**
- `agent.py`: modelo ONNX fp32 y diccionario `ACCIONES` (`BUSCAR` = girar a la derecha). Las opciones de LAYA salen del propio diccionario.
- `environment.py`: frase *"No hay enemigos a la vista, hay que BUSCAR."*

**Resultado:** 205 turnos, **13 enemigos**, recompensa 12, salud 100 hasta quedarse sin balas. 57 llamadas a LAYA (61 s pensando).
**Observaciones:** acierta 1 de cada 2 disparos, porque la zona de "delante" (40 px) es mucho más ancha que un enemigo lejano (5-10 px). Además, con dos enemigos a distancia parecida, el objetivo cambia de un turno a otro y el agente baila entre los dos.
**Conclusión:** ✅ Mucho mejor que el azar. Ahora el límite son las balas.
**Commit:** —

---

### Exp. 13: int8 por canal

**Hipótesis:** una escala por columna de pesos (`per_channel=True`) reduciría el error de redondeo.
**Cambio:** `src/cuantizar_pc.py`. Banco de pruebas actualizado a la versión actual del agente (4 opciones, frase con BUSCAR, munición de 26 a 1).
**Resultado:**

| | Apuntar | Buscar |
|---|---|---|
| int8 | 53/78 | 19/26 |
| int8 por canal | 63/78 | 18/26 |

**Conclusión:** ❌ Mejora, pero no basta. Además, el int8 **empeoró al pasar de 3 a 4 opciones** (del 83 % al 68 %): con más opciones los márgenes son más estrechos. Explicación: la cuantización dinámica redondea también las **activaciones** con **una sola escala por capa**, y en los modelos tipo BERT unos pocos valores enormes (*outliers*) arruinan esa escala. `per_channel` solo mejora los pesos.
**Commit:** —

---

### Exp. 14: Cuantización solo de pesos

**Idea:** la versión web de LAYA a 8 bits (`nvkudva/laya-web-q8`) usaba cuantización "solo de pesos" y mantenía las decisiones del original.
**Cambio:** `src/cuantizar_pesos.py` con `MatMulNBitsQuantizer` de ONNX Runtime, bloques de 32 pesos por escala y escala simétrica:
- `w8`: pesos en 8 bits; el cálculo se hace en float32.
- `w8_acc4`: pesos en 8 bits; `accuracy_level=4` (activaciones en int8, **por bloques de 32**).
- `w4_acc4`: pesos en 4 bits.

**Resultado** (banco de pruebas, 104 llamadas):

| Variante | Apuntar | Buscar | Tiempo por llamada |
|---|---|---|---|
| ONNX fp32 (referencia) | 78/78 | ✓ | ~1,05 s |
| int8 dinámico | 53/78 | 19/26 | ~0,46 s |
| w8 | **78/78** | **26/26** | 1,62 s 🐢 |
| **w8_acc4** | **78/78** | **26/26** | **0,69 s** |
| w4_acc4 | 37/78 | — | — |

**Conclusión:** ✅ **w8_acc4 decide exactamente igual que el original y es 2,2 veces más rápido.**
- `w8` es preciso pero lento: convierte los pesos a float32 en cada llamada.
- `w8_acc4` redondea las activaciones por bloques pequeños, así que un outlier solo estropea su bloque.
- 4 bits (16 valores posibles) es demasiado para un modelo pequeño como LAYA.

**Commit:** —

---

### Exp. 15: Puntería según el tamaño del enemigo

**Cambio en `environment.py`:**
- La zona de "JUSTO DELANTE" pasa a ser **un cuarto del ancho del enemigo** (mínimo 2 px). El punto de mira tiene que caer sobre su cuerpo.
- **Giro fino:** si el enemigo está a menos de 40 px del centro, los giros duran 1 tic en lugar de 4.
- El centro de la pantalla se calcula con `get_screen_width()` en lugar de fijarlo en 160.
- `agent.py` carga cualquier modelo por su nombre (`models/laya_<nombre>.onnx`). Modelo: `w8_acc4`.

**Resultado:** 549 turnos, **24 enemigos con 26 balas** (92 % de acierto), recompensa 23. 82 llamadas a LAYA en 57 s.
**Problema nuevo:** un **micro-baile** de hasta 140 turnos (desvío -4 ↔ +6). Un giro de 1 tic mueve unos 10 px, y con una tolerancia de ±2-3 px es imposible caer dentro.
**Conclusión:** ✅ La puntería casi dobla los enemigos eliminados. Hay que ajustar la tolerancia mínima.
**Commit:** —

---

### Exp. 16: Tolerancia mínima de 5 px

**Cambio:** `tolerancia = max(ancho / 4, 5)`, es decir, al menos medio paso de giro.
**Resultado (1 partida):** 311 turnos, 18 enemigos, recompensa 17.
**Conclusión:** ⚠️ Con una sola partida no se puede saber si es peor o mala suerte. Ver exp. 17.
**Commit:** —

---

### Exp. 17: Evaluador de varias partidas

**Cambio:**
- `src/evaluar.py`: carga el modelo una vez y juega 5 partidas con cada tolerancia (2 y 5 px), mostrando solo el resumen de cada partida.
- La tolerancia mínima pasa a ser configurable (`self.tolerancia_min`).

**Resultado:**

| Tolerancia mínima | Enemigos (media) | Rango | Acierto | Turnos (media) |
|---|---|---|---|---|
| 2 px | 23,8 | 21-26 | 92 % | 503 |
| **5 px** | 23,2 | 20-25 | 89 % | **353** |

- La primera partida tardó 57 s; las siguientes, **entre 0 y 6 s**.
- LAYA solo pensó **103 veces** en las 10 partidas, frente a 108 situaciones posibles (4 posiciones × 27 valores de munición).

**Conclusión:** ✅ **Empate en enemigos, pero 5 px usa un 30 % menos de turnos** (sin micro-baile). Se adopta 5 px. El escenario está prácticamente resuelto: ~23 de 26 enemigos posibles, limitado por la munición.
💡 **La caché ha "aprendido" el escenario:** con pocas situaciones posibles, LAYA actúa como generador de una tabla de decisiones y su velocidad casi deja de importar. Lo que importa es que la tabla sea correcta (de ahí la importancia de que el modelo cuantizado saque 78/78).
**Commit:** —

---

### Exp. 18: Reorganizar `src/` en carpetas

**Cambio:**

```
src/
├── main.py
├── agente/agent.py
├── entorno/environment.py
├── cuantizacion/   exportar_onnx, cuantizar_onnx, cuantizar_pc, cuantizar_pesos
├── pruebas/        test_laya, test_municion, test_opciones, test_opciones2, comparar_modelos
└── herramientas/   evaluar, explorar_escenario, detective
```

- Un `__init__.py` en cada carpeta para que sean paquetes de Python.
- Imports completos: `from src.entorno.environment import DoomEnvironment`.
- Ejecución con `python -m` desde la raíz del proyecto: `python -m src.main`, `python -m src.herramientas.evaluar`...
- README actualizado con la nueva estructura, los comandos y cómo generar los modelos.

**Resultado:** todo funciona. Dos partidas de comprobación:
- 216 turnos, 17 enemigos, **muerto con 7 balas** (primera vez que muere con munición).
- 346 turnos, **26 de 26 enemigos**, 100 % de acierto, recompensa 25: **la máxima puntuación posible**.

**Conclusión:** ✅ Código organizado. Las dos partidas muestran lo mucho que varía el resultado con el mismo código: hay que evaluar siempre con varias partidas.
**Commit:** —

---

### Lecciones del día

1. **Leer el código de las librerías.** Así se descubrieron `ONNXAgent` y que `fast=True` no hacía nada en la Raspberry.
2. **Probar todo el rango, no un solo caso.** El int8 parecía perfecto con 50 balas y fallaba con 24.
3. **Un banco de pruebas con criterio claro** ("tiene que sacar 78/78") permite comparar modelos de forma objetiva.
4. **La caché congela lo que decide el modelo**, tanto los aciertos como los errores.
5. **Con LAYA, cómo se describe la situación importa tanto como el modelo:** decide por coincidencia de palabras.
6. **No todas las cuantizaciones son iguales.** Lo decisivo fue cómo se tratan las activaciones: una escala por capa (falla) frente a una por bloque de 32 (funciona).
7. **Menos bits no siempre es mejor:** 4 bits rompió el modelo, y w8 sin `accuracy_level` era más lento que fp32.
8. **Una partida no es una prueba.** Con el mismo código salen 17 o 26 enemigos: hay que evaluar con varias partidas y la media.
9. **Explorar el terreno antes de programar** (nombres de enemigos, qué objetos ignorar).

---

## Ideas pendientes

- **Fijar el objetivo:** con dos enemigos a distancia parecida, el más cercano cambia de un turno a otro y el agente baila entre los dos. Seguir al mismo enemigo hasta eliminarlo o perderlo de vista, o elegir el más cercano al punto de mira.
- **Investigar la muerte con 7 balas** (26/09, exp. 18): posiblemente por el cambio de objetivo o por un enemigo que llega por la espalda.
- **Sin munición y con un enemigo delante, elige DISPARAR.** No afecta en `defend_the_center` (no hay nada mejor que hacer), pero sí en escenarios donde se pueda huir o recoger munición.
- **Escenario donde la salud importe:** `take_cover` (esquivar bolas de fuego) o `health_gathering` (recoger botiquines). Ahí la caché acertará menos y la velocidad de `w8_acc4` se notará más.
- **Mejoras del código:**
  - No importar `laya` (PyTorch) cuando se usa un modelo ONNX, para arrancar más rápido y usar menos memoria.
  - Clave de la caché `(posición, tiene_munición)` en vez de la munición exacta: 8 situaciones en lugar de 108. Solo si en el escenario el número exacto de balas no importa.
  - Mostrar BUSCAR en `main.py` (ahora aparece como "DERECHA").
- **Comprobar `torch.set_num_threads(4)`** (24/09, exp. 6): no aparece en el `main.py` actual. Solo afecta al modelo original de PyTorch; ONNX Runtime gestiona sus propios hilos.
- **Fine-tuning:** generar ejemplos correctos automáticamente con reglas y entrenar LAYA con ellos (en GPU, no en la Raspberry).
