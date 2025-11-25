import cv2
import numpy as np
import torch
from ultralytics import YOLO

class MoneyRecognizer:
    def __init__(self):
        print("💰 Initialisation reconnaissance de billets...")
        
        # Modèle custom pour billets (à entraîner)
        self.model = YOLO('money_detection.pt')  # Modèle custom
        self.confidence_threshold = 0.6
        
        # Caractéristiques des billets euros
        self.euro_characteristics = {
            "5": {"color": "gris", "size": "120x62mm"},
            "10": {"color": "rouge", "size": "127x67mm"},
            "20": {"color": "bleu", "size": "133x72mm"},
            "50": {"color": "orange", "size": "140x77mm"},
            "100": {"color": "vert", "size": "147x82mm"},
            "200": {"color": "jaune", "size": "153x82mm"},
            "500": {"color": "violet", "size": "160x82mm"}
        }
        
    def detect_money(self, frame):
        """Détecter les billets dans l'image"""
        try:
            # Redimensionner pour performance
            input_frame = cv2.resize(frame, (640, 480))
            
            # Détection avec YOLO
            results = self.model(input_frame, conf=0.5, verbose=False)
            
            money_detections = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    # Estimation de la valeur basée sur la taille/forme
                    bbox = box.xyxy[0].tolist()
                    value = self.estimate_money_value(bbox, frame)
                    
                    money_detections.append({
                        'value': value,
                        'confidence': confidence,
                        'bbox': bbox,
                        'currency': 'EUR'
                    })
                    
                    print(f"💰 Détection: {value}€ (confiance: {confidence:.2f})")
            
            return money_detections
            
        except Exception as e:
            print(f"❌ Erreur détection billets: {e}")
            return []

    def estimate_money_value(self, bbox, frame):
        """Estimer la valeur du billet basée sur la taille et les couleurs"""
        x1, y1, x2, y2 = map(int, bbox)
        roi = frame[y1:y2, x1:x2]
        
        if roi.size == 0:
            return "inconnu"
        
        # Analyser les couleurs dominantes
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        dominant_color = np.mean(hsv[:, :, 0])
        
        # Estimer basé sur la taille relative
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = width / height if height > 0 else 0
        
        # Logique de classification simplifiée
        if aspect_ratio > 2.0:
            if dominant_color < 30:
                return "5"
            elif dominant_color < 60:
                return "10"
        elif aspect_ratio > 1.8:
            return "20"
        elif aspect_ratio > 1.7:
            return "50"
        else:
            return "inconnu"
            
        return "inconnu"

    def draw_money_detections(self, frame, detections):
        """Dessiner les détections de billets"""
        for det in detections:
            bbox = det['bbox']
            value = det['value']
            confidence = det['confidence']
            
            x1, y1, x2, y2 = map(int, bbox)
            
            # Bounding box verte pour l'argent
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            
            # Label
            label = f"{value}€ ({confidence:.2f})"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            
            # Fond du label
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            
            # Texte
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)