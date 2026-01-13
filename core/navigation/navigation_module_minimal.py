"""
NavigationModule - Version minimale fonctionnelle
"""
import threading
import queue
import time
import yaml
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class NavigationState(Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    ALERT = "alert"
    GUIDANCE = "guidance"
    EMERGENCY = "emergency"

class NavigationModule:
    def __init__(self, config_path="config/navigation.yaml"):
        self.load_config(config_path)
        
        # États
        self.state = NavigationState.IDLE
        self.running = False
        
        # Composants
        self.camera_adapter = None
        self.arduino_manager = None
        self.object_detector = None
        self.eoh = None
        
        # Queues
        self.frame_queue = queue.Queue(maxsize=3)
        self.fusion_queue = queue.Queue(maxsize=5)
        
        # Variables Arduino
        self.last_ultrasound_data = None
        self.last_ultrasound_time = 0
        self.current_light_level = 512
        
        # Statistiques
        self.stats = {
            'start_time': time.time(),
            'frames_processed': 0,
            'detections_count': 0,
            'warnings_issued': 0,
            'arduino_readings': 0
        }
        
        # Télémetrie
        self.telemetry = {
            'arduino': {
                'connection_status': 'disconnected',
                'last_ultrasonic': None,
                'last_light': None
            }
        }
        
        logger.info("NavigationModule (minimal) initialisé")
    
    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Configuration chargée depuis {config_path}")
        except FileNotFoundError:
            logger.warning("Configuration non trouvée, valeurs par défaut")
            self.config = {
                'arduino': {'port': '/dev/ttyUSB0', 'baudrate': 115200},
                'camera': {'fps': 10, 'width': 1280, 'height': 720}
            }
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.stats['start_time'] = time.time()
        
        try:
            # Initialiser ArduinoManager
            from .arduino_manager import ArduinoManager
            self.arduino_manager = ArduinoManager(
                port=self.config['arduino']['port'],
                baudrate=self.config['arduino']['baudrate']
            )
            self.arduino_manager.register_callback(self._on_arduino_data)
            
            if self.arduino_manager.start():
                self.telemetry['arduino']['connection_status'] = 'connected'
                logger.info("✅ ArduinoManager démarré")
            else:
                logger.warning("ArduinoManager n'a pas pu démarrer")
            
            # Démarrer les threads
            self.threads = []
            self.threads.append(threading.Thread(target=self._camera_loop, daemon=True))
            self.threads.append(threading.Thread(target=self._fusion_loop, daemon=True))
            
            for thread in self.threads:
                thread.start()
            
            self.state = NavigationState.SCANNING
            logger.info("✅ NavigationModule démarré")
            
        except Exception as e:
            logger.error(f"Erreur au démarrage: {e}")
            self.stop()
            raise
    
    def _on_arduino_data(self, data_type, value):
        self.stats['arduino_readings'] += 1
        
        if data_type == 'ULTRASONIC':
            try:
                distance = float(value)
                self.last_ultrasound_data = {
                    'distance': distance,
                    'angle': 0.0,
                    'timestamp': time.time()
                }
                self.last_ultrasound_time = time.time()
                self.telemetry['arduino']['last_ultrasonic'] = distance
            except ValueError:
                pass
        elif data_type == 'LIGHT':
            try:
                self.current_light_level = int(value)
                self.telemetry['arduino']['last_light'] = self.current_light_level
            except ValueError:
                pass
    
    def _camera_loop(self):
        while self.running:
            try:
                time.sleep(0.1)  # Simuler la capture
            except Exception as e:
                logger.error(f"Erreur camera_loop: {e}")
                time.sleep(0.1)
    
    def _fusion_loop(self):
        while self.running:
            try:
                time.sleep(0.1)  # Simuler la fusion
            except Exception as e:
                logger.error(f"Erreur fusion_loop: {e}")
                time.sleep(0.1)
    
    def test_arduino_connection(self):
        if not self.arduino_manager:
            return {'status': 'no_manager', 'message': 'ArduinoManager non initialisé'}
        
        try:
            if self.arduino_manager.is_connected():
                return {
                    'status': 'connected',
                    'message': 'Arduino connecté',
                    'ultrasonic': self.last_ultrasound_data,
                    'light': self.current_light_level,
                    'port': self.config['arduino']['port']
                }
            else:
                return {
                    'status': 'disconnected',
                    'message': 'Arduino non connecté',
                    'port': self.config['arduino']['port']
                }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_state(self):
        return {
            'module_state': self.state.value,
            'running': self.running,
            'arduino_status': self.telemetry['arduino'],
            'statistics': self.stats
        }
    
    def get_sensor_data(self):
        return {
            'ultrasonic': {
                'last_reading': self.last_ultrasound_data,
                'last_time': self.last_ultrasound_time
            },
            'light': {
                'level': self.current_light_level
            }
        }
    
    def stop(self):
        if not self.running:
            return
        
        logger.info("Arrêt du NavigationModule...")
        self.running = False
        
        if self.arduino_manager:
            self.arduino_manager.stop()
        
        self.state = NavigationState.IDLE
        
        total_time = time.time() - self.stats['start_time']
        logger.info(f"Statistiques: {self.stats}")
        logger.info(f"Temps total: {total_time:.1f}s")
        
        return True
