import time
import os

class GameLogic:
    def __init__(self):
        self.LANE_WIDTH = 142 
        self.BTN_AVANZAR_X = 661 
        self.BTN_AVANZAR_Y = 524 
        self.BTN_RETIRAR_X = 660 
        self.BTN_RETIRAR_Y = 450 
        
        self.pasos_dados = 0
        self.total_partidas = 0
        self.total_victorias = 0
        
        self.llegadas_por_paso = {} 
        self.muertes_por_paso = {}  
        self.tolerancia_riesgo = 0.50 
        
        self.racha_retiros_seguros = 0
        self.ultimo_paso_retirado = 0

        self.last_bet_time = 0 
        self.BET_COOLDOWN = 4.0 
        self.fire_was_active = False
        self.last_fire_time = 0
        self.FIRE_COOLDOWN = 0.35 
        self.safe_since = None
        self.SAFETY_DELAY = 1.1 
        self.tiempo_llegada_paso = None
        self.LIMITE_PACIENCIA = 3.5  
        
        self.ultimo_peligro_visto = "desconocido"
        self.ultima_x_gallina = None
        self.x_inicial_gallina = None # <-- NUEVO: Punto de partida para medir distancias

    def resetear_pasos(self):
        self.pasos_dados = 0
        self.tiempo_llegada_paso = time.time()
        self.ultima_x_gallina = None
        self.x_inicial_gallina = None

    def registrar_resultado(self, victoria):
        self.total_partidas += 1
        if victoria:
            self.total_victorias += 1
            self.tolerancia_riesgo = min(0.75, self.tolerancia_riesgo + 0.01)
            
            if self.pasos_dados == self.ultimo_paso_retirado:
                self.racha_retiros_seguros += 1
            else:
                self.racha_retiros_seguros = 1
                self.ultimo_paso_retirado = self.pasos_dados
                
            print(f"💰 Victoria. Confianza sube a: {self.tolerancia_riesgo:.2f}")
        else:
            paso_del_fallo = self.pasos_dados + 1
            self.llegadas_por_paso[paso_del_fallo] = self.llegadas_por_paso.get(paso_del_fallo, 0) + 1
            self.muertes_por_paso[paso_del_fallo] = self.muertes_por_paso.get(paso_del_fallo, 0) + 1
            
            self.tolerancia_riesgo = max(0.35, self.tolerancia_riesgo - 0.02)
            self.racha_retiros_seguros = 0 
            print(f"💀 Muerte en el paso {paso_del_fallo}. Confianza baja a: {self.tolerancia_riesgo:.2f}")

        self.volcar_registro_estadistico()

    def volcar_registro_estadistico(self):
        try:
            with open("registro_ia.txt", "w") as f:
                f.write("=== REPORTE DEL CEREBRO DE LA IA ===\n")
                f.write(f"Partidas Totales: {self.total_partidas}\n")
                f.write(f"Victorias Totales: {self.total_victorias}\n")
                f.write(f"Winrate General: {self.obtener_winrate()}%\n")
                f.write(f"Tolerancia al Riesgo Actual: {self.tolerancia_riesgo:.2f}\n")
                f.write(f"Racha de retiros seguros: {self.racha_retiros_seguros} (en paso {self.ultimo_paso_retirado})\n\n")
                
                f.write("--- MAPA DE MORTALIDAD POR PASO ---\n")
                for paso in sorted(self.llegadas_por_paso.keys()):
                    llegadas = self.llegadas_por_paso.get(paso, 0)
                    muertes = self.muertes_por_paso.get(paso, 0)
                    prob_bayes = ((muertes + 1) / (llegadas + 2)) * 100
                    f.write(f"Paso {paso}: Llegó {llegadas} veces | Murió {muertes} veces | Mortalidad Bayesiana: {prob_bayes:.1f}%\n")
        except Exception as e:
            print(f"Error guardando registro: {e}")

    def obtener_winrate(self):
        if self.total_partidas == 0: return 0.0
        return round((self.total_victorias / self.total_partidas) * 100, 1)

    def decidir_siguiente_accion(self):
        siguiente_paso = self.pasos_dados + 1
        
        if self.racha_retiros_seguros >= 3 and self.pasos_dados == self.ultimo_paso_retirado:
            print("🦸‍♂️ IA Envalentonada: Rompiendo zona de confort. ¡Avanzando!")
            return False 
            
        llegadas = self.llegadas_por_paso.get(siguiente_paso, 0)
        muertes = self.muertes_por_paso.get(siguiente_paso, 0)
        
        probabilidad_muerte = (muertes + 1) / (llegadas + 2)
        umbral_exigencia = self.tolerancia_riesgo - (self.pasos_dados * 0.02)
        
        if self.pasos_dados >= 2:
            print(f"🧠 Riesgo Paso {siguiente_paso} -> Prob: {probabilidad_muerte:.2f} | Umbral: {umbral_exigencia:.2f}")
            if probabilidad_muerte > umbral_exigencia:
                return True 
        return False 

    def analyze_situation(self, chicken_pos, fire_positions, threat_positions, game_state):
        current_time = time.time()

        if game_state == "victory":
            self.safe_since = None
            if current_time - self.last_bet_time > self.BET_COOLDOWN:
                return "VICTORIA CONFIRMADA", "Cartel YOLO. Apostando...", "gold", "black", True, self.BTN_RETIRAR_X, self.BTN_RETIRAR_Y, None, None
            return "CELEBRANDO", "Guardando ganancias...", "gold", "black", False, None, None, None, None

        if game_state.startswith("dead_"):
            self.safe_since = None
            self.ultimo_peligro_visto = game_state.replace("dead_", "")
            return "COLISIÓN CONFIRMADA", f"YOLO vio: {self.ultimo_peligro_visto}", "red", "white", True, self.BTN_RETIRAR_X, self.BTN_RETIRAR_Y, None, None

        if chicken_pos is None:
            self.safe_since = None
            self.tiempo_llegada_paso = None 
            
            if self.pasos_dados > 0:
                self.ultimo_peligro_visto = "desaparicion_magica"
                return "COLISIÓN CONFIRMADA", "Gallina desapareció", "red", "white", True, self.BTN_RETIRAR_X, self.BTN_RETIRAR_Y, None, None

            if current_time - self.last_bet_time > self.BET_COOLDOWN:
                return "NUEVA_PARTIDA", "Presionando Apuesta...", "purple", "white", True, self.BTN_RETIRAR_X, self.BTN_RETIRAR_Y, None, None
            return "ESPERANDO TABLERO...", "Buscando gallina...", "gray", "white", False, None, None, None, None

        # --- LÓGICA RETIRADA (SOLO SI VIVA Y EXISTE) ---
        if self.pasos_dados > 0 and self.decidir_siguiente_accion():
            return "RETIRANDO...", "Matemática exige retirada.", "blue", "white", True, self.BTN_RETIRAR_X, self.BTN_RETIRAR_Y, None, None

        # --- ODOMETRÍA VISUAL (El núcleo de tu solución) ---
        cx, cy, cw, ch = chicken_pos
        chicken_center_x = cx + int(cw / 2)
        chicken_center_y = cy + int(ch / 2)
        
        # Fijamos la coordenada X donde nace la gallina en esta partida
        if self.x_inicial_gallina is None:
            self.x_inicial_gallina = chicken_center_x
            self.pasos_dados = 0
            
        # Contamos cuántos carriles (142px) ha atravesado el cuerpo de la gallina
        pasos_reales = int((chicken_center_x - self.x_inicial_gallina + (self.LANE_WIDTH * 0.5)) / self.LANE_WIDTH)
        
        # Solo lo actualizamos si realmente se movió a un carril nuevo
        if pasos_reales > self.pasos_dados:
            self.pasos_dados = pasos_reales
            # Contabilizamos la llegada con éxito para la estadística
            self.llegadas_por_paso[self.pasos_dados] = self.llegadas_por_paso.get(self.pasos_dados, 0) + 1
            print(f"👁️ VISIÓN: Paso {self.pasos_dados} confirmado por movimiento físico.")
            self.tiempo_llegada_paso = current_time

        # --- DETECTOR DE REINICIO FANTASMA ---
        if self.ultima_x_gallina is not None and self.pasos_dados > 0:
            if chicken_center_x < self.ultima_x_gallina - 100:
                self.ultima_x_gallina = None
                self.x_inicial_gallina = None
                self.ultimo_peligro_visto = "teletransporte_reinicio"
                return "COLISIÓN CONFIRMADA", "Tablero reiniciado", "red", "white", True, self.BTN_RETIRAR_X, self.BTN_RETIRAR_Y, None, None
                
        self.ultima_x_gallina = chicken_center_x

        target_lane_x = chicken_center_x + self.LANE_WIDTH
        
        fire_box = (target_lane_x - 45, chicken_center_y + 10, target_lane_x + 45, chicken_center_y + 100)
        car_box = (target_lane_x - 40, chicken_center_y - 280, target_lane_x + 40, chicken_center_y - 30)
        
        car_danger = any(car_box[0] < (tx+tw/2) < car_box[2] and car_box[1] < (ty+th/2) < car_box[3] for (tx, ty, tw, th) in threat_positions)
        lane_fire_active = any(fire_box[0] < (fx+fw/2) < fire_box[2] and fire_box[1] < (fy+fh/2) < fire_box[3] for (fx, fy, fw, fh) in fire_positions)

        fire_danger = False
        if lane_fire_active:
            self.fire_was_active = True
            self.last_fire_time = current_time
            fire_danger = True
        elif self.fire_was_active:
            if current_time - self.last_fire_time > self.FIRE_COOLDOWN:
                self.fire_was_active = False 
            else:
                fire_danger = True 

        if self.tiempo_llegada_paso is None:
            self.tiempo_llegada_paso = current_time
        tiempo_en_paso = current_time - self.tiempo_llegada_paso

        if car_danger:
            self.ultimo_peligro_visto = "auto"
            self.safe_since = None
            return "ESPERANDO...", "PELIGRO: AUTO", "red", "orange", False, self.BTN_AVANZAR_X, self.BTN_AVANZAR_Y, car_box, fire_box

        if fire_danger:
            self.ultimo_peligro_visto = "fuego"
            if tiempo_en_paso > self.LIMITE_PACIENCIA:
                pass 
            else:
                self.safe_since = None
                return "ESPERANDO...", f"PELIGRO: FUEGO ({tiempo_en_paso:.1f}s)", "red", "orange", False, self.BTN_AVANZAR_X, self.BTN_AVANZAR_Y, car_box, fire_box

        if self.safe_since is None: 
            self.safe_since = current_time
        time_passed = current_time - self.safe_since

        if time_passed >= self.SAFETY_DELAY:
            if tiempo_en_paso > self.LIMITE_PACIENCIA:
                return "¡DESATASCANDO!", f"Falso fuego ignorado", "purple", "white", True, self.BTN_AVANZAR_X, self.BTN_AVANZAR_Y, car_box, fire_box
            else:
                return "¡AVANZA!", f"Evaluando siguiente...", "green", "green", True, self.BTN_AVANZAR_X, self.BTN_AVANZAR_Y, car_box, fire_box
        
        return "ESPERANDO...", f"Confirmando... {round(self.SAFETY_DELAY-time_passed, 1)}s", "orange", "white", False, self.BTN_AVANZAR_X, self.BTN_AVANZAR_Y, car_box, fire_box