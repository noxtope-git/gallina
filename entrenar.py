from ultralytics import YOLO

if __name__ == '__main__':
    modelo = YOLO("yolov8n.pt") 
    
    print("🔥 Iniciando el entrenamiento en la RTX 4060 🔥")
    
    resultados = modelo.train(
        data="C:/Users/USUARIO/Desktop/gallina/Dataset_Gallina/data.yaml", # <-- RUTA A TU YAML
        epochs=100,       
        imgsz=640,        
        device=0,         
        batch=16,         
        workers=2
    )
    print("✅ ¡Entrenamiento Terminado!")