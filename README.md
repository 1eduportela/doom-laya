# IA que juega a DOOM con LAYA

Agente de IA que juega a DOOM usando [ViZDoom](https://github.com/Farama-Foundation/ViZDoom) y el modelo de decisión [LAYA](https://huggingface.co/convaiinnovations/laya), ejecutándose en una **Raspberry Pi 5 (16 GB)** solo con CPU.

## Cómo funciona

LAYA no ve la pantalla del juego. En cada turno:

1. **`entorno/environment.py`** lee el estado de ViZDoom: munición, salud y qué objetos se ven en pantalla (gracias al *labels buffer*). Elige el enemigo más cercano (el más ancho) y describe su posición con una frase: *"El enemigo está a la IZQUIERDA."*
2. **`agente/agent.py`** construye el texto completo (contexto + munición + posición) y LAYA elige una opción: `IZQUIERDA`, `DERECHA`, `DISPARAR` o `BUSCAR`.
3. La opción se traduce a una acción del juego y se ejecuta.

```
environment.py ──estado──▶ agent.py ──texto──▶ LAYA
      ▲                        │  ◀──opción──
      └───────acción───────────┘
```

### Optimizaciones
- **Modelo cuantizado `w8_acc4`:** LAYA exportado a ONNX y cuantizado a 8 bits por bloques de 32 (pesos y activaciones). Decide exactamente igual que el original y es ~2 veces más rápido (0,69 s frente a 1,5 s por decisión).
- **Caché de decisiones:** si una situación (posición + munición) ya se vio, se reutiliza la respuesta sin llamar a LAYA.
- **Frame skip adaptativo:** cada acción dura 4 tics, pero los giros son de 1 tic cuando el enemigo está cerca del centro (giro fino para apuntar).
- **Puntería según distancia:** la zona de "JUSTO DELANTE" es un cuarto del ancho del enemigo (mínimo 5 px).

### Claves para que LAYA decida bien
- El prompt debe estar en **español**: con un prompt en inglés elige disparar siempre.
- LAYA decide sobre todo por **coincidencia de palabras** entre la situación y las opciones. Por eso las frases usan las mismas palabras que las opciones (*"a la IZQUIERDA"* → `IZQUIERDA`, *"hay que BUSCAR"* → `BUSCAR`).

## Estructura

```
src/
├── main.py                 # Jugar una partida mostrando cada turno
├── agente/
│   └── agent.py            # El cerebro: LAYA + caché
├── entorno/
│   └── environment.py      # Los ojos y las manos: conexión con ViZDoom
├── cuantizacion/           # Crear los modelos de models/
│   ├── exportar_onnx.py    #   PyTorch -> ONNX fp32
│   ├── cuantizar_onnx.py   #   int8 dinámico
│   ├── cuantizar_pc.py     #   int8 dinámico por canal
│   └── cuantizar_pesos.py  #   w8, w8_acc4 y w4_acc4 (solo pesos)
├── pruebas/                # Bancos de pruebas de LAYA (sin arrancar el juego)
│   ├── test_municion.py    #   todas las municiones x 4 posiciones
│   ├── comparar_modelos.py
│   ├── test_opciones.py
│   ├── test_opciones2.py
│   └── test_laya.py
└── herramientas/           # Utilidades con el juego
    ├── grabadora.py        #   graba una partida en vídeo (MP4 con sonido)
    ├── evaluar.py          #   varias partidas + estadísticas
    ├── explorar_escenario.py
    └── detective.py
models/                     # Modelos ONNX (no se suben a git; se generan con cuantizacion/)
videos/                     # Vídeos grabados (no se suben a git)
```

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install vizdoom laya onnx onnxruntime onnxscript opencv-python-headless
sudo apt install ffmpeg      
```

### Generar los modelos
Los modelos no están en el repositorio (ocupan más de 1 GB). Para crearlos:

```bash
mkdir -p models
python -m src.cuantizacion.exportar_onnx     # crea models/laya_fp32.onnx (+ .onnx.data)
python -m src.cuantizacion.cuantizar_pesos   # crea models/laya_w8.onnx, laya_w8_acc4.onnx, laya_w4_acc4.onnx
```

## Uso

Todos los comandos se ejecutan **desde la raíz del proyecto**.

| Qué | Comando |
|---|---|
| Jugar una partida | `python -m src.main` |
| Solo el resumen final | `python -m src.main \| tail -6` |
| Jugar y grabar en vídeo | `python -m src.herramientas.grabadora` |
| Evaluar varias partidas | `python -m src.herramientas.evaluar \| grep -v "LAYA pensó"` |
| Banco de pruebas de un modelo | `python -m src.pruebas.test_municion w8_acc4` |
| Explorar un escenario | `python -m src.herramientas.explorar_escenario` |

Para cambiar de modelo, edita `MODELO` en `src/agente/agent.py` (`"original"` o el nombre de un archivo `models/laya_<nombre>.onnx`). Para cambiar de escenario, edita `ESCENARIO` en `src/main.py`.

## Ver jugar al agente

La Raspberry no tiene interfaz gráfica, así que las partidas se graban en vídeo y se ven en otro ordenador.

```bash
python -m src.herramientas.grabadora
```

- Juega una partida con `main()` y la guarda en `videos/<escenario>_<fecha>.mp4`.
- El vídeo va a **velocidad real** (35 fotogramas por segundo, uno por tic de juego), aunque LAYA tarde en pensar.
- Incluye la **barra de estado de DOOM** (HUD) y el **sonido** del juego.
- Si ffmpeg está instalado, el vídeo se convierte a **H.264 + AAC**, compatible con WhatsApp.

**Cómo funciona:** `main(grabadora=None)` acepta una grabadora opcional. `python -m src.main` juega sin grabar; `grabadora.py` crea una `Grabadora` y llama a `main(grabadora=...)`, así que la partida grabada es exactamente la misma que la normal. En cada turno, `main` pasa a la grabadora la imagen (repetida tantas veces como tics dura la acción) y el sonido de la acción anterior.

Para traer los vídeos al PC (desde el PC):

```bash
scp "pi@<ip-de-la-raspberry>:~/projects/IA/videos/*.mp4" .
```
