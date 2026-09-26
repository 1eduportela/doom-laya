import os
import vizdoom as vzd

# Nombres de los monstruos en los escenarios que usamos
ENEMIGOS = {"Cacodemon", "MarineChainsawVzd", "Demon"}

class DoomEnvironment:
    def __init__(self, escenario="basic"):
        print(f"Iniciando el motor de DOOM (escenario: {escenario})...")
        self.game = vzd.DoomGame()
        ruta_escenarios = os.path.join(os.path.dirname(vzd.__file__), "scenarios")
        self.game.load_config(os.path.join(ruta_escenarios, f"{escenario}.cfg"))

        # Activamos la deteccion de objetos visuales
        self.game.set_labels_buffer_enabled(True)

        self.game.set_window_visible(False)
        self.game.set_render_hud(True)
        self.game.set_audio_buffer_enabled(True)
        self.game.set_audio_sampling_rate(vzd.SamplingRate.SR_22050)
        self.game.set_audio_buffer_size(4)
        self.game.init()
        print("Motor de DOOM listo.")

        self.centro_pantalla = self.game.get_screen_width() / 2
        self.cerca_del_centro = False
        self.ultimos_tics = 4
        self.tolerancia_min = 5

        self.acciones = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ]

    def ejecutar_accion(self, indice_accion):
        accion = self.acciones[indice_accion]
        # Giro fino (1 tic) si el enemigo esta cerca del centro; si no, 4 tics
        girando = indice_accion in (0, 1)
        tics = 1 if (girando and self.cerca_del_centro) else 4
        self.ultimos_tics = tics
        return self.game.make_action(accion, tics)

    def leer_variables(self):
        # Se leen por nombre: funciona en cualquier escenario y tambien tras actuar
        municion = self.game.get_game_variable(vzd.GameVariable.AMMO2)
        salud = self.game.get_game_variable(vzd.GameVariable.HEALTH)
        return municion, salud

    def leer_muertes(self):
        return self.game.get_game_variable(vzd.GameVariable.KILLCOUNT)

    def obtener_estado(self):
        estado = self.game.get_state()
        if estado is None:
            return None

        municion, salud = self.leer_variables()

        # Nos quedamos con los enemigos (ignoramos DoomPlayer, BulletPuff, Blood...)
        enemigos = [o for o in estado.labels if o.object_name in ENEMIGOS]

        if not enemigos:
            posicion_enemigo = "No hay enemigos a la vista, hay que BUSCAR."
            descripcion = "-"
            self.cerca_del_centro = False
        else:
            # El mas ancho en pantalla es el mas cercano
            enemigo = max(enemigos, key=lambda o: o.width)
            centro_x = enemigo.x + (enemigo.width / 2)
            desvio = centro_x - self.centro_pantalla   # negativo = izquierda

            # El punto de mira debe caer sobre el cuerpo: tolerancia = 1/4 del ancho
            tolerancia = max(enemigo.width / 4, self.tolerancia_min)

            if abs(desvio) <= tolerancia:
                posicion_enemigo = "El enemigo está JUSTO DELANTE."
            elif desvio < 0:
                posicion_enemigo = "El enemigo está a la IZQUIERDA."
            else:
                posicion_enemigo = "El enemigo está a la DERECHA."

            self.cerca_del_centro = abs(desvio) < 40
            descripcion = f"{enemigo.object_name}(ancho={enemigo.width}, desvío={desvio:+.0f})"

        return {
            "municion": municion,
            "salud": salud,
            "posicion_enemigo": posicion_enemigo,
            # Datos extra solo para mostrar en pantalla (LAYA no los ve)
            "num_enemigos": len(enemigos),
            "enemigo": descripcion,
        }

    def reiniciar_partida(self):
        self.game.new_episode()

    def esta_terminado(self):
        return self.game.is_episode_finished()

    def cerrar(self):
        self.game.close()
