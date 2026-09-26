import time
from laya.onnx_agent import ONNXAgent

modelo = ONNXAgent("convaiinnovations/laya", onnx_path="models/laya_fp32.onnx")

contexto = (
    "Eres un agente de IA jugando a DOOM. "
    "Tu objetivo es sobrevivir y eliminar la amenaza. "
    "Si tienes munición y un enemigo delante, dispara. "
    "Si te quedas sin munición o necesitas buscar, muévete a los lados."
)

versiones = {
    "3 opciones (actual)": ["IZQUIERDA", "DERECHA", "DISPARAR"],
    "+ ESPERAR": ["IZQUIERDA", "DERECHA", "DISPARAR", "ESPERAR"],
    "+ BUSCAR": ["IZQUIERDA", "DERECHA", "DISPARAR", "BUSCAR"],
}

posiciones = {
    "IZQ": "El enemigo está a la IZQUIERDA.",
    "DER": "El enemigo está a la DERECHA.",
    "DEL": "El enemigo está JUSTO DELANTE.",
    "NADA": "No hay enemigos a la vista.",
}

def es_correcta(clave, eleccion, balas):
    if clave == "IZQ":
        return eleccion == "IZQUIERDA"
    if clave == "DER":
        return eleccion == "DERECHA"
    if clave == "DEL":
        return eleccion == "DISPARAR" if balas > 0 else eleccion != "DISPARAR"
    return eleccion != "DISPARAR"   # NADA: cualquier cosa menos disparar

municiones = [26, 20, 13, 5, 1, 0]

for nombre, opciones in versiones.items():
    preguntas = {
        "accion": {
            "instructions": "¿Qué acción ejecuto?",
            "type": "choice",
            "criteria": opciones
        }
    }
    print(f"\n=== {nombre} ===")
    print("Balas |  IZQ  |  DER  |  DEL  | NADA")
    aciertos = {c: 0 for c in posiciones}
    inicio = time.perf_counter()
    for balas in municiones:
        fila = []
        for clave, frase in posiciones.items():
            estado = f"{contexto} Situación actual: Tienes {float(balas)} balas. {frase}"
            r = modelo.predict(state=estado, questions=preguntas)
            eleccion = r["answers"]["accion"]["choice"]
            if es_correcta(clave, eleccion, balas):
                aciertos[clave] += 1
                fila.append("  ✓  " if clave != "NADA" else f" {eleccion[:4]}✓")
            else:
                fila.append(f" {eleccion[:4]}")
        print(f"  {balas:2d}  | " + " | ".join(fila))
    resumen = ", ".join(f"{c}: {n}/{len(municiones)}" for c, n in aciertos.items())
    print(f"Aciertos -> {resumen}  ({time.perf_counter() - inicio:.0f} s)")

# Probabilidades en detalle para "no hay enemigos"
print("\n=== Probabilidades con 'No hay enemigos' (20 balas) ===")
for nombre, opciones in versiones.items():
    preguntas = {"accion": {"instructions": "¿Qué acción ejecuto?", "type": "choice", "criteria": opciones}}
    estado = f"{contexto} Situación actual: Tienes 20.0 balas. {posiciones['NADA']}"
    probs = modelo.predict(state=estado, questions=preguntas)["answers"]["accion"]["probabilities"]
    print(f"{nombre:22s} | " + ", ".join(f"{k}: {v:.2f}" for k, v in probs.items()))
