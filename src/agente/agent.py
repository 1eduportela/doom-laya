import laya
import time
from laya.onnx_agent import ONNXAgent

# Elige el modelo: "original" o el nombre de un archivo models/laya_<nombre>.onnx
# ("fp32", "int8", "int8_pc", "w8", "w8_acc4", ...)
MODELO = "w8_acc4"

# Opcion de LAYA -> accion del juego (0 = girar izq, 1 = girar der, 2 = disparar)
ACCIONES = {
    "IZQUIERDA": 0,
    "DERECHA": 1,
    "DISPARAR": 2,
    "BUSCAR": 1,   # buscar = girar siempre hacia el mismo lado
}

class DoomAgent:
    def __init__(self):
        print(f"Cargando cerebro ({MODELO})...")
        if MODELO == "original":
            self.modelo = laya.load("convaiinnovations/laya")
        else:
            self.modelo = ONNXAgent("convaiinnovations/laya", onnx_path=f"models/laya_{MODELO}.onnx")

        self.contexto = (
            "Eres un agente de IA jugando a DOOM. "
            "Tu objetivo es sobrevivir y eliminar la amenaza. "
            "Si tienes munición y un enemigo delante, dispara. "
            "Si te quedas sin munición o necesitas buscar, muévete a los lados."
        )

        self.formato_respuesta = {
            "accion": {
                "instructions": "¿Qué acción ejecuto?",
                "type": "choice",
                "criteria": list(ACCIONES.keys())
            }
        }

        # Memoria: (posicion, municion) -> accion
        self.cache = {}

    def decidir_accion(self, estado_juego):
        if estado_juego is None:
            return 0

        municion_actual = estado_juego["municion"]
        posicion_enemigo = estado_juego["posicion_enemigo"]

        clave = (posicion_enemigo, municion_actual)
        if clave in self.cache:
            return self.cache[clave]

        estado_completo = f"{self.contexto} Situación actual: Tienes {municion_actual} balas. {posicion_enemigo}"

        inicio = time.perf_counter()
        resultado = self.modelo.predict(
            state=estado_completo,
            questions=self.formato_respuesta
        )
        duracion = time.perf_counter() - inicio

        accion_elegida = resultado["answers"]["accion"]["choice"]
        print(f"   [LAYA pensó {duracion:.2f} s] {posicion_enemigo} -> {accion_elegida}")

        accion = ACCIONES.get(accion_elegida, 0)
        self.cache[clave] = accion
        return accion
