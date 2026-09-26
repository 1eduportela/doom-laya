import os
import time
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

entrada = "models/laya_fp32.onnx"
limpio = "models/laya_fp32_limpio.onnx"
salida = "models/laya_int8_pc.onnx"

print("Limpiando anotaciones de tamaños...")
modelo = onnx.load(entrada)
del modelo.graph.value_info[:]
onnx.save(modelo, limpio)

print("Cuantizando a 8 bits POR CANAL...")
inicio = time.perf_counter()
quantize_dynamic(model_input=limpio, model_output=salida,
                 weight_type=QuantType.QInt8, per_channel=True)
os.remove(limpio)
print(f"Listo en {time.perf_counter() - inicio:.0f} s")
print(f"Tamaño: {os.path.getsize(salida) / 1e6:.0f} MB")
