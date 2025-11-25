"""
ObjectDetector simple et fonctionnel pour YOLOv8
"""

import cv2
import numpy as np
from ultralytics import YOLO

class ObjectDetector:
    def __init__(self, model_path="yolov8n.pt"):
        try:
            self.model = YOLO(model_path)
            print("✅ YOLOv8 model chargé avec succès!")
        except Exception as e:
            print(f"❌ Erreur chargement YOLO: {e}")
            self.model = None

    def detect_objects(self, frame):
        """Détecte les objets dans une frame avec YOLOv8"""
        if self.model is None or frame is None:
            return []
            
        try:
            # Détection YOLO
            results = self.model(frame, verbose=False)
            detections = []
            
            for r in results:
                if r.boxes is not None and len(r.boxes) > 0:
                    for i, box in enumerate(r.boxes):
                        # Coordonnées de la bounding box
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Nom de la classe
                        class_name = self.model.names[class_id]
                        
                        detections.append({
                            "class": class_name,
                            "bbox": [x1, y1, x2, y2],
                            "confidence": confidence
                        })
            
            return detections
            
        except Exception as e:
            print(f"❌ Erreur lors de la détection: {e}")
            return []

    def draw_detections(self, frame, detections):
        """Dessine les détections sur la frame"""
        for det in detections:
            try:
                x1, y1, x2, y2 = map(int, det["bbox"])
                label = det["class"]
                confidence = det.get("confidence", 0.5)
                
                # Couleur selon la confiance
                color = (0, 255, 0)  # Vert par défaut
                if confidence < 0.3:
                    color = (0, 165, 255)  # Orange
                elif confidence < 0.6:
                    color = (0, 255, 255)  # Jaune
                
                # Rectangle de détection
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Label avec fond
                label_text = f"{label} {confidence:.1f}"
                (text_width, text_height), baseline = cv2.getTextSize(
                    label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )
                
                # Rectangle de fond pour le texte
                cv2.rectangle(frame, 
                            (x1, y1 - text_height - 10),
                            (x1 + text_width, y1),
                            color, -1)
                
                # Texte
                cv2.putText(frame, label_text,
                          (x1, y1 - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                          
            except Exception as e:
                print(f"❌ Erreur dessin détection: {e}")
                continue