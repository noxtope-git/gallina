import cv2
import numpy as np
import pyautogui
from ultralytics import YOLO

class VisionController:
    def __init__(self):
        # Carga tu nuevo cerebro de 7 clases
        self.model = YOLO("best.pt")

    def capture_screen(self):
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame

    def get_object_positions(self, frame):
        # Mantenemos la confianza estricta para evitar falsos positivos
        results = self.model(frame, conf=0.4, verbose=False)[0]
        
        chicken_pos = None
        fire_pos = []
        threat_pos = []
        game_state = "playing" # Estado por defecto
        
        for box in results.boxes:
            cls_id = int(box.cls[0].item())
            x_c, y_c, w, h = box.xywh[0].tolist()
            b_box = (int(x_c - w/2), int(y_c - h/2), int(w), int(h))
            
            # --- EL NUEVO MAPA DE 7 CLASES ---
            if cls_id == 0: chicken_pos = b_box
            elif cls_id == 1: threat_pos.append(b_box)
            elif cls_id == 2: fire_pos.append(b_box)
            elif cls_id == 3: game_state = "victory"
            elif cls_id == 4: game_state = "dead_squashed"
            elif cls_id == 5: game_state = "dead_burnt"
            elif cls_id == 6: game_state = "dead_hole"
            
        return chicken_pos, fire_pos, threat_pos, game_state