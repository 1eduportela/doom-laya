import os
import vizdoom as vzd

class DoomEnvironment:
    def __init__(self):
        print("Iniciando el motor de DOOM...")
        self.game = vzd.DoomGame()
        ruta_escenarios = os.path.join(os.path.dirname(vzd.__file__), "scenarios")
        self.game.load_config(os.path.join(ruta_escenarios, "basic.cfg"))
        
        # --- NUEVO: Activamos la detección de objetos visuales ---
        self.game.set_labels_buffer_enabled(True)
        
        self.game.set_window_visible(False)
        self.game.init()
        print("Motor de DOOM listo.")
        
        self.acciones = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ]

    def ejecutar_accion(self, indice_accion):
        accion = self.acciones[indice_accion]
        return self.game.make_action(accion)

    def obtener_estado(self):
        estado = self.game.get_state()
        if estado is None:
            return None
            
        municion = estado.game_variables[0]
        
        # --- NUEVO: Buscamos al enemigo en la pantalla ---
        posicion_enemigo = "No hay enemigos a la vista."
        
        if estado.labels:
            for objeto in estado.labels:
                # El monstruo en este escenario se llama Cacodemon
                if objeto.object_name == "Cacodemon":
                    centro_x = objeto.x + (objeto.width / 2)
                    
                    if centro_x < 140:
                        posicion_enemigo = "El enemigo está a la IZQUIERDA."
                    elif centro_x > 180:
                        posicion_enemigo = "El enemigo está a la DERECHA."
                    else:
                        posicion_enemigo = "El enemigo está JUSTO DELANTE."

        return {
            "municion": municion,
            "posicion_enemigo": posicion_enemigo
        }

    def reiniciar_partida(self):
        self.game.new_episode()

    def esta_terminado(self):
        return self.game.is_episode_finished()

    def cerrar(self):
        self.game.close()
