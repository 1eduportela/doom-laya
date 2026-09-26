import time
import torch
from laya.agent import Agent

print("Cargando LAYA (PyTorch)...")
agent = Agent("convaiinnovations/laya", compile=False, device="cpu")

# Datos de ejemplo (solo para que el exportador vea los tipos de datos)
entradas = (
    torch.randint(0, 100, (1, 16), dtype=torch.long),   # input_ids
    torch.ones((1, 16), dtype=torch.long),              # attention_mask
    torch.tensor([[1, 5]], dtype=torch.long),           # marker_pos
    torch.tensor([[True, True]], dtype=torch.bool),     # marker_mask
    torch.tensor([0], dtype=torch.long),                # qtype
)

# Dimensiones VARIABLES: la longitud del texto y el numero de opciones
longitud = torch.export.Dim("seq_len", min=4, max=8192)
opciones = torch.export.Dim("num_markers", min=2, max=256)
formas_dinamicas = {
    "input_ids": {1: longitud},
    "attention_mask": {1: longitud},
    "marker_pos": {1: opciones},
    "marker_mask": {1: opciones},
    "qtype": None,
}

print("Exportando a ONNX con el exportador nuevo (puede tardar unos minutos)...")
inicio = time.perf_counter()
torch.onnx.export(
    agent.model,
    entradas,
    "models/laya_fp32.onnx",
    input_names=["input_ids", "attention_mask", "marker_pos", "marker_mask", "qtype"],
    output_names=["logits", "act_logits"],
    dynamic_shapes=formas_dinamicas,
    dynamo=True,
    opset_version=18,
)
print(f"Listo en {time.perf_counter() - inicio:.0f} s -> models/laya_fp32.onnx")
