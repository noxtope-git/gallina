import os
import sys
import cv2
import numpy as np
import pyautogui

class ButtonDetector:
    def __init__(self, ruta_base="."):
        self.ruta_base = ruta_base
        self.plantillas_dir = self._ruta_plantillas()
        os.makedirs(self.plantillas_dir, exist_ok=True)

        self.fallback_apostar = (660, 450)
        self.fallback_avanzar = (661, 524)

        self.btn_apostar = self.fallback_apostar
        self.btn_avanzar = self.fallback_avanzar

        self.plantilla_apostar = self._cargar_plantilla("apostar.png")
        self.plantilla_avanzar = self._cargar_plantilla("avanzar.png")

    def _ruta_plantillas(self):
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = self.ruta_base
        return os.path.join(base, "assets", "plantillas")

    def _cargar_plantilla(self, nombre):
        ruta = os.path.join(self.plantillas_dir, nombre)
        if os.path.exists(ruta):
            return cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
        return None

    def calibrar(self):
        faltan = []
        if self.plantilla_apostar is None:
            faltan.append(("apostar.png", *self.fallback_apostar))
        if self.plantilla_avanzar is None:
            faltan.append(("avanzar.png", *self.fallback_avanzar))

        if not faltan:
            return

        print("📷 Calibrando botones por primera vez...")
        for nombre, x, y in faltan:
            try:
                screenshot = pyautogui.screenshot(region=(x - 20, y - 20, 40, 40))
                ruta = os.path.join(self.plantillas_dir, nombre)
                screenshot.save(ruta)
                print(f"  {nombre} guardada en ({x}, {y})")
            except Exception as e:
                print(f"  Error capturando {nombre}: {e}")

        self.plantilla_apostar = self._cargar_plantilla("apostar.png")
        self.plantilla_avanzar = self._cargar_plantilla("avanzar.png")

    def encontrar_botones(self):
        pos_apostar = self._encontrar(self.plantilla_apostar)
        pos_avanzar = self._encontrar(self.plantilla_avanzar)

        if pos_apostar:
            self.btn_apostar = pos_apostar
        if pos_avanzar:
            self.btn_avanzar = pos_avanzar

        return self.btn_apostar, self.btn_avanzar

    def _encontrar(self, plantilla, umbral=0.7):
        if plantilla is None:
            return None
        try:
            screenshot = pyautogui.screenshot()
            pantalla = np.array(screenshot)
            pantalla_gray = cv2.cvtColor(pantalla, cv2.COLOR_RGB2GRAY)

            resultado = cv2.matchTemplate(pantalla_gray, plantilla, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(resultado)

            if max_val >= umbral:
                h, w = plantilla.shape
                return (max_loc[0] + w // 2, max_loc[1] + h // 2)
        except Exception as e:
            print(f"Error en template matching: {e}")
        return None
