import laya
import inspect

modelo = laya.load("convaiinnovations/laya")
print("\n--- SECRETO REVELADO ---")
print("Variables que acepta predict:", inspect.signature(modelo.predict))
