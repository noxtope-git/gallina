import os
import sys  
os.environ['KMP_DUPLICATE_LIB_OK']='True' 

import tkinter as tk
from tkinter import messagebox
from threading import Thread
import time
import pyautogui
import keyboard  
import shutil
import subprocess
import glob
import cv2 
import torch
from ultralytics import YOLO

from src.vision import VisionController
from src.logic import GameLogic
from src.caja_negra import CajaNegra
from src.botones import ButtonDetector

pyautogui.FAILSAFE = False 
pyautogui.PAUSE = 0.01

def obtener_ruta_base():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

RUTA_BASE = obtener_ruta_base()

def ruta_relativa(path):
    ruta = os.path.join(RUTA_BASE, path)
    if not os.path.exists(ruta) and getattr(sys, 'frozen', False):
        ruta = os.path.join(sys._MEIPASS, path)
    return ruta

def verificar_gpu():
    print("🔍 Verificando compatibilidad de hardware...")
    try:
        if not torch.cuda.is_available():
            print("╔══════════════════════════════════════════════════════╗")
            print("║     🚫 GPU NO COMPATIBLE DETECTADA                  ║")
            print("╠══════════════════════════════════════════════════════╣")
            print("║  No se detectó una GPU NVIDIA con CUDA.            ║")
            print("║  Este programa requiere una tarjeta gráfica        ║")
            print("║  NVIDIA compatible con CUDA para funcionar.        ║")
            print("╠══════════════════════════════════════════════════════╣")
            print("║  GPUs compatibles (lista no exhaustiva):           ║")
            print("║  • NVIDIA GeForce GTX 900 series en adelante       ║")
            print("║  • NVIDIA GeForce GTX 1000 series en adelante      ║")
            print("║  • NVIDIA GeForce RTX 2000 series en adelante      ║")
            print("║  • NVIDIA Quadro P series en adelante              ║")
            print("╠══════════════════════════════════════════════════════╣")
            print("║  Si tienes una GPU compatible, actualiza tus       ║")
            print("║  drivers e instala CUDA Toolkit desde:             ║")
            print("║  https://developer.nvidia.com/cuda-downloads        ║")
            print("╚══════════════════════════════════════════════════════╝")
            sys.exit(1)

        gpu_name = torch.cuda.get_device_name(0)
        gpu_ver = torch.version.cuda
        print(f"✅ GPU Detectada: {gpu_name}")
        print(f"✅ CUDA Version: {gpu_ver}")
        print("✅ Hardware compatible. Iniciando programa...\n")
    except Exception as e:
        print(f"⚠ Error al verificar GPU: {e}")
        sys.exit(1)

