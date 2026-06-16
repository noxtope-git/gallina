# gallina stake experimento IA

Bot autónomo que juega y se re-entrena solo usando YOLOv8 + Grounding DINO.

## Requisitos

- Python 3.10+
- GPU NVIDIA con CUDA (obligatorio, el programa verifica al iniciar)

## Opción 1: Ejecutable (más simple)

Genera el .exe con doble clic en `build.bat` (necesitas Python y CUDA instalados).

> **Nota:** El .exe pesa ~2.5GB por incluir PyTorch + CUDA, por lo que no se sube a GitHub. Si quieres compartir el .exe, súbelo a Google Drive, Mega o Discord desde tu PC y pega el enlace aquí mismo en el README.

## Opción 2: Desde código (Python)

```powershell
# Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el bot
python main.py
```

## Controles

| Tecla/Control | Función |
|---|---|
| `Ctrl+Ñ` | Activar/Pausar Auto-Play |
| `F9` | Capturar foto manual para dataset |
| Botón **AUTO-PLAY** | Inicia/Detiene el juego automático |
| Botón **SOLO JUGAR** | Juega sin capturar screens ni auto-entrenar |
| Botón **ENTRENAR IA** | Entrena la IA manualmente |

## Funcionalidades

- **Detector de GPU automático** — Verifica que el hardware sea compatible al iniciar. Si no detecta una GPU NVIDIA con CUDA, muestra las series compatibles y se cierra para proteger equipos de gama baja.
- **Solo Jugar** — Botón que desactiva la captura de screenshots y el auto-entrenamiento. Solo juega con lo ya aprendido. Al desactivarlo, vuelve al modo normal con captura y re-entrenamiento automático.
- **Auto-aprendizaje** — Cuando se acumulan suficientes fotos de fallos, la IA se re-entrena sola usando DINO para etiquetar y YOLO para aprender.

## Estructura del proyecto

```
gallina/
├── src/               # Código fuente del bot
│   ├── vision.py      # Detección por cámara (YOLO)
│   ├── logic.py       # Lógica de juego y decisiones
│   └── caja_negra.py  # Captura de evidencia en muerte
├── scripts/           # Utilidades
│   ├── entrenar.py    # Entrenamiento YOLO
│   ├── etiquetador_dino.py
│   ├── fusionar_dino.py
│   └── ...
├── assets/            # Imágenes del UI
├── dist/              # Ejecutable compilado
│   └── gallina.exe
├── main.py            # Punto de entrada
├── main.spec          # Configuración de PyInstaller
└── best.pt            # Pesos del modelo (generado)
```
