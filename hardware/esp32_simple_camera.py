import cv2
import requests
import time
import threading

class ESP32SimpleCamera:
    def __init__(self, ip="10.231.158.139"):
        self.ip = ip
        self.is_connected = False
        self.current_frame = None
        
        print(f"🔌 Initialisation ESP32: {self.ip}")
        
        # Test de connexion simple et rapide
        try:
            response = requests.get(f"http://{self.ip}", timeout=2)
            if response.status_code == 200:
                print("✅ ESP32 accessible")
                self.is_connected = True
            else:
                print("⚠️ ESP32 non accessible")
        except:
            print("❌ ESP32 hors ligne")
            
    def get_frame(self):
        """Retourne None pour l'instant"""
        return None
        
    def toggle_flash(self):
        """Simuler le flash"""
        print("⚠️ Flash ESP32 simulé")
        return True