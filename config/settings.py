import os

class Config:
    # Chemins
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # YOLO
    YOLO_MODEL = "yolov8n.pt"
    CONFIDENCE_THRESHOLD = 0.25
    
    # Caméra USB Raspberry Pi
    CAMERA_ID = 0
    CAMERA_RESOLUTION = (640, 480)
    CAMERA_FPS = 15
    
    # Arduino
    ARDUINO_PORTS = ["COM4", "COM3", "COM5", "COM6", "/dev/ttyUSB0", "/dev/ttyACM0"]
    ARDUINO_BAUDRATE = 9600
    ARDUINO_TIMEOUT = 3
    
    # ESP32 Double Caméra - CONFIGURATION COMPLÈTE
    ESP32_IP = "192.168.4.1"  # IP par défaut de l'ESP32 en mode AP
    ESP32_PORT = 80
    
    # URLs pour les caméras ESP32
    ESP32_CAM_URL = f"http://{ESP32_IP}:{ESP32_PORT}/cam"  # URL simple par défaut
    ESP32_CAM1_URL = f"http://{ESP32_IP}:{ESP32_PORT}/cam1"
    ESP32_CAM2_URL = f"http://{ESP32_IP}:{ESP32_PORT}/cam2"
    ESP32_FLASH_URL = f"http://{ESP32_IP}:{ESP32_PORT}/flash"
    
    # Sélection caméra
    PREFER_ESP32_CAMERAS = False  # Désactivé par défaut pour éviter les erreurs
    ACTIVE_ESP32_CAMERA = "cam1"
    
    # Traitement
    PROCESSING_INTERVAL = 2.0
    
    # Audio
    LANGUAGE = "fr"
    VOICE_ENABLED = True
    AUDIO_ANNOUNCE_COOLDOWN = 3
    
    # Navigation
    ULTRASONIC_THRESHOLD = 1.0
    
    # Débogage
    DEBUG_MODE = True
    SAVE_DETECTION_IMAGES = False



 # Configuration caméra
    CAMERA_ID = 0
    CAMERA_RESOLUTION = (640, 480)
    
    # Configuration ESP32
    ESP32_CAM_URL = "http://192.168.4.1"
    
    # Intervalles de traitement
    PROCESSING_INTERVAL = 2.0
    
    # Classes cibles pour la détection
    TARGET_OBJECTS = ["person", "car", "chair", "bottle", "cup"]
    
    # Chemins des modèles
    YOLO_MODEL_PATH = "yolov8n.pt"
    FACES_DIR = "models/faces"


    
    @classmethod
    def get_arduino_port(cls):
        """Trouve automatiquement le port Arduino"""
        import serial.tools.list_ports
        
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if any(arduino_port in port.device for arduino_port in cls.ARDUINO_PORTS):
                print(f"✅ Arduino trouvé sur: {port.device}")
                return port.device
        
        print("❌ Aucun Arduino trouvé, utilisation manuelle nécessaire")
        return cls.ARDUINO_PORTS[0] if cls.ARDUINO_PORTS else "COM4"