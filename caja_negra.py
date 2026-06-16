import cv2
import os
import time
from collections import deque

class CajaNegra:
    def __init__(self, max_frames=15):
        # deque funciona como una memoria circular: si se llena, borra el más viejo
        self.buffer = deque(maxlen=max_frames) 
        self.carpeta = "Dataset_Fallos"
        
        # Crea la carpeta si no existe
        if not os.path.exists(self.carpeta):
            os.makedirs(self.carpeta)
            print(f"📁 Carpeta '{self.carpeta}' creada para guardar evidencias.")

    def registrar_frame(self, frame):
        """Guarda temporalmente el frame actual en la memoria RAM."""
        self.buffer.append(frame)

    def guardar_evidencia(self, razon="Error_IA"):
        """Vuelca la memoria RAM al disco duro cuando ocurre un desastre."""
        if len(self.buffer) == 0:
            return

        print(f"🚨 CAJA NEGRA ACTIVADA: Guardando últimos {len(self.buffer)} frames...")
        print(f"Motivo: {razon}")
        
        timestamp = int(time.time())
        for i, frame in enumerate(self.buffer):
            # Guardamos la imagen en formato BGR limpio para LabelImg
            nombre_archivo = f"{self.carpeta}/fallo_{timestamp}_f{i}.jpg"
            cv2.imwrite(nombre_archivo, frame)
            
        print(f"✅ Evidencia guardada en la carpeta '{self.carpeta}'.")
        # Vaciamos la memoria para el siguiente intento
        self.buffer.clear()