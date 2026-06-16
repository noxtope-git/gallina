import torch
from ultralytics import YOLO
import os

# 1. Ver si la gráfica responde
print(f"¿Pytorch ve la GPU?: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Gráfica detectada: {torch.cuda.get_device_name(0)}")

# 2. Intentar cargar el modelo
print("Intentando cargar best.pt...")
if os.path.exists("best.pt"):
    try:
        model = YOLO("best.pt")
        print("✅ ¡LOGRADO! El modelo carga perfecto.")
    except Exception as e:
        print(f"❌ Error al cargar: {e}")
else:
    print("❌ No encuentro el archivo best.pt al lado de este script.")