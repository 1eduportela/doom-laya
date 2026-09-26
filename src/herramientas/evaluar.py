import time
import statistics
from src.entorno.environment import DoomEnvironment
from src.agente.agent import DoomAgent

ESCENARIO = "defend_the_center"
PARTIDAS = 5
TOLERANCIAS = [2, 5]

entorno = DoomEnvironment(ESCENARIO)
agente = DoomAgent()

resumen = {}

for tol in TOLERANCIAS:
    entorno.tolerancia_min = tol
    print(f"\n===== Tolerancia mínima: {tol} px =====")
    muertes_lista, turnos_lista, precision_lista = [], [], []

    for i in range(PARTIDAS):
        entorno.reiniciar_partida()
        municion_inicial, _ = entorno.leer_variables()
        turnos = 0
        inicio = time.perf_counter()

        while not entorno.esta_terminado():
            estado = entorno.obtener_estado()
            accion = agente.decidir_accion(estado)
            entorno.ejecutar_accion(accion)
            turnos += 1

        muertes = entorno.leer_muertes()
        municion_final, _ = entorno.leer_variables()
        balas = municion_inicial - municion_final
        precision = muertes / balas if balas > 0 else 0

        muertes_lista.append(muertes)
        turnos_lista.append(turnos)
        precision_lista.append(precision)
        print(f"Partida {i + 1}: {muertes:.0f} enemigos | {balas:.0f} balas | "
              f"acierto {precision:.0%} | {turnos} turnos | {time.perf_counter() - inicio:.0f} s")

    resumen[tol] = (statistics.mean(muertes_lista), statistics.mean(precision_lista),
                    statistics.mean(turnos_lista), min(muertes_lista), max(muertes_lista))

print("\n===== RESUMEN =====")
for tol, (m, p, t, mn, mx) in resumen.items():
    print(f"Tolerancia {tol} px: media {m:.1f} enemigos (entre {mn:.0f} y {mx:.0f}) | "
          f"acierto {p:.0%} | {t:.0f} turnos de media")
print(f"Llamadas totales a LAYA: {len(agente.cache)}")
entorno.cerrar()
