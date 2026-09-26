import os
import time
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

entrada = "models/laya_fp32.onnx"
limpio = "models/laya_fp32_limpio.onnx"
salida = "models/laya_int8.onnx"

print("Limpiando anotaciones de tamaños...")
modelo = onnx.load(entrada)
del modelo.graph.value_info[:]
onnx.save(modelo, limpio)

print("Cuantizando a 8 bits...")
inicio = time.perf_counter()
quantize_dynamic(model_input=limpio, model_output=salida, weight_type=QuantType.QInt8)
os.remove(limpio)
print(f"Listo en {time.perf_counter() - inicio:.0f} s")

mb_antes = os.path.getsize(entrada) / 1e6
mb_despues = os.path.getsize(salida) / 1e6
print(f"Tamaño: {mb_antes:.0f} MB -> {mb_despues:.0f} MB ({mb_antes / mb_despues:.1f} veces menos)")
