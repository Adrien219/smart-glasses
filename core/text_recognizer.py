import easyocr
import cv2
import numpy as np
import re
class TextRecognizer:
    def __init__(self):
        self.reader = None
        print("📖 Initialisation OCR...")
        self.initialize_ocr()

    def initialize_ocr(self):
        """Initialiser EasyOCR"""
        try:
            self.reader = easyocr.Reader(['fr', 'en'])
            print("✅ EasyOCR initialisé avec succès!")
        except Exception as e:
            print(f"❌ Erreur initialisation EasyOCR: {e}")

    def extract_text(self, frame):
        """Extraire le texte d'une image"""
        if self.reader is None:
            return []

        try:
            results = self.reader.readtext(frame)
            text_info = []
            
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Seuil de confiance
                    text_info.append({
                        'bbox': bbox,
                        'text': text,
                        'confidence': confidence
                    })
                    print(f"📖 Texte détecté: {text} (confiance: {confidence:.2f})")
            
            return text_info
            
        except Exception as e:
            print(f"❌ Erreur reconnaissance texte: {e}")
            return []

    def draw_text_areas(self, frame, text_info):
        """Dessiner les zones de texte sur l'image"""
        try:
            for info in text_info:
                bbox = info['bbox']
                text = info['text']
                confidence = info['confidence']
                
                # Convertir les coordonnées EasyOCR
                points = np.array(bbox, dtype=np.int32)
                
                # Dessiner le polygone
                cv2.polylines(frame, [points], True, (0, 255, 0), 2)
                
                # Dessiner un fond pour le texte
                top_left = tuple(points[0])
                text_size = cv2.getTextSize(f"{text} ({confidence:.2f})", 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                
                # Rectangle de fond
                cv2.rectangle(frame, 
                             (top_left[0], top_left[1] - text_size[1] - 5),
                             (top_left[0] + text_size[0], top_left[1] - 5),
                             (0, 255, 0), -1)
                
                # Texte avec la confiance
                cv2.putText(frame, f"{text} ({confidence:.2f})", 
                           (top_left[0], top_left[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                
            return frame
            
        except Exception as e:
            print(f"❌ Erreur dessin texte: {e}")
            return frame
        
    def setup(self):
        print("💰 Initialisation reconnaissance billets...")
        self.reader = easyocr.Reader(['fr', 'en'])
    
    def detect_bills(self, frame):
        """Détecte les billets dans l'image"""
        results = self.reader.readtext(frame)
        bills = []
        
        for (bbox, text, confidence) in results:
            amount = self.extract_amount(text)
            if amount and confidence > 0.6:
                bills.append({
                    'amount': amount,
                    'confidence': confidence,
                    'position': bbox
                })
        
        return bills
    
    def extract_amount(self, text):
        patterns = [
            r'(\d+)\s*€',
            r'EURO\s*(\d+)',
            r'(\d+)\s*EUROS',
            r'(\d+)\s*EUR'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.upper())
            if match:
                return f"{match.group(1)}€"
        return None
    
    def announce_text(self, text):
        """Annoncer le texte détecté (méthode pour VoiceAssistant)"""
        return f"Texte détecté: {text}"