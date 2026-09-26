import sys
import time
import laya
from laya.onnx_agent import ONNXAgent

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
        "criteria": ["IZQUIERDA", "DERECHA", "DISPARAR", "BUSCAR"]
    }
}
posiciones = {
    "IZQ": ("El enemigo está a la IZQUIERDA.", {"IZQUIERDA"}),
    "DER": ("El enemigo está a la DERECHA.", {"DERECHA"}),
    "DEL": ("El enemigo está JUSTO DELANTE.", {"DISPARAR"}),
    "NADA": ("No hay enemigos a la vista, hay que BUSCAR.", {"IZQUIERDA", "DERECHA", "BUSCAR"}),
}

todos = {
    "original": lambda: laya.load("convaiinnovations/laya"),
    "onnx_fp32": lambda: ONNXAgent("convaiinnovations/laya", onnx_path="models/laya_fp32.onnx"),
    "onnx_int8": lambda: ONNXAgent("convaiinnovations/laya", onnx_path="models/laya_int8.onnx"),
    "onnx_int8_pc": lambda: ONNXAgent("convaiinnovations/laya", onnx_path="models/laya_int8_pc.onnx"),
}

# Uso: python src/test_municion.py onnx_int8 onnx_int8_pc
elegidos = sys.argv[1:] or list(todos)

for nombre in elegidos:
    modelo = todos[nombre]() if nombre in todos else ONNXAgent("convaiinnovations/laya", onnx_path=f"models/laya_{nombre}.onnx")
    print(f"\n=== {nombre} ===")
    print("Balas |  IZQ  |  DER  |  DEL  | NADA")
    aciertos_apuntar = 0
    aciertos_nada = 0
    inicio = time.perf_counter()
    for balas in range(26, 0, -1):   # de 26 a 1 (con balas)
        fila = []
        for clave, (frase, correctas) in posiciones.items():
            estado = f"{contexto} Situación actual: Tienes {float(balas)} balas. {frase}"
            eleccion = modelo.predict(state=estado, questions=preguntas)["answers"]["accion"]["choice"]
            if eleccion in correctas:
                fila.append("  ✓  ")
                if clave == "NADA":
                    aciertos_nada += 1
                else:
                    aciertos_apuntar += 1
            else:
                fila.append(f" {eleccion[:4]}")
        print(f"  {balas:2d}  | " + " | ".join(fila))
    print(f"Apuntar: {aciertos_apuntar}/78 | Buscar: {aciertos_nada}/26 | {time.perf_counter() - inicio:.0f} s")
    del modelo
