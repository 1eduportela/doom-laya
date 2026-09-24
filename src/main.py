from environment import DoomEnvironment
from agent import DoomAgent
import time

def main():
	print("---INICIANDO SISTEMA---")
	entorno=DoomEnvironment()
	agente=DoomAgent()

	print("\n¡Comienza la partida!")
	turnos=0

	nombres_acciones = ["MOVER IZQUIERDA", "MOVER DERECHA", "DISPARAR"]

	while not entorno.esta_terminado():
		estado=entorno.obtener_estado()
		accion=agente.decidir_accion(estado)
		recompensa=entorno.ejecutar_accion(accion)
		print(f"Turno {turnos:03d} | Municion: {estado['municion']} | Acción elegida: {nombres_acciones[accion]} | Recompensa: {recompensa}")
		turnos+=1
	print("\n---PARTIDA TERMINADA---")
	entorno.cerrar()

if __name__=="__main__":
	main()
