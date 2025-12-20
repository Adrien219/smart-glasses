"""
Wrapper pour YOLOv8 (Ultralytics) pour la détection d'objets.
"""
import time
import logging
from typing import List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class ObjectDetector:
    """Détecteur d'objets utilisant YOLOv8."""
    
    def __init__(self, model_path: str = 'yolov8n.pt', 
                 confidence_threshold: float = 0.5,
                 iou_threshold: float = 0.3,
                 classes: Optional[List[int]] = None):
        """
        Initialise le détecteur YOLOv8.
        
        Args:
            model_path: Chemin vers le modèle YOLO
            confidence_threshold: Seuil de confiance
            iou_threshold: Seuil IoU pour NMS
            classes: Liste des classes à détecter (None = toutes)
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.classes = classes
        
        self.model = None
        self.class_names = []
        self.initialized = False
        
        # Statistiques
        self.inference_times = []
        self.detection_counts = []
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Charge le modèle YOLOv8."""
        try:
            from ultralytics import YOLO
            
            logger.info(f"Chargement du modèle YOLO: {self.model_path}")
            
            # Charger le modèle
            self.model = YOLO(self.model_path)
            
            # Tester une inference pour vérifier
            dummy_input = np.zeros((640, 640, 3), dtype=np.uint8)
            results = self.model(dummy_input, verbose=False)
            
            # Récupérer les noms de classes
            if hasattr(results[0], 'names') and results[0].names:
                self.class_names = results[0].names
            else:
                # Noms par défaut COCO
                self.class_names = [
                    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
                    'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
                    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
                    'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
                    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard',
                    'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
                    'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork',
                    'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
                    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
                    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv',
                    'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
                    'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
                    'scissors', 'teddy bear', 'hair drier', 'toothbrush'
                ]
            
            self.initialized = True
            logger.info(f"Modèle YOLO chargé avec succès. Classes: {len(self.class_names)}")
            
            # Afficher les classes sélectionnées
            if self.classes:
                class_list = [self.class_names[i] for i in self.classes if i < len(self.class_names)]
                logger.info(f"Classes actives: {class_list}")
            
        except ImportError as e:
            logger.error(f"Ultralytics non installé: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur chargement modèle YOLO: {e}")
            raise
    
    def detect(self, image: np.ndarray) -> List:
        """
        Détecte les objets dans une image.
        
        Args:
            image: Image numpy array (RGB)
            
        Returns:
            Liste de détections (objets Detection)
        """
        from ..navigation_module import Detection
        
        if not self.initialized or self.model is None:
            logger.error("Détecteur non initialisé")
            return []
        
        try:
            start_time = time.time()
            
            # Exécuter l'inférence
            results = self.model(
                image,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                classes=self.classes,
                verbose=False,
                device='cpu'  # Forcer CPU pour Raspberry Pi
            )
            
            inference_time = time.time() - start_time
            self.inference_times.append(inference_time)
            
            # Garder seulement les 50 dernières mesures
            if len(self.inference_times) > 50:
                self.inference_times.pop(0)
            
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                
                if hasattr(result, 'boxes') and result.boxes is not None:
                    boxes = result.boxes
                    
                    # Récupérer les données des boîtes
                    if boxes.xywhn.numel() > 0:  # xywhn: normalisé
                        boxes_data = boxes.xywhn.cpu().numpy()
                        confidences = boxes.conf.cpu().numpy()
                        class_ids = boxes.cls.cpu().numpy().astype(int)
                        
                        for i in range(len(boxes_data)):
                            # Extraire les données
                            x_center, y_center, width, height = boxes_data[i]
                            confidence = float(confidences[i])
                            class_id = int(class_ids[i])
                            
                            # Convertir de xywh (normalisé) à xyxy (normalisé)
                            x1 = x_center - width / 2
                            y1 = y_center - height / 2
                            x2 = x_center + width / 2
                            y2 = y_center + height / 2
                            
                            # S'assurer que les coordonnées sont dans [0, 1]
                            x1 = max(0.0, min(1.0, x1))
                            y1 = max(0.0, min(1.0, y1))
                            x2 = max(0.0, min(1.0, x2))
                            y2 = max(0.0, min(1.0, y2))
                            
                            # Obtenir le nom de la classe
                            class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}"
                            
                            # Créer l'objet Detection
                            detection = Detection(
                                class_name=class_name,
                                confidence=confidence,
                                bbox=(x1, y1, x2 - x1, y2 - y1),  # (x, y, w, h) normalisé
                                distance_estimate=None,
                                bearing=None,
                                timestamp=time.time()
                            )
                            
                            detections.append(detection)
            
            # Mettre à jour les statistiques
            self.detection_counts.append(len(detections))
            if len(self.detection_counts) > 100:
                self.detection_counts.pop(0)
            
            logger.debug(f"Détection: {len(detections)} objets en {inference_time:.3f}s")
            
            return detections
            
        except Exception as e:
            logger.error(f"Erreur détection YOLO: {e}", exc_info=True)
            return []
    
    def get_average_inference_time(self) -> float:
        """Retourne le temps d'inférence moyen."""
        if not self.inference_times:
            return 0.0
        return sum(self.inference_times) / len(self.inference_times)
    
    def get_detection_statistics(self) -> dict:
        """Retourne les statistiques de détection."""
        return {
            'average_inference_time': self.get_average_inference_time(),
            'total_detections': sum(self.detection_counts) if self.detection_counts else 0,
            'average_detections_per_frame': (
                sum(self.detection_counts) / len(self.detection_counts) 
                if self.detection_counts else 0
            ),
            'model_loaded': self.initialized,
            'model_name': self.model_path,
            'class_count': len(self.class_names)
        }
    
    def set_thresholds(self, confidence: Optional[float] = None, 
                       iou: Optional[float] = None):
        """Modifie les seuils de détection."""
        if confidence is not None:
            self.confidence_threshold = max(0.1, min(1.0, confidence))
        if iou is not None:
            self.iou_threshold = max(0.1, min(1.0, iou))
        
        logger.info(f"Seuils mis à jour: conf={self.confidence_threshold}, iou={self.iou_threshold}")
    
    def __del__(self):
        """Destructeur."""
        # Libérer la mémoire GPU si nécessaire
        if hasattr(self, 'model') and self.model is not None:
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass