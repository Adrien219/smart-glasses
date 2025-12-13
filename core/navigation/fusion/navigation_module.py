"""
Module principal de navigation pour smart-glasses.
Orchestre capteurs, perception, fusion et décision.
"""
import threading
import queue
import time
import yaml
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

class NavigationState(Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    ALERT = "alert"
    GUIDANCE = "guidance"
    EMERGENCY = "emergency"
    RECOVER = "recover"

@dataclass
class Detection:
    """Représente un objet détecté."""
    class_name: str
    confidence: float
    bbox: tuple  # (x, y, w, h) normalisé [0,1]
    distance_estimate: Optional[float] = None  # en cm
    bearing: Optional[float] = None  # en degrés (-gauche, +droite)
    timestamp: float = None

@dataclass
class UltrasonicReading:
    distance_cm: float
    timestamp: float

class NavigationModule:
    """Module principal de navigation."""
    
    def __init__(self, config_path: str = "config/navigation.yaml"):
        """
        Initialise le module de navigation.
        
        Args:
            config_path: Chemin vers le fichier de configuration.
        """
        self.load_config(config_path)
        
        # États et contrôle
        self.state = NavigationState.IDLE
        self.running = False
        self.callbacks = {
            'on_alert': [],
            'on_state_change': [],
            'on_telemetry': []
        }
        
        # Composants
        self.camera_adapter = None
        self.ultra_adapter = None
        self.eoh = None
        self.priority_engine = None
        self.tts_service = None
        
        # Queues pour communication inter-threads
        self.frame_queue = queue.Queue(maxsize=2)
        self.ultra_queue = queue.Queue(maxsize=10)
        self.detection_queue = queue.Queue(maxsize=5)
        self.tts_queue = queue.PriorityQueue(maxsize=10)
        
        # Threads
        self.threads = []
        
        # Télémetrie
        self.telemetry = {
            'last_alert': None,
            'fps': {'camera': 0, 'detection': 0},
            'latency': {'detection': 0, 'tts': 0}
        }
        
        logger.info("NavigationModule initialisé")
    
    def load_config(self, config_path: str):
        """Charge la configuration depuis un fichier YAML."""
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Configuration chargée depuis {config_path}")
        except FileNotFoundError:
            logger.warning(f"Fichier de configuration {config_path} non trouvé, utilisation des valeurs par défaut")
            self.config = self._default_config()
    
    def _default_config(self):
        """Configuration par défaut."""
        return {
            'camera': {
                'fov_deg': 62.2,
                'width': 1280,
                'height': 720,
                'fps': 5
            },
            'ultrasonic': {
                'trig_pin': 23,
                'echo_pin': 24,
                'sample_rate_hz': 10
            },
            'fusion': {
                'eoh_bins': 13,
                'ema_alpha': 0.4,
                'association_window_ms': 150
            },
            'thresholds': {
                'emergency_dist_cm': 30,
                'alert_dist_cm': 80,
                'persist_ms': 200,
                'min_vocal_interval_s': 3
            },
            'tts': {
                'model_name': 'tts_models/fr/mai/tacotron2-DDC',
                'async': True
            }
        }
    
    def start(self):
        """Démarre tous les composants du module."""
        if self.running:
            logger.warning("NavigationModule déjà démarré")
            return
        
        self.running = True
        
        try:
            # Initialiser les adaptateurs
            from .adapters.camera_adapter import CameraAdapter
            from .adapters.hc_sr04_adapter import UltrasonicAdapter
            from .fusion.eoh import EgocentricOccupancyHistogram
            from .decision.priority_engine import PriorityEngine
            from .tts.coqui_tts_service import TTSWorker
            
            self.camera_adapter = CameraAdapter(self.config['camera'])
            self.ultra_adapter = UltrasonicAdapter(
                trig_pin=self.config['ultrasonic']['trig_pin'],
                echo_pin=self.config['ultrasonic']['echo_pin']
            )
            
            # Initialiser les composants de fusion et décision
            self.eoh = EgocentricOccupancyHistogram(
                bins=self.config['fusion']['eoh_bins'],
                fov_deg=self.config['camera']['fov_deg']
            )
            
            self.priority_engine = PriorityEngine(
                emergency_dist=self.config['thresholds']['emergency_dist_cm'],
                alert_dist=self.config['thresholds']['alert_dist_cm'],
                min_vocal_interval=self.config['thresholds']['min_vocal_interval_s']
            )
            
            # Initialiser TTS
            self.tts_service = TTSWorker(
                config=self.config['tts'],
                tts_queue=self.tts_queue
            )
            
            # Démarrer les threads
            self._start_threads()
            
            # Transition vers l'état SCANNING
            self._set_state(NavigationState.SCANNING)
            
            logger.info("NavigationModule démarré avec succès")
            
        except Exception as e:
            logger.error(f"Erreur au démarrage: {e}")
            self.stop()
            raise
    
    def _start_threads(self):
        """Démarre tous les threads de traitement."""
        threads_config = [
            (self._camera_capture_loop, "CamCapture"),
            (self._ultrasonic_loop, "UltraSensor"),
            (self._perception_loop, "Perception"),
            (self._fusion_loop, "Fusion"),
            (self._decision_loop, "Decision"),
            (self._telemetry_loop, "Telemetry")
        ]
        
        for target, name in threads_config:
            thread = threading.Thread(target=target, name=name, daemon=True)
            thread.start()
            self.threads.append(thread)
        
        # Démarrer TTS dans son propre thread
        tts_thread = threading.Thread(
            target=self.tts_service.run,
            name="TTSWorker",
            daemon=True
        )
        tts_thread.start()
        self.threads.append(tts_thread)
    
    def stop(self):
        """Arrête proprement tous les composants."""
        self.running = False
        self._set_state(NavigationState.IDLE)
        
        # Arrêter les adaptateurs
        if self.camera_adapter:
            self.camera_adapter.close()
        if self.ultra_adapter:
            self.ultra_adapter.cleanup()
        
        # Vider les queues
        for q in [self.frame_queue, self.ultra_queue, 
                  self.detection_queue, self.tts_queue]:
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    pass
        
        # Attendre la fin des threads
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        logger.info("NavigationModule arrêté")
    
    def _camera_capture_loop(self):
        """Thread de capture vidéo."""
        from .perception.yolo_wrapper import ObjectDetector
        
        detector = ObjectDetector()
        fps_counter = 0
        last_fps_time = time.time()
        
        while self.running:
            try:
                # Capturer une frame
                frame = self.camera_adapter.capture_frame()
                if frame is None:
                    continue
                
                # Détection d'objets
                detections = detector.detect(frame)
                
                # Ajouter timestamp
                timestamp = time.time()
                for det in detections:
                    det.timestamp = timestamp
                
                # Mettre dans la queue (non bloquant)
                try:
                    self.detection_queue.put_nowait((frame, detections))
                except queue.Full:
                    # Jeter la frame la plus ancienne si nécessaire
                    try:
                        self.detection_queue.get_nowait()
                        self.detection_queue.put_nowait((frame, detections))
                    except queue.Empty:
                        pass
                
                # Calcul FPS
                fps_counter += 1
                if time.time() - last_fps_time >= 1.0:
                    self.telemetry['fps']['camera'] = fps_counter
                    fps_counter = 0
                    last_fps_time = time.time()
                    
            except Exception as e:
                logger.error(f"Erreur dans camera_capture_loop: {e}")
                time.sleep(0.1)
    
    def _ultrasonic_loop(self):
        """Thread de lecture du capteur ultrasonique."""
        while self.running:
            try:
                distance = self.ultra_adapter.get_distance()
                reading = UltrasonicReading(
                    distance_cm=distance,
                    timestamp=time.time()
                )
                
                try:
                    self.ultra_queue.put_nowait(reading)
                except queue.Full:
                    # Garder seulement la dernière lecture
                    try:
                        self.ultra_queue.get_nowait()
                        self.ultra_queue.put_nowait(reading)
                    except queue.Empty:
                        pass
                
                # Respecter le taux d'échantillonnage
                time.sleep(1.0 / self.config['ultrasonic']['sample_rate_hz'])
                
            except Exception as e:
                logger.error(f"Erreur dans ultrasonic_loop: {e}")
                time.sleep(0.5)
    
    def _fusion_loop(self):
        """Thread de fusion des données."""
        while self.running:
            try:
                # Récupérer les dernières données
                ultra_readings = []
                while not self.ultra_queue.empty():
                    ultra_readings.append(self.ultra_queue.get_nowait())
                
                # Prendre la dernière détection
                try:
                    frame, detections = self.detection_queue.get_nowait()
                    # Fusionner les données
                    self._fuse_data(detections, ultra_readings)
                except queue.Empty:
                    # Pas de nouvelle détection, continuer
                    pass
                
                time.sleep(0.05)  # 20 Hz
                
            except Exception as e:
                logger.error(f"Erreur dans fusion_loop: {e}")
    
    def _fuse_data(self, detections: List[Detection], 
                   ultra_readings: List[UltrasonicReading]):
        """Fusionne les détections vision et ultrasons."""
        if not ultra_readings:
            return
        
        # Prendre la dernière lecture ultra
        latest_ultra = ultra_readings[-1]
        
        for detection in detections:
            # Calculer le bearing (position angulaire)
            if detection.bbox:
                center_x = detection.bbox[0] + detection.bbox[2] / 2
                # Convertir en degrés (-FOV/2 à +FOV/2)
                fov = self.config['camera']['fov_deg']
                detection.bearing = (center_x - 0.5) * fov
            
            # Associer avec ultrason si au centre
            if (detection.bearing and 
                abs(detection.bearing) < 10):  # ±10° au centre
                detection.distance_estimate = latest_ultra.distance_cm
            
            # Mettre à jour l'histogramme EOH
            if detection.distance_estimate and detection.bearing:
                self.eoh.update(
                    bearing=detection.bearing,
                    distance=detection.distance_estimate,
                    confidence=detection.confidence,
                    timestamp=detection.timestamp
                )
    
    def _decision_loop(self):
        """Thread de prise de décision."""
        last_vocal_time = 0
        
        while self.running:
            try:
                snapshot = self.eoh.get_snapshot()
                
                # Prendre décision via PriorityEngine
                decision = self.priority_engine.evaluate(snapshot)
                
                if decision.action_needed:
                    # Vérifier le délai entre messages vocaux
                    current_time = time.time()
                    if (current_time - last_vocal_time >= 
                        self.config['thresholds']['min_vocal_interval_s']):
                        
                        # Ajouter à la file TTS
                        self.tts_queue.put((
                            decision.priority.value,  # Priorité (plus bas = plus urgent)
                            {
                                'text': decision.message,
                                'priority': decision.priority
                            }
                        ))
                        
                        last_vocal_time = current_time
                        
                        # Déclencher les callbacks
                        self._trigger_callbacks('on_alert', {
                            'type': decision.alert_type,
                            'distance': snapshot.min_distance,
                            'bearing': snapshot.closest_bearing,
                            'suggested_action': decision.suggested_action,
                            'confidence': decision.confidence
                        })
                
                # Mettre à jour l'état
                if decision.new_state:
                    self._set_state(decision.new_state)
                
                time.sleep(0.1)  # 10 Hz
                
            except Exception as e:
                logger.error(f"Erreur dans decision_loop: {e}")
    
    def _telemetry_loop(self):
        """Thread de télémetrie et logging."""
        while self.running:
            try:
                # Mettre à jour la télémetrie
                snapshot = self.eoh.get_snapshot()
                self.telemetry.update({
                    'eoh_snapshot': snapshot.to_dict(),
                    'state': self.state.value,
                    'timestamp': time.time()
                })
                
                # Déclencher callback télémetrie
                self._trigger_callbacks('on_telemetry', self.telemetry)
                
                time.sleep(1.0)  # 1 Hz
                
            except Exception as e:
                logger.error(f"Erreur dans telemetry_loop: {e}")
    
    def _perception_loop(self):
        """Thread de perception (placeholder pour OCR/Face)."""
        # À implémenter selon besoins
        while self.running:
            time.sleep(1.0)
    
    def _set_state(self, new_state: NavigationState):
        """Change l'état du module."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            logger.info(f"État changé: {old_state} -> {new_state}")
            
            # Déclencher callback
            self._trigger_callbacks('on_state_change', {
                'old_state': old_state.value,
                'new_state': new_state.value
            })
    
    def _trigger_callbacks(self, event_name: str, data: Dict):
        """Déclenche tous les callbacks pour un événement."""
        for callback in self.callbacks[event_name]:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Erreur dans callback {event_name}: {e}")
    
    def register_callback(self, event_name: str, callback: Callable):
        """Enregistre un callback pour un événement."""
        if event_name in self.callbacks:
            self.callbacks[event_name].append(callback)
        else:
            logger.warning(f"Événement {event_name} non reconnu")
    
    def get_state(self) -> Dict:
        """Retourne l'état courant du module."""
        return {
            'state': self.state.value,
            'eoh_snapshot': self.eoh.get_snapshot().to_dict() if self.eoh else None,
            'telemetry': self.telemetry,
            'running': self.running
        }
    
    def calibrate_camera(self, camera_params: Dict):
        """Calibre les paramètres de la caméra."""
        # À implémenter selon méthode de calibration
        logger.info(f"Calibration caméra: {camera_params}")
    
    def set_thresholds(self, thresholds: Dict):
        """Met à jour les seuils de détection."""
        if 'emergency_dist_cm' in thresholds:
            self.config['thresholds']['emergency_dist_cm'] = thresholds['emergency_dist_cm']
        if 'alert_dist_cm' in thresholds:
            self.config['thresholds']['alert_dist_cm'] = thresholds['alert_dist_cm']
        if 'min_vocal_interval_s' in thresholds:
            self.config['thresholds']['min_vocal_interval_s'] = thresholds['min_vocal_interval_s']
        
        logger.info(f"Seuils mis à jour: {thresholds}")
    
    def force_announce(self, text: str, priority: str = 'low'):
        """Force l'annonce d'un message (debug/manuel)."""
        priority_map = {
            'low': 3,
            'medium': 2,
            'high': 1,
            'emergency': 0
        }
        
        self.tts_queue.put((
            priority_map.get(priority, 3),
            {'text': text, 'priority': priority}
        ))
        
        logger.info(f"Message forcé: {text} (priorité: {priority})")
    
    def get_sensor_data(self) -> Dict:
        """Retourne les dernières données des capteurs (debug)."""
        ultra_data = []
        while not self.ultra_queue.empty():
            ultra_data.append(self.ultra_queue.get_nowait())
        
        return {
            'ultrasonic': ultra_data[-1] if ultra_data else None,
            'queue_sizes': {
                'frame': self.frame_queue.qsize(),
                'ultra': self.ultra_queue.qsize(),
                'detection': self.detection_queue.qsize(),
                'tts': self.tts_queue.qsize()
            }
        }