import laya

modelo = laya.load("convaiinnovations/laya")

escenas = {
    "LEFT":  "The monster is on the left side of my screen, not in front of my gun.",
    "RIGHT": "The monster is on the right side of my screen, not in front of my gun.",
    "AHEAD": "The monster is exactly in the center of my screen, right in front of my gun.",
    "NONE":  "I cannot see any monster on my screen.",
}

opciones = [
    "Turn left",
    "Turn right",
    "Shoot",
]

def probar(nombre, crear_estado, crear_instruccion):
    print(f"\n=== Version {nombre} ===")
    for real, escena in escenas.items():
        preguntas = {
            "action": {
                "instructions": crear_instruccion(escena),
                "type": "choice",
                "criteria": opciones
            }
        }
        r = modelo.predict(state=crear_estado(escena), questions=preguntas)
        a = r["answers"]["action"]
        probs = ", ".join(f"{k}: {v:.2f}" for k, v in a["probabilities"].items())
        print(f"{real:6s} -> {a['choice']:12s} | {probs}")

# C: solo la escena, sin reglas
probar(
    "C (escena sin reglas)",
    lambda escena: f"I am playing DOOM and I have ammo. {escena}",
    lambda escena: "What should I do to aim at the monster and kill it?"
)

# D: la escena dentro de la pregunta
probar(
    "D (escena en la pregunta)",
    lambda escena: "I am playing DOOM and I have ammo.",
    lambda escena: f"{escena} What should I do to aim at the monster and kill it?"
)
