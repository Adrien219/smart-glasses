import cv2
import numpy as np
import requests
import time

class StereoVision:
    def __init__(self, esp32_cam_urls):
        # URLs des deux caméras ESP32
        self.cam_left_url = esp32_cam_urls[0]   # ex: "http://192.168.1.100/capture"
        self.cam_right_url = esp32_cam_urls[1]  # ex: "http://192.168.1.101/capture"
        
        # Calibration stéréo (à ajuster selon tes caméras)
        self.focal_length = 800
        self.baseline = 0.12  # 12cm entre les deux caméras
        
    def get_stereo_frames(self):
        """Capturer des images des deux caméras ESP32"""
        try:
            # Capturer image gauche
            response_left = requests.get(self.cam_left_url, timeout=2)
            img_left = cv2.imdecode(np.frombuffer(response_left.content, np.uint8), cv2.IMREAD_COLOR)
            
            # Capturer image droite  
            response_right = requests.get(self.cam_right_url, timeout=2)
            img_right = cv2.imdecode(np.frombuffer(response_right.content, np.uint8), cv2.IMREAD_COLOR)
            
            return img_left, img_right
            
        except Exception as e:
            print(f"❌ Erreur capture stéréo: {e}")
            return None, None
    
    def calculate_depth_map(self, img_left, img_right):
        """Calculer la carte de profondeur"""
        # Convertir en niveaux de gris
        gray_left = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY)
        gray_right = cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)
        
        # Créer le matcher stéréo
        stereo = cv2.StereoSGBM_create(
            minDisparity=0,
            numDisparities=64,
            blockSize=5,
            P1=8*3*5**2,
            P2=32*3*5**2,
            disp12MaxDiff=1,
            uniquenessRatio=10,
            speckleWindowSize=100,
            speckleRange=32
        )
        
        # Calculer la disparité
        disparity = stereo.compute(gray_left, gray_right)
        
        # Convertir en profondeur réelle
        depth = np.zeros_like(disparity, dtype=np.float32)
        depth[disparity > 0] = (self.focal_length * self.baseline) / disparity[disparity > 0]
        
        return depth
    
    def get_obstacle_distances(self, depth_map):
        """Analyser la carte de profondeur pour détecter les obstacles"""
        h, w = depth_map.shape
        
        # Diviser l'image en zones (gauche, centre, droite)
        left_zone = depth_map[:, :w//3]
        center_zone = depth_map[:, w//3:2*w//3] 
        right_zone = depth_map[:, 2*w//3:]
        
        # Calculer la distance moyenne dans chaque zone
        zones = {
            "gauche": np.mean(left_zone[left_zone > 0]) if np.any(left_zone > 0) else float('inf'),
            "centre": np.mean(center_zone[center_zone > 0]) if np.any(center_zone > 0) else float('inf'),
            "droite": np.mean(right_zone[right_zone > 0]) if np.any(right_zone > 0) else float('inf')
        }
        
        return zones