class AppUI:
    def __init__(self):
        try:
            self.vision = VisionController(ruta_base=RUTA_BASE)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el modelo YOLO:\n{e}")
            sys.exit(1)
        self.logic = GameLogic()
        self.caja_negra = CajaNegra(max_frames=8, ruta_base=RUTA_BASE)
        self.detector = ButtonDetector(ruta_base=RUTA_BASE)
        self.detector.calibrar()
        
        self.running = True
        self.auto_play = False
        self.solo_jugar = False
        self.frames_perdidos = 0 
        self.entrenando = False 
        
        # --- UMBRAL DE AUTO-ENTRENAMIENTO ---
        self.FOTOS_PARA_EVOLUCIONAR = 30 
        
        self.root = tk.Tk()
        self.setup_gui()
        
        self.thread = Thread(target=self.run_bot, daemon=True)
        self.thread.start()
        self.root.mainloop()

    def setup_gui(self):
        self.root.title("Gallina AI - Skynet Loop")
        self.root.attributes("-topmost", True)
        self.root.geometry("250x230+10+10") 
        
        self.lbl_status = tk.Label(self.root, text="INICIANDO...", font=("Arial", 16, "bold"))
        self.lbl_status.pack(pady=5)
        
        self.lbl_reason = tk.Label(self.root, text="Ctrl+Ñ para Activar/Pausar", font=("Arial", 10))
        self.lbl_reason.pack()
        
        self.lbl_nivel = tk.Label(self.root, text="Pasos: 0 | Confianza: 0.65 | Win: 0%", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_nivel.pack(pady=2)
        
        self.btn_auto = tk.Button(self.root, text="AUTO-PLAY: OFF", command=self.toggle_auto, bg="orange", fg="white", font=("Arial", 10, "bold"))
        self.btn_auto.pack(pady=5)

        self.btn_solo = tk.Button(self.root, text="🎮 SOLO JUGAR: OFF", command=self.toggle_solo, bg="gray", fg="white", font=("Arial", 10, "bold"))
        self.btn_solo.pack(pady=5)

        self.btn_train = tk.Button(self.root, text="🔥 ENTRENAR IA 🔥", command=self.lanzar_entrenamiento, bg="purple", fg="white", font=("Arial", 10, "bold"))
        self.btn_train.pack(pady=5)

    def toggle_auto(self):
        if self.entrenando:
            print("⏳ Espera, la IA se está entrenando...")
            return
            
        self.auto_play = not self.auto_play
        self.btn_auto.config(text=f"AUTO-PLAY: {'ON' if self.auto_play else 'OFF'}", 
                             bg="#2ECC71" if self.auto_play else "orange")

    def toggle_solo(self):
        if self.entrenando:
            print("⏳ Espera, la IA se está entrenando...")
            return

        self.solo_jugar = not self.solo_jugar
        self.btn_solo.config(
            text=f"🎮 SOLO JUGAR: {'ON' if self.solo_jugar else 'OFF'}",
            bg="#2ECC71" if self.solo_jugar else "gray"
        )
        if self.solo_jugar:
            print("🎮 Modo Solo Jugar activado: sin capturas ni auto-entrenamiento")

    def lanzar_entrenamiento(self):
        if self.entrenando: return
        self.entrenando = True
        
        # Guardamos el estado anterior para reanudar automáticamente
        self.reaundar_al_terminar = self.auto_play
        if self.auto_play: self.toggle_auto() 
        
        Thread(target=self.proceso_entrenamiento_magico, daemon=True).start()

    def ruta_script(self, nombre):
        return ruta_relativa(os.path.join("scripts", nombre))

    def proceso_entrenamiento_magico(self):
        self.btn_train.config(text="ENTRENANDO...", bg="red", state=tk.DISABLED)
        self.lbl_status.config(text="ACTUALIZANDO CEREBRO", fg="red")

        try:
            import subprocess, sys
            python_exe = sys.executable

            print("\n🦖 1. Llamando al Profesor DINO (Etiquetado Automático)...")
            subprocess.run([python_exe, self.ruta_script("etiquetador_dino.py")], check=True)

            print("\n🧹 2. Fusionando y limpiando Dataset de Fallos...")
            subprocess.run([python_exe, self.ruta_script("fusionar_dino.py")], check=True)

            print("\n🔥 3. Encendiendo motores RTX (Entrenamiento YOLOv8)...")
            subprocess.run([python_exe, self.ruta_script("entrenar.py")], check=True)

            print("\n🔍 4. Buscando el nuevo cerebro generado...")
            carpetas_train = glob.glob(ruta_relativa('runs/detect/train*'))
            if carpetas_train:
                ultima_carpeta = max(carpetas_train, key=os.path.getctime)
                ruta_nuevo_best = os.path.join(ultima_carpeta, 'weights', 'best.pt')

                if os.path.exists(ruta_nuevo_best):
                    shutil.copy(ruta_nuevo_best, ruta_relativa("best.pt"))
                    print(f"✅ Nuevo best.pt copiado con éxito desde: {ultima_carpeta}")

                    print("\n⚡ 5. Recargando IA en memoria (Hot-Swap)...")
                    self.vision.model = YOLO(ruta_relativa("best.pt"))
                    print("🎉 ¡PROCESO COMPLETADO! IA más inteligente lista para jugar.")
                else:
                    print("❌ No se encontró el archivo best.pt.")

        except Exception as e:
            print(f"❌ Error CRÍTICO en el proceso de entrenamiento: {e}")

        finally:
            self.btn_train.config(text="🔥 ENTRENAR IA 🔥", bg="purple", state=tk.NORMAL)
            self.lbl_status.config(text="LISTO PARA JUGAR", fg="white")
            self.entrenando = False
            
            # --- AUTO-REANUDACIÓN ---
            if self.reaundar_al_terminar and not self.auto_play:
                print("▶️ Reanudando Auto-Play tras evolución...")
                self.toggle_auto()

    def pipeline_retroalimentacion(self, motivo_finalizacion):
        try:
            timestamp = int(time.time())
            carpeta_temporal = f"temp_ronda_{timestamp}"
            
            print(f"📸 Guardando evidencia RAW para DINO ({motivo_finalizacion})...")
            self.caja_negra.guardar_evidencia(carpeta_temporal)
            time.sleep(1.5)
            
            dataset_fallos = ruta_relativa("Dataset_Fallos")
            opcion_subcarpeta = os.path.join(dataset_fallos, carpeta_temporal)
            ruta_origen = opcion_subcarpeta if os.path.exists(opcion_subcarpeta) else (carpeta_temporal if os.path.exists(carpeta_temporal) else None)
                
            if not ruta_origen: return
                
            archivos = os.listdir(ruta_origen)
            imagenes_a_procesar = [f for f in archivos if f.endswith(('.jpg', '.png'))]
            
            for img_name in imagenes_a_procesar:
                img_path = os.path.join(ruta_origen, img_name)
                nombre_final = f"{motivo_finalizacion}_{timestamp}_{img_name}"
                ruta_destino = os.path.join(dataset_fallos, nombre_final)
                shutil.move(img_path, ruta_destino)
                
            shutil.rmtree(ruta_origen)
            print(f"📦 {len(imagenes_a_procesar)} fotos de '{motivo_finalizacion}' listas en la sala de espera para DINO.")
            
        except Exception as e:
            print(f"❌ Error al recolectar fotos para DINO: {e}")

    def comprobar_auto_evolucion(self):
        if self.entrenando: return
        try:
            dataset_fallos = ruta_relativa("Dataset_Fallos")
            if not os.path.exists(dataset_fallos): return
            archivos = [f for f in os.listdir(dataset_fallos) if f.endswith('.jpg')]
            if len(archivos) >= self.FOTOS_PARA_EVOLUCIONAR:
                print(f"🤖 SKYNET PROTOCOL: Se acumularon {len(archivos)} imágenes. Iniciando Auto-Evolución...")
                self.lanzar_entrenamiento()
        except Exception as e:
            pass

    def run_bot(self):
        ultimo_chequeo_evolucion = time.time()
        
        while self.running:
            try:
                if keyboard.is_pressed('ctrl+ñ') and not self.entrenando:
                    self.toggle_auto()
                    time.sleep(0.6) 

                if keyboard.is_pressed('f9') and not self.entrenando:
                    frame_manual = self.vision.capture_screen()
                    timestamp = int(time.time())
                    ruta_img = os.path.join(ruta_relativa("Dataset_Fallos"), f"manual_inicio_{timestamp}.jpg")
                    cv2.imwrite(ruta_img, frame_manual)
                    with open(ruta_img.replace('.jpg', '.txt'), 'w') as f: pass 
                    print(f"📸 ¡FOTO MANUAL CAPTURADA!")
                    time.sleep(1) 

                if self.entrenando:
                    time.sleep(1) 
                    continue

                # --- NUEVO: LAS CÁMARAS SOLO GRABAN SI ESTÁ JUGANDO ---
                if self.auto_play:
                    frame = self.vision.capture_screen()
                    if not self.solo_jugar:
                        self.caja_negra.registrar_frame(frame)
                    
                    btn_apostar, btn_avanzar = self.detector.encontrar_botones()
                    self.logic.actualizar_coordenadas(btn_apostar=btn_apostar, btn_avanzar=btn_avanzar)

                    chicken_pos, fire_pos, threat_pos, game_state = self.vision.get_object_positions(frame)
                    main_txt, sub_txt, main_col, sub_col, is_ready, click_x, click_y, _, _ = self.logic.analyze_situation(chicken_pos, fire_pos, threat_pos, game_state)
                    
                    self.root.after(0, self.lbl_status.config, {"text": main_txt, "fg": main_col})
                    self.root.after(0, self.lbl_reason.config, {"text": sub_txt, "fg": sub_col})
                    self.root.after(0, self.lbl_nivel.config, {"text": f"Pasos: {self.logic.pasos_dados} | Riesgo: {round(self.logic.tolerancia_riesgo, 2)} | Win: {self.logic.obtener_winrate()}%"})

                    if is_ready and click_x is not None:
                        pyautogui.click(x=click_x, y=click_y)
                        
                        if "RETIRANDO" in main_txt:
                            print("💰 Presionando botón de retiro de ganancias...")
                            self.logic.registrar_resultado(victoria=True) 
                            self.logic.resetear_pasos() 
                            time.sleep(0.5) 
                            
                        elif "VICTORIA CONFIRMADA" in main_txt:
                            print("🔄 YOLO vio el cartel de victoria. Iniciando nueva partida.")
                            self.logic.last_bet_time = time.time() 
                            time.sleep(1.0) 
                            
                        elif "COLISIÓN CONFIRMADA" in main_txt:
                            motivo_muerte = f"muerte_{self.logic.ultimo_peligro_visto}"
                            print(f"💀 YOLO vio el Game Over ({self.logic.ultimo_peligro_visto}). Reiniciando.")
                            self.logic.registrar_resultado(victoria=False)
                            if not self.solo_jugar:
                                Thread(target=self.pipeline_retroalimentacion, args=(motivo_muerte,), daemon=True).start()
                            self.logic.resetear_pasos() 
                            self.logic.last_bet_time = time.time() 
                            time.sleep(1.0) 
                            
                        elif "NUEVA_PARTIDA" in main_txt:
                            self.logic.last_bet_time = time.time() 
                            time.sleep(1.0) 
                            
                        else:
                            time.sleep(0.60) 
                else:
                    # Interfaz en modo de espera y CPU descansando
                    self.root.after(0, self.lbl_status.config, {"text": "PAUSADO", "fg": "orange"})
                    self.root.after(0, self.lbl_reason.config, {"text": "Modo Standby...", "fg": "white"})
                    time.sleep(0.1)
                        
                # --- CHEQUEO PERIÓDICO DE AUTO-ENTRENAMIENTO (Cada 10 segundos) ---
                if not self.solo_jugar and time.time() - ultimo_chequeo_evolucion > 10.0 and self.logic.pasos_dados == 0:
                    self.comprobar_auto_evolucion()
                    ultimo_chequeo_evolucion = time.time()
                
                time.sleep(0.01) 
            except Exception as e:
                print(f"Error en loop principal: {e}")
                time.sleep(1)

if __name__ == "__main__":
    try:
        AppUI()
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERROR FATAL: {error_msg}")
        try:
            messagebox.showerror("Error Fatal", f"Ocurrió un error:\n{e}\n\nRevisa la consola para más detalles.")
        except:
            pass
        sys.exit(1)