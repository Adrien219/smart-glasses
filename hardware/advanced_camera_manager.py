import cv2
import time
from config.settings import Config

class AdvancedCameraManager:
    def __init__(self):
        self.available_cameras = []
        self.active_camera = "usb"
        self.usb_camera = None
        self.esp32_dual_camera = None
        
        self.initialize_all_cameras()
    
    def initialize_all_cameras(self):
        """Initialiser les 3 caméras"""
        print("📷 Initialisation du système multi-caméras...")
        
        # Caméra USB Raspberry Pi
        try:
            self.usb_camera = cv2.VideoCapture(Config.CAMERA_ID)
            self.usb_camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_RESOLUTION[0])
            self.usb_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_RESOLUTION[1])
            self.usb_camera.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
            
            # Test capture
            ret, test_frame = self.usb_camera.read()
            if ret:
                self.available_cameras.append("usb")
                print("✅ Caméra USB Raspberry Pi initialisée")
            else:
                print("❌ Caméra USB non disponible")
                self.usb_camera = None
        except Exception as e:
            print(f"❌ Erreur caméra USB: {e}")
            self.usb_camera = None
        
        # ESP32 Double Caméra
        try:
            from hardware.esp32_dual_camera import ESP32DualCamera
            self.esp32_dual_camera = ESP32DualCamera()
            
            if self.esp32_dual_camera.connected:
                self.available_cameras.extend(["esp32_cam1", "esp32_cam2"])
                print("✅ ESP32 Double Caméra initialisée")
                
                # Priorité ESP32 si configuré
                if Config.PREFER_ESP32_CAMERAS and "esp32_cam1" in self.available_cameras:
                    self.active_camera = "esp32_cam1"
            else:
                print("❌ ESP32 Double Caméra non connectée")
                self.esp32_dual_camera = None
        except Exception as e:
            print(f"❌ Erreur initialisation ESP32: {e}")
            self.esp32_dual_camera = None
        
        print(f"🎯 Caméras disponibles: {self.available_cameras}")
        print(f"🎯 Caméra active: {self.active_camera}")

    def get_frame(self):
        """Obtenir une frame de la caméra active"""
        # ESP32 Caméra 1
        if self.active_camera == "esp32_cam1" and self.esp32_dual_camera:
            frame = self.esp32_dual_camera.get_frame("cam1")
            if frame is not None:
                return frame
            else:
                print("🔄 Fallback ESP32 cam1 → USB")
                self.active_camera = "usb"
        
        # ESP32 Caméra 2  
        elif self.active_camera == "esp32_cam2" and self.esp32_dual_camera:
            frame = self.esp32_dual_camera.get_frame("cam2")
            if frame is not None:
                return frame
            else:
                print("🔄 Fallback ESP32 cam2 → USB")
                self.active_camera = "usb"
        
        # Caméra USB (fallback)
        if self.active_camera == "usb" and self.usb_camera:
            ret, frame = self.usb_camera.read()
            if ret:
                return frame
        
        return None

    def switch_camera(self):
        """Changer de caméra dans l'ordre : usb → esp32_cam1 → esp32_cam2 → usb"""
        if not self.available_cameras:
            return self.active_camera
            
        current_index = self.available_cameras.index(self.active_camera) if self.active_camera in self.available_cameras else -1
        next_index = (current_index + 1) % len(self.available_cameras)
        self.active_camera = self.available_cameras[next_index]
        
        print(f"📷 Caméra activée: {self.active_camera}")
        return self.active_camera

    def get_esp32_frame(self, camera):
        """Obtenir une frame spécifique de l'ESP32"""
        if self.esp32_dual_camera:
            return self.esp32_dual_camera.get_frame(camera)
        return None

    def get_both_esp32_frames(self):
        """Obtenir les deux frames ESP32 simultanément"""
        if self.esp32_dual_camera:
            return self.esp32_dual_camera.get_both_frames()
        return None, None

    def control_esp32_flash(self, state):
        """Contrôler le flash ESP32"""
        if self.esp32_dual_camera:
            return self.esp32_dual_camera.control_flash(state)
        return False

    def toggle_esp32_flash(self):
        """Activer/désactiver le flash ESP32"""
        if self.esp32_dual_camera:
            return self.esp32_dual_camera.toggle_flash()
        return False

    def get_camera_status(self):
        """Obtenir le statut complet des caméras"""
        esp32_status = self.esp32_dual_camera.get_status() if self.esp32_dual_camera else {}
        
        return {
            "active_camera": self.active_camera,
            "available_cameras": self.available_cameras,
            "usb_available": self.usb_camera is not None,
            "esp32_available": self.esp32_dual_camera is not None and self.esp32_dual_camera.connected,
            "esp32_status": esp32_status
        }

    def release(self):
        """Libérer toutes les ressources caméra"""
        if self.usb_camera:
            self.usb_camera.release()
        if self.esp32_dual_camera:
            self.esp32_dual_camera.stop_streaming()
        print("✅ Toutes les caméras libérées")