import laya

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

    def decidir_accion(self, estado_juego):
        if estado_juego is None:
            return 0

        municion_actual = estado_juego["municion"]
        posicion_enemigo = estado_juego["posicion_enemigo"]
        
        # --- NUEVO: La situación cambia dinámicamente en cada turno ---
        estado_completo = f"{self.contexto} Situación actual: Tienes {municion_actual} balas. {posicion_enemigo}"
        
        resultado = self.modelo.predict(
            state=estado_completo,
            questions=self.formato_respuesta
        )
        
        accion_elegida = resultado["answers"]["accion"]["choice"]
        
        if accion_elegida == "IZQUIERDA":
            return 0
        elif accion_elegida == "DERECHA":
            return 1
        elif accion_elegida == "DISPARAR":
            return 2
        else:
            return 0
