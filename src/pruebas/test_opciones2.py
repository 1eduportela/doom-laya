import time
from laya.onnx_agent import ONNXAgent

modelo = ONNXAgent("convaiinnovations/laya", onnx_path="models/laya_fp32.onnx")

contexto = (
    "Eres un agente de IA jugando a DOOM. "
    "Tu objetivo es sobrevivir y eliminar la amenaza. "
    "Si tienes munición y un enemigo delante, dispara. "
    "Si te quedas sin munición o necesitas buscar, muévete a los lados."
)

# Cada version: (opciones, frase para "no hay enemigos")
versiones = {
    "ESPERAR + frase 'hay que ESPERAR'": (
        ["IZQUIERDA", "DERECHA", "DISPARAR", "ESPERAR"],
        "No hay enemigos a la vista, hay que ESPERAR."),
    "BUSCAR + frase 'hay que BUSCAR'": (
        ["IZQUIERDA", "DERECHA", "DISPARAR", "BUSCAR"],
        "No hay enemigos a la vista, hay que BUSCAR."),
}

posiciones_fijas = {
    "IZQ": "El enemigo está a la IZQUIERDA.",
    "DER": "El enemigo está a la DERECHA.",
    "DEL": "El enemigo está JUSTO DELANTE.",
}

def es_correcta(clave, eleccion, balas):
    if clave == "IZQ":
        return eleccion == "IZQUIERDA"
    if clave == "DER":
        return eleccion == "DERECHA"
    if clave == "DEL":
        return eleccion == "DISPARAR" if balas > 0 else eleccion != "DISPARAR"
    return eleccion != "DISPARAR"

municiones = [26, 20, 13, 5, 1, 0]

for nombre, (opciones, frase_nada) in versiones.items():
    preguntas = {"accion": {"instructions": "¿Qué acción ejecuto?", "type": "choice", "criteria": opciones}}
    posiciones = dict(posiciones_fijas, NADA=frase_nada)
    print(f"\n=== {nombre} ===")
    print("Balas |  IZQ  |  DER  |  DEL  | NADA")
    aciertos = {c: 0 for c in posiciones}
    for balas in municiones:
        fila = []
        for clave, frase in posiciones.items():
            estado = f"{contexto} Situación actual: Tienes {float(balas)} balas. {frase}"
            eleccion = modelo.predict(state=estado, questions=preguntas)["answers"]["accion"]["choice"]
            if es_correcta(clave, eleccion, balas):
                aciertos[clave] += 1
                fila.append("  ✓  " if clave != "NADA" else f" {eleccion[:4]}✓")
            else:
                fila.append(f" {eleccion[:4]}")
        print(f"  {balas:2d}  | " + " | ".join(fila))
    print("Aciertos -> " + ", ".join(f"{c}: {n}/{len(municiones)}" for c, n in aciertos.items()))

    estado = f"{contexto} Situación actual: Tienes 20.0 balas. {frase_nada}"
    probs = modelo.predict(state=estado, questions=preguntas)["answers"]["accion"]["probabilities"]
    print("Probabilidades NADA (20 balas): " + ", ".join(f"{k}: {v:.2f}" for k, v in probs.items()))
