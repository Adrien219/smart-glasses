import cv2

class ObjectDetector:
    def __init__(self):
        self.model = None
        
    def setup(self):
        print("🎯 Initialisation détection d'objets...")
        # Initialisation YOLOv8
        try:
            from ultralytics import YOLO
            self.model = YOLO('yolov8n.pt')  # Modèle léger
            print("✅ YOLOv8 initialisé avec succès!")
        except ImportError:
            print("⚠️  Ultralytics non installé - mode simulation")
            self.model = None
    
    def detect_obstacles(self, frame):
        """Détection d'objets avec YOLOv8 ou simulation"""
        obstacles = []
        
        if self.model:
            # Détection réelle avec YOLO
            results = self.model(frame)
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if confidence > 0.5:  # Seuil de confiance
                        obstacles.append({
                            'class': class_id,
                            'confidence': confidence,
                            'position': box.xyxy[0].tolist()
                        })
        else:
            # Simulation
            obstacles.append({
                'type': 'obstacle',
                'distance': 45.0,
                'position': 'centre'
            })
        
        return obstacles