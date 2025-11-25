import cv2
import time

class SimpleCameraManager:
    def __init__(self, camera_id=0, resolution=(640, 480)):
        self.camera_id = camera_id
        self.resolution = resolution
        self.cap = None
        self.initialize_camera()
    
    def initialize_camera(self):
        """Initialiser la caméra"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            if self.cap.isOpened():
                print(f"✅ Caméra {self.camera_id} initialisée")
            else:
                print(f"❌ Erreur caméra {self.camera_id}")
        except Exception as e:
            print(f"❌ Erreur initialisation caméra: {e}")
    
    def get_frame(self):
        """Obtenir une frame"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None
    
    def release(self):
        """Libérer la caméra"""
        if self.cap:
            self.cap.release()
            print("✅ Caméra libérée")
    
    # Méthodes compatibilité (ne font rien mais évitent les erreurs)
    def switch_camera(self):
        print("⚠️ Changement de caméra non implémenté")
        return "usb"
    
    def toggle_esp32_flash(self):
        print("⚠️ Contrôle flash non implémenté")
        return False
    
    def get_camera_status(self):
        return {"status": "caméra USB simple"}
    
    def get_both_esp32_frames(self):
        return None, None