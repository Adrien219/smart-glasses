import cv2
import face_recognition
import numpy as np
import os
from pathlib import Path

class FaceRecognizer:
    def __init__(self, known_faces_path="known_faces"):
        print("👤 Initialisation reconnaissance faciale avancée...")
        self.known_faces_path = known_faces_path
        self.known_face_encodings = []
        self.known_face_names = []
        
        # Charger les visages connus
        self.load_known_faces()
        print(f"✅ {len(self.known_face_names)} visages chargés depuis '{known_faces_path}'")

    def load_known_faces(self):
        """Charger tous les visages du dossier known_faces"""
        if not os.path.exists(self.known_faces_path):
            print(f"⚠️ Dossier '{self.known_faces_path}' non trouvé - création...")
            os.makedirs(self.known_faces_path)
            return

        supported_formats = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
        
        for file_path in Path(self.known_faces_path).iterdir():
            if file_path.suffix.lower() in supported_formats:
                try:
                    # Charger l'image
                    image = face_recognition.load_image_file(str(file_path))
                    
                    # Détecter les encodages faciaux
                    face_encodings = face_recognition.face_encodings(image)
                    
                    if len(face_encodings) > 0:
                        # Prendre le premier visage détecté
                        self.known_face_encodings.append(face_encodings[0])
                        self.known_face_names.append(file_path.stem)  # Nom du fichier sans extension
                        print(f"  ✅ Visage chargé: {file_path.stem}")
                    else:
                        print(f"  ⚠️ Aucun visage détecté dans: {file_path.name}")
                        
                except Exception as e:
                    print(f"  ❌ Erreur chargement {file_path.name}: {e}")

    def detect_faces(self, frame):
        """Détecter et reconnaître les visages dans une frame"""
        if len(self.known_face_encodings) == 0:
            return []

        try:
            # Redimensionner pour améliorer les performances
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Détecter tous les visages dans l'image
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            face_confidences = []

            for face_encoding in face_encodings:
                # Comparer avec les visages connus
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "Inconnu"
                confidence = 0.0

                # Calculer les distances
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                        confidence = 1 - face_distances[best_match_index]

                face_names.append(name)
                face_confidences.append(confidence)

            # Convertir les coordonnées vers l'image originale
            results = []
            for (top, right, bottom, left), name, confidence in zip(face_locations, face_names, face_confidences):
                # Multiplier par 2 car on a redimensionné à 0.5
                top *= 2; right *= 2; bottom *= 2; left *= 2
                
                results.append({
                    'bbox': (left, top, right - left, bottom - top),
                    'name': name,
                    'confidence': confidence
                })

            return results

        except Exception as e:
            print(f"❌ Erreur détection faciale: {e}")
            return []

    def draw_faces(self, frame, faces):
        """Dessiner les rectangles et noms sur la frame"""
        for face in faces:
            left, top, width, height = face['bbox']
            right = left + width
            bottom = top + height
            
            # Couleur selon la reconnaissance
            if face['name'] == "Inconnu":
                color = (0, 0, 255)  # Rouge pour inconnu
            else:
                color = (0, 255, 0)  # Vert pour connu
            
            # Rectangle autour du visage
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Étiquette avec nom et confiance
            label = f"{face['name']} ({face['confidence']:.2f})"
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 6, bottom - 6), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        return frame