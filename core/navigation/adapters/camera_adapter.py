"""
Adaptateur pour la caméra Raspberry Pi.
Support PiCamera v2/v3 et webcam USB.
"""
import time
import logging
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class CameraAdapter:
    """Adaptateur pour différentes caméras."""
    
    def __init__(self, config: dict):
        """
        Initialise l'adaptateur caméra.
        
        Args:
            config: Configuration de la caméra
        """
        self.config = config
        self.camera = None
        self.camera_type = None
        self.last_frame_time = 0
        
        self._initialize_camera()
        
        logger.info(f"CameraAdapter initialisé: {self.camera_type}, "
                   f"{config['width']}x{config['height']} @ {config['fps']} FPS")
    
    def _initialize_camera(self):
        """Initialise la caméra selon le matériel disponible."""
        try:
            # Essayer PiCamera d'abord (pour Raspberry Pi)
            from picamera2 import Picamera2
            from libcamera import controls
            
            self.camera = Picamera2()
            
            # Configurer la caméra
            config = self.camera.create_video_configuration(
                main={"size": (self.config['width'], self.config['height']),
                      "format": "RGB888"},
                controls={
                    "FrameRate": self.config['fps'],
                    "AwbMode": controls.AwbModeEnum.Auto,
                    "AeEnable": True,
                    "ExposureTime": 10000
                }
            )
            
            self.camera.configure(config)
            self.camera.start()
            self.camera_type = "picamera2"
            
            logger.info("PiCamera2 initialisé avec succès")
            
        except ImportError:
            logger.warning("PiCamera2 non disponible, tentative avec OpenCV...")
            self._initialize_opencv()
    
    def _initialize_opencv(self):
        """Initialise avec OpenCV (pour webcam USB)."""
        try:
            import cv2
            
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise RuntimeError("Impossible d'ouvrir la caméra")
            
            # Configurer la résolution et FPS
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['width'])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['height'])
            self.camera.set(cv2.CAP_PROP_FPS, self.config['fps'])
            
            # Vérifier la configuration
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width != self.config['width'] or actual_height != self.config['height']:
                logger.warning(f"Résolution demandée {self.config['width']}x{self.config['height']} "
                             f"non supportée, utilisation de {actual_width}x{actual_height}")
                self.config['width'] = actual_width
                self.config['height'] = actual_height
            
            self.camera_type = "opencv"
            logger.info(f"OpenCV camera initialisé: {actual_width}x{actual_height}")
            
        except Exception as e:
            logger.error(f"Échec initialisation caméra: {e}")
            raise RuntimeError(f"Impossible d'initialiser la caméra: {e}")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture une frame de la caméra.
        
        Returns:
            Image numpy array (RGB) ou None en cas d'erreur
        """
        try:
            self.last_frame_time = time.time()
            
            if self.camera_type == "picamera2":
                # Capture avec PiCamera2
                frame = self.camera.capture_array()
                
                # Convertir en RGB si nécessaire
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    # Déjà RGB
                    pass
                else:
                    # Convertir BGR à RGB
                    frame = frame[:, :, ::-1]
                
            elif self.camera_type == "opencv":
                # Capture avec OpenCV
                import cv2
                
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Échec capture frame OpenCV")
                    return None
                
                # OpenCV utilise BGR, convertir en RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Rotation si configuré
                if self.config.get('rotation', 0) != 0:
                    rotation_code = {
                        90: cv2.ROTATE_90_CLOCKWISE,
                        180: cv2.ROTATE_180,
                        270: cv2.ROTATE_90_COUNTERCLOCKWISE
                    }.get(self.config['rotation'])
                    if rotation_code:
                        frame = cv2.rotate(frame, rotation_code)
            else:
                return None
            
            return frame
            
        except Exception as e:
            logger.error(f"Erreur capture frame: {e}")
            return None
    
    def get_frame_rate(self) -> float:
        """Retourne le taux de capture réel."""
        return self.config['fps']
    
    def get_resolution(self) -> Tuple[int, int]:
        """Retourne la résolution (width, height)."""
        return (self.config['width'], self.config['height'])
    
    def get_fov(self) -> float:
        """Retourne le champ de vision en degrés."""
        return self.config['fov_deg']
    
    def adjust_exposure(self, brightness: float):
        """Ajuste l'exposition (0-1)."""
        if self.camera_type == "picamera2":
            try:
                from libcamera import controls
                # Convertir brightness à valeur d'exposition
                exposure = int(10000 * brightness)
                self.camera.set_controls({"ExposureTime": exposure})
            except:
                pass
    
    def close(self):
        """Ferme la caméra proprement."""
        if self.camera:
            if self.camera_type == "picamera2":
                self.camera.stop()
                self.camera.close()
            elif self.camera_type == "opencv":
                import cv2
                self.camera.release()
            
            logger.info("Caméra fermée")
    
    def __del__(self):
        """Destructeur."""
        self.close()