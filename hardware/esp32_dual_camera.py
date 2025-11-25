import requests
import cv2
import numpy as np
import time
import threading
from config.settings import Config

class ESP32DualCamera:
    def __init__(self):
        # URLs ESP32 avec valeurs par défaut
        self.esp32_ip = getattr(Config, 'ESP32_IP', '192.168.4.1')
        self.esp32_port = getattr(Config, 'ESP32_PORT', 80)
        
        self.cam1_url = f"http://{self.esp32_ip}:{self.esp32_port}/cam1"
        self.cam2_url = f"http://{self.esp32_ip}:{self.esp32_port}/cam2"
        self.flash_url = f"http://{self.esp32_ip}:{self.esp32_port}/flash"
        
        self.connected = False
        self.current_camera = "cam1"
        self.cam1_frame = None
        self.cam2_frame = None
        self.capture_interval = 0.3
        self.flash_enabled = False
        
        # Threads de capture
        self.capture_thread = None
        self.streaming = False
        
        self.test_connection()

    def test_connection(self):
        """Tester la connexion aux caméras ESP32"""
        print("🔍 Test de connexion ESP32 Dual Camera...")
        
        # Tester caméra 1
        try:
            response = requests.get(self.cam1_url, timeout=5)
            if response.status_code == 200:
                print("✅ ESP32 Caméra 1 connectée")
                self.connected = True
            else:
                print("❌ ESP32 Caméra 1 inaccessible")
        except Exception as e:
            print(f"❌ Erreur connexion Caméra 1: {e}")
        
        if self.connected:
            self.start_streaming()

    def start_streaming(self):
        """Démarrer le streaming"""
        if not self.connected:
            return False
            
        self.streaming = True
        self.capture_thread = threading.Thread(target=self._streaming_loop, daemon=True)
        self.capture_thread.start()
        print("🎥 Streaming ESP32 Dual Camera démarré")
        return True

    def _streaming_loop(self):
        """Boucle de capture"""
        while self.streaming:
            try:
                # Capture caméra 1
                try:
                    response1 = requests.get(self.cam1_url, timeout=3)
                    if response1.status_code == 200:
                        img_array = np.frombuffer(response1.content, np.uint8)
                        frame1 = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        self.cam1_frame = frame1
                except:
                    self.cam1_frame = None
                
                # Capture caméra 2  
                try:
                    response2 = requests.get(self.cam2_url, timeout=3)
                    if response2.status_code == 200:
                        img_array = np.frombuffer(response2.content, np.uint8)
                        frame2 = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        self.cam2_frame = frame2
                except:
                    self.cam2_frame = None
                
                time.sleep(self.capture_interval)
                
            except Exception as e:
                print(f"❌ Erreur streaming ESP32: {e}")
                time.sleep(1)

    def get_frame(self, camera=None):
        """Obtenir une frame"""
        if not camera:
            camera = self.current_camera
            
        if camera == "cam1" and self.cam1_frame is not None:
            return self.cam1_frame
        elif camera == "cam2" and self.cam2_frame is not None:
            return self.cam2_frame
        else:
            return None

    def get_both_frames(self):
        """Obtenir les deux frames"""
        return self.cam1_frame, self.cam2_frame

    def toggle_flash(self):
        """Activer/désactiver le flash"""
        if not self.connected:
            return False
            
        try:
            new_state = not self.flash_enabled
            command = "on" if new_state else "off"
            response = requests.get(f"{self.flash_url}?state={command}", timeout=2)
            self.flash_enabled = new_state
            
            if response.status_code == 200:
                status = "activé" if new_state else "désactivé"
                print(f"⚡ Flash ESP32 {status}")
                return True
        except Exception as e:
            print(f"❌ Erreur contrôle flash: {e}")
            
        return False

    def stop_streaming(self):
        """Arrêter le streaming"""
        self.streaming = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        print("🔴 Streaming ESP32 arrêté")

    def get_status(self):
        """Obtenir le statut"""
        return {
            "connected": self.connected,
            "active_camera": self.current_camera,
            "cam1_available": self.cam1_frame is not None,
            "cam2_available": self.cam2_frame is not None,
            "flash_enabled": self.flash_enabled,
            "streaming": self.streaming
        }