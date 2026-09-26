import time
from src.entorno.environment import DoomEnvironment
from src.agente.agent import DoomAgent

ESCENARIO = "defend_the_center"

def main():
    print("---INICIANDO SISTEMA---")
    entorno = DoomEnvironment(ESCENARIO)
    agente = DoomAgent()

    print("\n¡Comienza la partida!")
    turnos = 0
    recompensa_total = 0
    inicio = time.perf_counter()

    nombres_acciones = ["IZQUIERDA", "DERECHA", "DISPARAR"]

    while not entorno.esta_terminado():
        estado = entorno.obtener_estado()
        accion = agente.decidir_accion(estado)
        recompensa = entorno.ejecutar_accion(accion)
        recompensa_total += recompensa

        # Leemos de nuevo DESPUES de actuar
        municion_despues, salud_despues = entorno.leer_variables()

        print(
            f"Turno {turnos:03d} | {nombres_acciones[accion]:9s} | "
            f"Munición: {estado['municion']:.0f} -> {municion_despues:.0f} | "
            f"Salud: {estado['salud']:.0f} -> {salud_despues:.0f} | "
            f"Enemigos: {estado['num_enemigos']} (objetivo: {estado['enemigo']}) | "
            f"Recompensa: {recompensa:+.0f}"
        )
        turnos += 1

    duracion = time.perf_counter() - inicio
    municion_final, salud_final = entorno.leer_variables()

    print("\n---PARTIDA TERMINADA---")
    print(f"Turnos sobrevividos: {turnos}")
    print(f"Enemigos eliminados: {entorno.leer_muertes():.0f}")
    print(f"Munición final: {municion_final:.0f} | Salud final: {salud_final:.0f}")
    print(f"Recompensa total: {recompensa_total:.0f}")
    print(f"Llamadas a LAYA: {len(agente.cache)} | Tiempo de juego: {duracion:.1f} s")
    entorno.cerrar()

if __name__ == "__main__":
    main()
