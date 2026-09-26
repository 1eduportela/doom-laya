import os
import time
import onnx
from onnxruntime.quantization.matmul_nbits_quantizer import MatMulNBitsQuantizer

# nombre: (bits, accuracy_level)
variantes = {
    "w8": (8, None),       # activaciones en decimales (lo mas preciso)
    "w8_acc4": (8, 4),     # activaciones a 8 bits en bloques de 32
    "w4_acc4": (4, 4),     # pesos a 4 bits
}

for nombre, (bits, nivel) in variantes.items():
    print(f"\n=== {nombre} ===")
    inicio = time.perf_counter()
    modelo = onnx.load("models/laya_fp32.onnx")   # carga tambien el .onnx.data
    q = MatMulNBitsQuantizer(modelo, bits=bits, block_size=32,
                             is_symmetric=True, accuracy_level=nivel)
    q.process()
    salida = f"models/laya_{nombre}.onnx"
    q.model.save_model_to_file(salida, False)
    print(f"Listo en {time.perf_counter() - inicio:.0f} s | {os.path.getsize(salida) / 1e6:.0f} MB")
