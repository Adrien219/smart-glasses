import requests
import cv2
import numpy as np
import time
import threading

class ESP32EnhancedCommunication:
    def __init__(self, base_url="http://192.168.1.100"):
        self.base_url = base_url
        self.connected = False
        self.streaming = False
        self.current_frame = None
        self.stream_thread = None
        
        self.test_connection()

    def test_connection(self):
        """Tester la connexion à l'ESP32"""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                self.connected = True
                print("✅ ESP32-CAM connectée et fonctionnelle")
            else:
                self.connected = False
                print("❌ ESP32-CAM répond mais avec erreur")
        except Exception as e:
            self.connected = False
            print(f"❌ ESP32-CAM non connectée: {e}")

    def start_stream(self):
        """Démarrer le streaming vidéo"""
        if not self.connected:
            print("❌ Impossible de démarrer le streaming: ESP32 non connectée")
            return False
            
        try:
            self.streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()
            print("🎥 Streaming ESP32 démarré")
            return True
        except Exception as e:
            print(f"❌ Erreur démarrage streaming: {e}")
            return False

    def _stream_loop(self):
        """Boucle de récupération des frames"""
        while self.streaming:
            try:
                frame = self.capture_frame()
                if frame is not None:
                    self.current_frame = frame
                time.sleep(0.1)  # 10 FPS
            except Exception as e:
                print(f"❌ Erreur streaming: {e}")
                time.sleep(1)

    def capture_frame(self):
        """Capturer une frame depuis l'ESP32"""
        try:
            response = requests.get(f"{self.base_url}/capture", timeout=3)
            img_array = np.frombuffer(response.content, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            print(f"❌ Erreur capture ESP32: {e}")
            self.connected = False
            return None

    def control_flash(self, state):
        """Contrôler le flash LED"""
        try:
            command = "on" if state else "off"
            response = requests.get(f"{self.base_url}/flash?state={command}", timeout=2)
            return response.status_code == 200
        except:
            return False

    def get_sensor_data(self):
        """Obtenir les données des capteurs ESP32"""
        try:
            response = requests.get(f"{self.base_url}/sensors", timeout=2)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    def stop_stream(self):
        """Arrêter le streaming"""
        self.streaming = False
        if self.stream_thread:
            self.stream_thread.join(timeout=1.0)
        print("🔴 Streaming ESP32 arrêté")

    def get_frame(self):
        """Obtenir la frame courante"""
        return self.current_frame