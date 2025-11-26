import cv2
import requests
import threading
import numpy as np

# Importations conditionnelles pour éviter les 
try:
    from core.face_recognizer import FaceRecognizer
    from core.text_recognizer import TextRecognizer
    from core.object_detector import ObjectDetector
    MODULES_LOADED = True
except ImportError as e:
    print(f"⚠️  Modules core non trouvés: {e}")
    print("🔧 Utilisation du mode test...")
    MODULES_LOADED = False
class CameraProcessor:
    def __init__(self, esp32_ip):
        self.esp32_ip = esp32_ip
        self.esp32_stream = f"http://{esp32_ip}/stream"
        self.running = True  # ⬅️ AJOUTER
        self.cap_esp32 = None
        self.cap_rpi = None
        
        if MODULES_LOADED:
            self.face_recognizer = FaceRecognizer()
            self.text_recognizer = TextRecognizer() 
            self.object_detector = ObjectDetector()
        else:
            self.face_recognizer = None
            self.text_recognizer = None
            self.object_detector = None
        
    def setup(self):
        print("🔧 Initialisation des modules...")
        
        if MODULES_LOADED:
            try:
                self.face_recognizer.setup()
                print("✅ Reconnaissance faciale initialisée")
            except Exception as e:
                print(f"❌ Erreur reconnaissance faciale: {e}")
                self.face_recognizer = None
            
            try:
                self.text_recognizer.setup()
                print("✅ OCR initialisé")
            except Exception as e:
                print(f"❌ Erreur OCR: {e}")
                self.text_recognizer = None
                
            try:
                self.object_detector.setup()
                print("✅ Détection d'objets initialisée")
            except Exception as e:
                print(f"❌ Erreur détection objets: {e}")
                self.object_detector = None
        else:
            print("🔧 Mode test activé - modules simulés")
        
    def process_esp32_stream(self):
        """Traite le stream ESP32 pour visages/billets"""
        print(f"📹 Connexion au stream ESP32 ({self.esp32_ip})...")
        
        # Test de connectivité d'abord
        if not self.test_esp32_connection():
            print("❌ ESP32 inaccessible - arrêt du stream")
            return
        
        try:
            cap = cv2.VideoCapture(self.esp32_stream)
            
            if not cap.isOpened():
                print("❌ Impossible d'ouvrir le stream ESP32")
                return
            
            print("✅ Stream ESP32 ouvert avec succès")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Impossible de lire le stream ESP32")
                    break
                    
                # Traitement selon les modules disponibles
                if self.face_recognizer:
                    faces = self.face_recognizer.detect_faces(frame)
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                        cv2.putText(frame, "Visage", (x, y-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
                
                if self.text_recognizer:
                    bills = self.text_recognizer.detect_bills(frame)
                    for bill in bills:
                        # Dessiner rectangle autour du billet
                        pts = bill['position']
                        cv2.polylines(frame, [np.array(pts, dtype=np.int32)], 
                                     True, (0, 255, 0), 2)
                        cv2.putText(frame, f"{bill['amount']}", 
                                   (pts[0][0], pts[0][1]-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Affichage
                cv2.putText(frame, f"ESP32 Stream - {self.esp32_ip}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow('ESP32 - Visages/Billets', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            cap.release()
            
        except Exception as e:
            print(f"❌ Erreur stream ESP32: {e}")
        finally:
            cv2.destroyAllWindows()
    
    def test_esp32_connection(self):
        """Test si l'ESP32 est accessible"""
        try:
            response = requests.get(f"http://{self.esp32_ip}/status", timeout=5)
            print(f"✅ ESP32 accessible - Status: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ ESP32 inaccessible: {e}")
            return False
    
    def process_rpi_camera(self):
        """Traite la caméra RPi pour navigation"""
        print("📷 Démarrage caméra Raspberry Pi...")
        
        try:
            cap = cv2.VideoCapture(0)  # Caméra USB RPi
            
            if not cap.isOpened():
                print("❌ Impossible d'ouvrir la caméra RPi")
                return
                
            print("✅ Caméra RPi ouverte avec succès")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Erreur lecture caméra RPi")
                    break
                
                # Détection d'obstacles
                if self.object_detector:
                    obstacles = self.object_detector.detect_obstacles(frame)
                    for obstacle in obstacles:
                        cv2.putText(frame, f"Obstacle: {obstacle.get('distance', 'N/A')}cm", 
                                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # Affichage
                cv2.putText(frame, "RPi Camera - Navigation", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow('RPi - Navigation', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            cap.release()
            
        except Exception as e:
            print(f"❌ Erreur caméra RPi: {e}")
        finally:
            cv2.destroyAllWindows()

    def process_rpi_camera_main_thread(self, controller):
        """Version CAMÉRA dans le THREAD PRINCIPAL - ARRÊT IMMÉDIAT"""
        print("📷 Caméra RPi - Thread principal...")
        
        cap = None
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("❌ Impossible d'ouvrir la caméra RPi")
                return
                
            print("✅ Caméra RPi ouverte - Appuyez sur 'q' pour quitter")
            
            while controller.running:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Erreur lecture caméra")
                    break
                
                # Traitement YOLO
                if hasattr(controller, 'model') and controller.model:
                    results = controller.model(frame)
                    annotated_frame = results[0].plot()
                else:
                    annotated_frame = frame  # Fallback sans YOLO
                
                # Affichage
                cv2.imshow('Smart Glasses - Appuyez sur Q pour quitter', annotated_frame)
                
                # ✅ VÉRIFICATION CONTINUE DE LA TOUCHE 'q'
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("🎯 Touche Q pressée - Arrêt demandé")
                    controller.running = False
                    break
                    
        except Exception as e:
            print(f"❌ Erreur caméra: {e}")
        finally:
            # ✅ FERMETURE GARANTIE
            if cap:
                cap.release()
            cv2.destroyAllWindows()
            print("✅ Caméra RPi fermée")

    def stop(self):
        """Arrêt IMMÉDIAT et SÉCURISÉ des caméras"""
        print("🛑 Arrêt urgent des caméras...")
        self.running = False
        
        # Fermeture forcée mais sécurisée
        try:
            if self.cap_esp32:
                self.cap_esp32.release()
            if self.cap_rpi:
                self.cap_rpi.release()
        except:
            pass
        
        # Destruction fenêtres
        try:
            cv2.destroyAllWindows()
        except:
            pass
        
        print("✅ Caméras arrêtées")