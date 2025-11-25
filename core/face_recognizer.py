import cv2
import face_recognition
import numpy as np
import os
import pickle

class FaceRecognizer:
    def __init__(self):
        print("👤 Initialisation reconnaissance faciale...")
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_known_faces()
        
    def load_known_faces(self):
        """Charger les visages connus depuis le dossier"""
        faces_dir = "known_faces"
        if not os.path.exists(faces_dir):
            os.makedirs(faces_dir)
            print("📁 Dossier 'known_faces' créé - Ajoutez-y des photos")
            return
            
        for filename in os.listdir(faces_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(faces_dir, filename)
                image = face_recognition.load_image_file(image_path)
                
                # Extraire l'encodage du visage
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_face_encodings.append(encodings[0])
                    self.known_face_names.append(os.path.splitext(filename)[0])
                    print(f"✅ Visage chargé: {filename}")
                    
        print(f"📊 {len(self.known_face_names)} visages connus chargés")

    def detect_faces(self, frame):
        """Détecter et reconnaître les visages"""
        try:
            # Convertir BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Détecter tous les visages
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            face_info = []
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Comparer avec les visages connus
                name = "Inconnu"
                if self.known_face_encodings:
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    
                    if True in matches:
                        best_match_index = np.argmin(face_distances)
                        if face_distances[best_match_index] < 0.6:
                            name = self.known_face_names[best_match_index]
                
                face_info.append({
                    'name': name,
                    'location': (left, top, right, bottom),
                    'distance': face_distances[best_match_index] if name != "Inconnu" else None
                })
                
                print(f"👤 {name} détecté")
                
            return face_info
            
        except Exception as e:
            print(f"❌ Erreur reconnaissance faciale: {e}")
            return []

    def draw_faces(self, frame, faces):
        """Dessiner les visages sur l'image"""
        for face in faces:
            left, top, right, bottom = face['location']
            name = face['name']
            
            # Rectangle autour du visage
            color = (0, 255, 0) if name != "Inconnu" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Label
            label = f"{name}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Fond du label
            cv2.rectangle(frame, (left, bottom - label_size[1] - 10), 
                         (left + label_size[0], bottom), color, -1)
            
            # Texte
            cv2.putText(frame, label, (left, bottom - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)