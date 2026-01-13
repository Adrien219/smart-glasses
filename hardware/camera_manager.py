import os
import time
import cv2   # Toujours importé (Windows + USB)
import numpy as np

IS_WINDOWS = os.name == 'nt'

# --- Gestion des imports Raspberry Pi ---
try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None
    print("⚠️ picamera2 non installé → Mode USB uniquement")


class CameraManager:
    def __init__(self, camera_id=0, resolution=(640, 480)):
        self.camera_id = camera_id
        self.resolution = resolution
        
        self.cap = None
        self.picam2 = None
        
        self.active_camera = "usb"
        self.available_cameras = ["usb"]
        self.esp32_dual_camera = None

        self.initialize_camera()
        self.initialize_esp32()

    # -------------------------------------------------------------------------
    # ESP32 INIT
    # -------------------------------------------------------------------------
    def initialize_esp32(self):
        try:
            from hardware.esp32_dual_camera import ESP32DualCamera
            self.esp32_dual_camera = ESP32DualCamera()

            if self.esp32_dual_camera.connected:
                self.available_cameras += ["esp32_cam1", "esp32_cam2"]
                print("✅ ESP32 Dual Camera disponible")
            else:
                print("❌ ESP32 Dual Camera non connectée")

        except Exception as e:
            print(f"⚠️ ESP32 non disponible: {e}")
            self.esp32_dual_camera = None

    # -------------------------------------------------------------------------
    # CAMERA INIT
    # -------------------------------------------------------------------------
    def initialize_camera(self):
        if IS_WINDOWS:
            # Windows → Webcam USB
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

            if self.cap.isOpened():
                print(f"✅ Caméra USB Windows initialisée - {self.resolution}")
            else:
                print("❌ Aucune caméra USB détectée")

        else:
            # Raspberry Pi → Picamera2 si dispo
            if Picamera2 is not None:
                try:
                    self.picam2 = Picamera2()
                    config = self.picam2.create_preview_configuration(main={"size": self.resolution})
                    self.picam2.configure(config)
                    self.picam2.start()
                    print(f"✅ Caméra Pi initialisée - {self.resolution}")
                    return
                except Exception as e:
                    print(f"⚠️ Erreur caméra Pi: {e}")

            # Sinon fallback USB
            print("🔄 Fallback → Webcam USB")
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

    # -------------------------------------------------------------------------
    # FRAME CAPTURE
    # -------------------------------------------------------------------------
    def get_frame(self):
        # ESP32 Dual Cam
        if self.active_camera.startswith("esp32") and self.esp32_dual_camera:
            cam_key = "cam1" if self.active_camera == "esp32_cam1" else "cam2"
            frame = self.esp32_dual_camera.get_frame(cam_key)
            if frame is not None:
                return frame
            
            print("🔄 Fallback ESP32 → USB")
            self.active_camera = "usb"

        # Webcam USB (Windows / Fallback Pi)
        if self.active_camera == "usb" and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame

        # Picamera2 (Raspberry)
        if self.active_camera == "usb" and self.picam2:
            frame = self.picam2.capture_array()
            return frame

        return None

    # -------------------------------------------------------------------------
    def switch_camera(self):
        if not self.available_cameras:
            return self.active_camera
        
        idx = self.available_cameras.index(self.active_camera)
        self.active_camera = self.available_cameras[(idx + 1) % len(self.available_cameras)]
        
        names = {
            "usb": "Caméra principale",
            "esp32_cam1": "ESP32 Cam 1",
            "esp32_cam2": "ESP32 Cam 2",
        }
        
        print(f"📷 Caméra activée: {names.get(self.active_camera, self.active_camera)}")
        return self.active_camera

    # -------------------------------------------------------------------------
    def toggle_esp32_flash(self):
        if self.esp32_dual_camera:
            return self.esp32_dual_camera.toggle_flash()
        print("❌ ESP32 non disponible pour le flash")
        return False

    # -------------------------------------------------------------------------
    def get_camera_status(self):
        return {
            "active_camera": self.active_camera,
            "available_cameras": self.available_cameras,
            "usb_available": self.cap is not None and self.cap.isOpened(),
            "esp32_available": self.esp32_dual_camera is not None,
            "picam_available": self.picam2 is not None,
        }

    # -------------------------------------------------------------------------
    def release(self):
        if self.cap:
            self.cap.release()
        if self.picam2:
            self.picam2.close()
        if self.esp32_dual_camera:
            self.esp32_dual_camera.stop_streaming()

        print("🟢 Toutes les caméras libérées")
