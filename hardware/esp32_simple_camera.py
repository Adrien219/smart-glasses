import cv2
import requests
import threading
import time

class ESP32SimpleCamera:
    def __init__(self, ip_address):
        self.ip = ip_address
        self.stream_url = f"http://{ip_address}/stream"
        self.is_connected = False
        self.frame = None
        self.running = False
        self.thread = None
        
        # Tester la connexion
        self.connect()
    
    def connect(self):
        """Test simple de connexion"""
        try:
            print(f"🔌 Test ESP32 single cam: {self.ip}")
            # Test basique de connexion
            response = requests.get(f"http://{self.ip}/", timeout=3)
            self.is_connected = (response.status_code == 200)
            
            if self.is_connected:
                print(f"✅ ESP32 single cam connectée")
                self.start_stream()
            else:
                print("❌ ESP32 single cam inaccessible")
                
        except Exception as e:
            print(f"❌ Erreur connexion ESP32: {e}")
            self.is_connected = False
    
    def start_stream(self):
        """Démarrer le flux simple"""
        if not self.is_connected:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._stream_worker, daemon=True)
        self.thread.start()
        print("📹 Flux ESP32 single cam démarré")
    
    def _stream_worker(self):
        """Worker simple pour une seule caméra"""
        cap = cv2.VideoCapture(self.stream_url)
        
        while self.running and self.is_connected:
            try:
                ret, frame = cap.read()
                if ret:
                    self.frame = frame
                else:
                    # Réessayer la connexion
                    cap.release()
                    time.sleep(1)
                    cap = cv2.VideoCapture(self.stream_url)
            except Exception as e:
                print(f"❌ Erreur flux: {e}")
                time.sleep(1)
        
        if cap:
            cap.release()
    
    def get_frame(self):
        """Obtenir la frame actuelle"""
        return self.frame
    
    def toggle_flash(self):
        """Basculer le flash"""
        try:
            response = requests.get(f"http://{self.ip}/flash")
            return response.status_code == 200
        except:
            return False
    
    def release(self):
        """Arrêter le flux"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)