import cv2
import math
import numpy as np
from config.settings import Config

class SpatialAnalyzer:
    def __init__(self, frame_width=640, frame_height=480):
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Calibration de la caméra (à ajuster selon ta caméra)
        self.focal_length = 800  # Valeur approximative pour webcam HD
        self.sensor_width = 3.67  # mm (typique pour webcam)
        
        # Hauteurs réelles des objets en mètres (pour calcul de distance)
        self.object_heights = {
            "personne": 1.7,      # Personne moyenne
            "chaise": 0.9,        # Chaise standard
            "table": 0.75,        # Table standard
            "voiture": 1.5,       # Voiture
            "chien": 0.5,         # Chien moyen
            "chat": 0.3,          # Chat
            "bouteille": 0.25,    # Bouteille d'eau
            "téléphone": 0.15,    # Téléphone portable
            "ordinateur portable": 0.03,  # Épaisseur ordinateur
        }
        
        print("📍 Analyseur spatial initialisé")

    def calculate_distance(self, bbox, object_class):
        """Calcule la distance approximative d'un objet"""
        try:
            # Hauteur de la bounding box en pixels
            bbox_height = bbox[3] - bbox[1]
            
            if bbox_height == 0:
                return None
                
            # Hauteur réelle de l'objet (en mètres)
            real_height = self.object_heights.get(object_class, 0.5)  # 0.5m par défaut
            
            # Formule : distance = (hauteur_réelle * focale) / hauteur_pixels
            distance = (real_height * self.focal_length) / bbox_height
            
            return round(distance, 1)
            
        except Exception as e:
            print(f"❌ Erreur calcul distance: {e}")
            return None

    def get_horizontal_position(self, bbox):
        """Détermine la position horizontale (gauche, centre, droite)"""
        x_center = (bbox[0] + bbox[2]) / 2
        third = self.frame_width / 3
        
        if x_center < third:
            return "gauche", "à votre gauche"
        elif x_center < 2 * third:
            return "centre", "devant vous"
        else:
            return "droite", "à votre droite"

    def get_vertical_position(self, bbox):
        """Détermine la position verticale (haut, milieu, bas)"""
        y_center = (bbox[1] + bbox[3]) / 2
        third = self.frame_height / 3
        
        if y_center < third:
            return "haut", "en haut"
        elif y_center < 2 * third:
            return "milieu", "à hauteur"
        else:
            return "bas", "en bas"

    def get_urgency_level(self, distance):
        """Détermine le niveau d'urgence selon la distance"""
        if distance is None:
            return "normal", ""
            
        if distance < 1.0:
            return "danger", "Attention ! "
        elif distance < 2.0:
            return "warning", "Prudence, "
        elif distance < 5.0:
            return "info", ""
        else:
            return "distant", "Au loin, "

    def analyze_detections(self, detections):
        """Analyse spatiale complète des détections"""
        spatial_info = []
        
        for det in detections:
            bbox = det['bbox']
            class_name = det['class']
            confidence = det['confidence']
            
            # Calculs spatiaux
            distance = self.calculate_distance(bbox, class_name)
            horiz_pos, horiz_desc = self.get_horizontal_position(bbox)
            vert_pos, vert_desc = self.get_vertical_position(bbox)
            urgency, urgency_prefix = self.get_urgency_level(distance)
            
            # Construction de la description
            if distance is not None:
                description = f"{urgency_prefix}{class_name} à {distance}m {horiz_desc}"
            else:
                description = f"{class_name} {horiz_desc}"
            
            spatial_info.append({
                'class': class_name,
                'distance': distance,
                'horizontal_position': horiz_pos,
                'horizontal_description': horiz_desc,
                'vertical_position': vert_pos,
                'vertical_description': vert_desc,
                'urgency': urgency,
                'description': description,
                'bbox': bbox,
                'confidence': confidence
            })
            
            # Debug
            print(f"📍 {description}")
        
        return spatial_info

    def draw_spatial_info(self, frame, spatial_info):
        """Dessine les informations spatiales sur l'image"""
        for info in spatial_info:
            bbox = info['bbox']
            description = info['description']
            urgency = info['urgency']
            
            # Couleur selon l'urgence
            if urgency == "danger":
                color = (0, 0, 255)  # Rouge
            elif urgency == "warning":
                color = (0, 165, 255)  # Orange
            else:
                color = (0, 255, 0)  # Vert
            
            # Bounding box
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Label avec description spatiale
            label = f"{description}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Fond du label
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            # Texte
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)