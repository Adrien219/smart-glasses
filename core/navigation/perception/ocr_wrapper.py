"""
Wrapper pour OCR (Tesseract) pour la lecture de texte.
Optionnel pour la reconnaissance de panneaux.
"""
import logging
from typing import Optional, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class OCRWrapper:
    """Wrapper pour la reconnaissance de texte."""
    
    def __init__(self, language: str = 'fra', config: str = '--oem 3 --psm 6'):
        """
        Initialise l'OCR.
        
        Args:
            language: Langue pour l'OCR
            config: Configuration Tesseract
        """
        self.language = language
        self.config = config
        self.tesseract = None
        
        self._initialize_tesseract()
    
    def _initialize_tesseract(self):
        """Initialise Tesseract OCR."""
        try:
            import pytesseract
            
            # Vérifier que tesseract est installé
            pytesseract.get_tesseract_version()
            
            self.tesseract = pytesseract
            logger.info(f"OCR initialisé avec la langue: {self.language}")
            
        except ImportError:
            logger.warning("pytesseract non disponible, OCR désactivé")
            self.tesseract = None
        except Exception as e:
            logger.error(f"Erreur initialisation OCR: {e}")
            self.tesseract = None
    
    def detect_text(self, image: np.ndarray, roi: Optional[Tuple] = None) -> List[dict]:
        """
        Détecte le texte dans une image.
        
        Args:
            image: Image numpy array (RGB)
            roi: Région d'intérêt (x, y, w, h) en pixels
            
        Returns:
            Liste de détections de texte
        """
        if self.tesseract is None:
            return []
        
        try:
            import cv2
            
            # Convertir en niveaux de gris si nécessaire
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Appliquer un prétraitement pour améliorer l'OCR
            gray = cv2.medianBlur(gray, 3)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Découper la ROI si spécifiée
            if roi is not None:
                x, y, w, h = roi
                gray = gray[y:y+h, x:x+w]
            
            # Exécuter l'OCR
            data = self.tesseract.image_to_data(
                gray,
                lang=self.language,
                config=self.config,
                output_type=self.tesseract.Output.DICT
            )
            
            # Filtrer les détections avec une confiance suffisante
            detections = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                confidence = float(data['conf'][i])
                
                if text and confidence > 60:  # Seuil de confiance
                    detection = {
                        'text': text,
                        'confidence': confidence / 100.0,  # Normaliser à [0, 1]
                        'bbox': (
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        ),
                        'type': 'text'
                    }
                    detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Erreur OCR: {e}")
            return []
    
    def detect_signs(self, image: np.ndarray) -> List[dict]:
        """
        Détecte les panneaux spécifiques (ex: sortie, escalier).
        Cette fonction peut être étendue avec un modèle spécialisé.
        """
        # Pour l'instant, utilise l'OCR générique
        # Vous pourriez entraîner un modèle spécifique pour les panneaux
        text_detections = self.detect_text(image)
        
        # Filtrer les textes qui pourraient être des panneaux
        signs = []
        keywords = {
            'sortie': 'exit',
            'exit': 'exit',
            'escalier': 'stairs',
            'stairs': 'stairs',
            'toilette': 'toilet',
            'toilet': 'toilet',
            'homme': 'male_toilet',
            'femme': 'female_toilet',
            'ascenseur': 'elevator',
            'elevator': 'elevator',
            'danger': 'danger',
            'attention': 'warning'
        }
        
        for detection in text_detections:
            text_lower = detection['text'].lower()
            for keyword, sign_type in keywords.items():
                if keyword in text_lower:
                    detection['sign_type'] = sign_type
                    signs.append(detection)
                    break
        
        return signs
    
    def is_available(self) -> bool:
        """Vérifie si l'OCR est disponible."""
        return self.tesseract is not None