import laya
import time

class DoomAgent:
    def __init__(self):
        print("Cargando cerebro...")
        self.modelo = laya.load("convaiinnovations/laya")
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
                "criteria": ["IZQUIERDA", "DERECHA", "DISPARAR"]
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

        if accion_elegida == "IZQUIERDA":
            accion = 0
        elif accion_elegida == "DERECHA":
            accion = 1
        elif accion_elegida == "DISPARAR":
            accion = 2
        else:
            accion = 0

        self.cache[clave] = accion
        return accion
