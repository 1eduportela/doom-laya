import time
import laya
from laya.onnx_agent import ONNXAgent

# --- Exactamente el mismo prompt que usa agent.py ---
contexto = (
    "Eres un agente de IA jugando a DOOM. "
    "Tu objetivo es sobrevivir y eliminar la amenaza. "
    "Si tienes munición y un enemigo delante, dispara. "
    "Si te quedas sin munición o necesitas buscar, muévete a los lados."
)
preguntas = {
    "accion": {
        "instructions": "¿Qué acción ejecuto?",
        "type": "choice",
        "criteria": ["IZQUIERDA", "DERECHA", "DISPARAR"]
    }
}
situaciones = [
    "El enemigo está a la IZQUIERDA.",
    "El enemigo está a la DERECHA.",
    "El enemigo está JUSTO DELANTE.",
    "No hay enemigos a la vista.",
]
REPETICIONES = 5

def cargar(nombre):
    inicio = time.perf_counter()
    if nombre == "original":
        modelo = laya.load("convaiinnovations/laya")
    elif nombre == "onnx_fp32":
        modelo = ONNXAgent("convaiinnovations/laya", onnx_path="models/laya_fp32.onnx")
    else:
        modelo = ONNXAgent("convaiinnovations/laya", onnx_path="models/laya_int8.onnx")
    print(f"  (carga: {time.perf_counter() - inicio:.1f} s)")
    return modelo

resultados = {}

for nombre in ["original", "onnx_fp32", "onnx_int8"]:
    print(f"\n=== {nombre} ===")
    modelo = cargar(nombre)

    # Calentamiento: la primera llamada siempre es mas lenta
    modelo.predict(state=f"{contexto} Situación actual: Tienes 50.0 balas. {situaciones[0]}", questions=preguntas)

    tiempos = []
    elecciones = []
    for situacion in situaciones:
        estado = f"{contexto} Situación actual: Tienes 50.0 balas. {situacion}"
        for _ in range(REPETICIONES):
            inicio = time.perf_counter()
            r = modelo.predict(state=estado, questions=preguntas)
            tiempos.append(time.perf_counter() - inicio)
        a = r["answers"]["accion"]
        probs = ", ".join(f"{k}: {v:.2f}" for k, v in a["probabilities"].items())
        print(f"  {situacion:32s} -> {a['choice']:10s} | {probs}")
        elecciones.append(a["choice"])

    media = sum(tiempos) / len(tiempos)
    print(f"  Tiempo medio por llamada: {media:.3f} s")
    resultados[nombre] = (media, elecciones)
    del modelo  # liberamos memoria antes de cargar el siguiente

print("\n=== RESUMEN ===")
base_tiempo, base_elecciones = resultados["original"]
for nombre, (media, elecciones) in resultados.items():
    iguales = sum(a == b for a, b in zip(elecciones, base_elecciones))
    print(f"{nombre:10s} | {media:.3f} s/llamada | {base_tiempo / media:.1f}x más rápido | decide igual que el original: {iguales}/4")
