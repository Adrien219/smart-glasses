import requests
import cv2
import numpy as np
import time

class ESP32Camera:
    def __init__(self, url):
        self.url = url
        self.connected = False
        self.test_connection()
    
    def test_connection(self):
        """Tester la connexion à l'ESP32-CAM"""
        try:
            response = requests.get(self.url, timeout=5)
            self.connected = True
            print("✅ ESP32-CAM connectée")
        except:
            self.connected = False
            print("❌ ESP32-CAM non connectée")
    
    def capture_frame(self):
        """Capturer une frame depuis l'ESP32-CAM"""
        if not self.connected:
            return None
            
        try:
            response = requests.get(self.url, timeout=2)
            img_array = np.frombuffer(response.content, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            print(f"❌ Erreur capture ESP32: {e}")
            self.connected = False
            return None