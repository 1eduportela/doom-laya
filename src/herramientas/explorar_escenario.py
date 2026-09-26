import os
import vizdoom as vzd

ESCENARIO = "defend_the_center"

game = vzd.DoomGame()
ruta = os.path.join(os.path.dirname(vzd.__file__), "scenarios")
game.load_config(os.path.join(ruta, f"{ESCENARIO}.cfg"))
game.set_labels_buffer_enabled(True)
game.set_window_visible(False)
game.init()

print(f"=== Escenario: {ESCENARIO} ===")
print("Botones (en este orden):", [b.name for b in game.get_available_buttons()])
print("Variables:", [v.name for v in game.get_available_game_variables()])
print("Resolución:", game.get_screen_width(), "x", game.get_screen_height())
print("Duración máxima (tics):", game.get_episode_timeout())

girar_derecha = [0, 1, 0]
disparar = [0, 0, 1]

objetos_vistos = {}
salud_anterior = game.get_game_variable(vzd.GameVariable.HEALTH)
turno = 0

while not game.is_episode_finished():
    estado = game.get_state()

    for obj in estado.labels:
        nombre = obj.object_name
        objetos_vistos[nombre] = objetos_vistos.get(nombre, 0) + 1

    # Cada 5 turnos mostramos que hay en pantalla
    if turno % 5 == 0:
        en_pantalla = [f"{o.object_name}(x={o.x + o.width / 2:.0f}, ancho={o.width})" for o in estado.labels]
        print(f"Turno {turno:03d}: {en_pantalla}")

    accion = disparar if turno % 3 == 0 else girar_derecha
    game.make_action(accion, 4)

    salud = game.get_game_variable(vzd.GameVariable.HEALTH)
    if salud < salud_anterior:
        print(f"   ¡Daño en el turno {turno}! Salud: {salud_anterior:.0f} -> {salud:.0f}")
    salud_anterior = salud
    turno += 1

print(f"\n=== Partida terminada en {turno} turnos ===")
print("Munición final:", game.get_game_variable(vzd.GameVariable.AMMO2))
print("¿Muerto?:", game.is_player_dead())
print("Recompensa total:", game.get_total_reward())
print("\nObjetos vistos (nombre: veces):")
for nombre, veces in sorted(objetos_vistos.items(), key=lambda x: -x[1]):
    print(f"   {nombre}: {veces}")

game.close()
