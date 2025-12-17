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
from datetime import datetime

logger = logging.getLogger(__name__)

class NavigationState(Enum):
    """États du module de navigation."""
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
    """Lecture du capteur ultrasonique."""
    distance_cm: float
    timestamp: float

@dataclass
class Decision:
    """Décision prise par le moteur de priorité."""
    action_needed: bool = False
    message: str = ""
    priority: int = 0  # 0=urgence, 1=haute, 2=moyenne, 3=basse
    suggested_action: str = ""
    alert_type: str = ""
    confidence: float = 0.0
    new_state: Optional[NavigationState] = None

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
            'on_telemetry': [],
            'on_guidance': []
        }
        
        # Composants
        self.camera_adapter = None
        self.ultra_adapter = None
        self.eoh = None
        self.priority_engine = None
        self.guidance_planner = None
        self.tts_service = None
        self.object_detector = None
        
        # Queues pour communication inter-threads
        self.frame_queue = queue.Queue(maxsize=3)
        self.ultra_queue = queue.Queue(maxsize=10)
        self.detection_queue = queue.Queue(maxsize=5)
        self.tts_queue = queue.PriorityQueue(maxsize=20)
        self.fusion_queue = queue.Queue(maxsize=5)
        
        # Threads
        self.threads = []
        
        # Télémetrie
        self.telemetry = {
            'last_alert': None,
            'fps': {'camera': 0, 'detection': 0, 'fusion': 0},
            'latency': {'detection': 0, 'fusion': 0, 'decision': 0},
            'state_history': [],
            'obstacles_detected': 0
        }
        
        # Statistiques
        self.stats = {
            'start_time': time.time(),
            'frames_processed': 0,
            'detections_count': 0,
            'warnings_issued': 0
        }
        
        # Messages récents (pour éviter répétition)
        self.recent_messages = {}
        
        logger.info("NavigationModule initialisé (version 1.0)")
    
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
                'fps': 10,
                'rotation': 0
            },
            'ultrasonic': {
                'trig_pin': 23,
                'echo_pin': 24,
                'sample_rate_hz': 15,
                'max_distance_cm': 400,
                'timeout_us': 30000
            },
            'detection': {
                'model_path': 'models/yolov8n.pt',
                'confidence_threshold': 0.5,
                'iou_threshold': 0.3,
                'classes': [0, 1, 2, 3, 5, 7],  # person, bicycle, car, motorcycle, bus, truck
                'track': True
            },
            'fusion': {
                'eoh_bins': 13,
                'ema_alpha': 0.4,
                'association_window_ms': 150,
                'max_object_age_s': 2.0,
                'min_confidence': 0.3
            },
            'thresholds': {
                'emergency_dist_cm': 35,
                'alert_dist_cm': 100,
                'warning_dist_cm': 200,
                'persist_ms': 300,
                'min_vocal_interval_s': 2.5,
                'recovery_time_s': 1.5
            },
            'guidance': {
                'clear_path_threshold_cm': 150,
                'min_safe_angle_deg': 20,
                'preferred_direction': 'right'  # 'left' or 'right'
            },
            'tts': {
                'model_name': 'tts_models/fr/mai/tacotron2-DDC',
                'speaker_wav': None,
                'use_cuda': False,
                'cache_dir': 'tts_cache',
                'preload_phrases': True
            },
            'system': {
                'debug_mode': False,
                'log_level': 'INFO',
                'save_telemetry': True,
                'telemetry_interval_s': 5
            }
        }
    
    def start(self):
        """Démarre tous les composants du module."""
        if self.running:
            logger.warning("NavigationModule déjà démarré")
            return
        
        self.running = True
        self.stats['start_time'] = time.time()
        
        try:
            # Initialiser les adaptateurs
            from .adapters.camera_adapter import CameraAdapter
            from .adapters.hc_sr04_adapter import UltrasonicAdapter
            
            # Initialiser les composants de perception
            from .perception.yolo_wrapper import ObjectDetector
            
            # Initialiser les composants de fusion et décision
            from .fusion.eoh import EgocentricOccupancyHistogram
            from .decision.priority_engine import PriorityEngine
            from .decision.guidance_planner import GuidancePlanner
            
            # Initialiser TTS
            from .tts.coqui_tts_service import TTSWorker
            
            logger.info("Initialisation des composants...")
            
            # Créer les instances
            self.camera_adapter = CameraAdapter(self.config['camera'])
            self.ultra_adapter = UltrasonicAdapter(
                trig_pin=self.config['ultrasonic']['trig_pin'],
                echo_pin=self.config['ultrasonic']['echo_pin'],
                max_distance=self.config['ultrasonic']['max_distance_cm'],
                timeout_us=self.config['ultrasonic']['timeout_us']
            )
            
            self.object_detector = ObjectDetector(
                model_path=self.config['detection']['model_path'],
                confidence_threshold=self.config['detection']['confidence_threshold'],
                classes=self.config['detection']['classes']
            )
            
            self.eoh = EgocentricOccupancyHistogram(
                bins=self.config['fusion']['eoh_bins'],
                fov_deg=self.config['camera']['fov_deg'],
                ema_alpha=self.config['fusion']['ema_alpha']
            )
            
            self.priority_engine = PriorityEngine(
                emergency_dist=self.config['thresholds']['emergency_dist_cm'],
                alert_dist=self.config['thresholds']['alert_dist_cm'],
                warning_dist=self.config['thresholds']['warning_dist_cm'],
                min_vocal_interval=self.config['thresholds']['min_vocal_interval_s']
            )
            
            self.guidance_planner = GuidancePlanner(
                clear_path_threshold=self.config['guidance']['clear_path_threshold_cm'],
                min_safe_angle=self.config['guidance']['min_safe_angle_deg'],
                preferred_direction=self.config['guidance']['preferred_direction']
            )
            
            self.tts_service = TTSWorker(
                config=self.config['tts'],
                tts_queue=self.tts_queue
            )
            
            # Démarrer les threads
            self._start_threads()
            
            # Transition vers l'état SCANNING
            self._set_state(NavigationState.SCANNING)
            
            logger.info("NavigationModule démarré avec succès")
            
            # Pré-charger les messages vocaux critiques
            if self.config['tts'].get('preload_phrases', True):
                self._preload_tts_phrases()
            
        except Exception as e:
            logger.error(f"Erreur au démarrage: {e}", exc_info=True)
            self.stop()
            raise
    
    def _preload_tts_phrases(self):
        """Pré-charge les phrases TTS critiques pour réduire la latence."""
        critical_phrases = [
            "Attention, obstacle très proche",
            "Arrêtez-vous immédiatement",
            "Déplacez-vous à gauche",
            "Déplacez-vous à droite",
            "Zone dégagée"
        ]
        
        logger.info("Pré-chargement des phrases TTS critiques...")
        for phrase in critical_phrases:
            self.tts_service.preload_phrase(phrase)
    
    def _start_threads(self):
        """Démarre tous les threads de traitement."""
        threads_config = [
            (self._camera_capture_loop, "CamCapture"),
            (self._ultrasonic_loop, "UltraSensor"),
            (self._detection_loop, "Perception"),
            (self._fusion_loop, "Fusion"),
            (self._decision_loop, "Decision"),
            (self._guidance_loop, "Guidance"),
            (self._telemetry_loop, "Telemetry"),
            (self._health_monitor_loop, "HealthMonitor")
        ]
        
        for target, name in threads_config:
            thread = threading.Thread(
                target=target,
                name=f"Nav-{name}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            logger.debug(f"Thread démarré: {name}")
        
        # Démarrer TTS dans son propre thread
        tts_thread = threading.Thread(
            target=self.tts_service.run,
            name="Nav-TTSWorker",
            daemon=True
        )
        tts_thread.start()
        self.threads.append(tts_thread)
    
    def _camera_capture_loop(self):
        """Thread de capture vidéo."""
        fps_counter = 0
        last_fps_time = time.time()
        
        while self.running:
            try:
                start_time = time.time()
                
                # Capturer une frame
                frame = self.camera_adapter.capture_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Ajouter timestamp
                timestamp = time.time()
                
                # Mettre dans la queue (non bloquant)
                try:
                    self.frame_queue.put_nowait((frame, timestamp))
                except queue.Full:
                    # Jeter la frame la plus ancienne si nécessaire
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait((frame, timestamp))
                    except queue.Empty:
                        pass
                
                # Calcul FPS
                fps_counter += 1
                if time.time() - last_fps_time >= 1.0:
                    self.telemetry['fps']['camera'] = fps_counter
                    fps_counter = 0
                    last_fps_time = time.time()
                
                # Respecter le FPS configuré
                elapsed = time.time() - start_time
                target_delay = 1.0 / self.config['camera']['fps']
                if elapsed < target_delay:
                    time.sleep(target_delay - elapsed)
                    
            except Exception as e:
                logger.error(f"Erreur dans camera_capture_loop: {e}")
                time.sleep(0.1)
    
    def _detection_loop(self):
        """Thread de détection d'objets."""
        detection_times = []
        
        while self.running:
            try:
                # Récupérer une frame
                try:
                    frame, timestamp = self.frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                start_detect = time.time()
                
                # Détection d'objets
                detections = self.object_detector.detect(frame)
                
                # Ajouter timestamp et calculer bearing
                for det in detections:
                    det.timestamp = timestamp
                    
                    # Calculer le bearing (position angulaire)
                    if det.bbox:
                        center_x = det.bbox[0] + det.bbox[2] / 2
                        # Convertir en degrés (-FOV/2 à +FOV/2)
                        fov = self.config['camera']['fov_deg']
                        det.bearing = (center_x - 0.5) * fov
                
                # Mesurer le temps de traitement
                detection_time = time.time() - start_detect
                detection_times.append(detection_time)
                
                # Garder seulement les 10 dernières mesures
                if len(detection_times) > 10:
                    detection_times.pop(0)
                
                # Calculer la latence moyenne
                if detection_times:
                    self.telemetry['latency']['detection'] = sum(detection_times) / len(detection_times)
                
                # Mettre dans la queue de fusion
                try:
                    self.fusion_queue.put_nowait((detections, timestamp))
                except queue.Full:
                    # Fusion est en retard, sauter cette frame
                    pass
                
                # Mettre à jour les statistiques
                self.stats['frames_processed'] += 1
                self.stats['detections_count'] += len(detections)
                
            except Exception as e:
                logger.error(f"Erreur dans detection_loop: {e}", exc_info=True)
                time.sleep(0.1)
    
    def _ultrasonic_loop(self):
        """Thread de lecture du capteur ultrasonique."""
        sample_interval = 1.0 / self.config['ultrasonic']['sample_rate_hz']
        
        while self.running:
            try:
                start_time = time.time()
                
                # Lire la distance
                distance = self.ultra_adapter.get_distance()
                
                # Créer la lecture
                reading = UltrasonicReading(
                    distance_cm=distance,
                    timestamp=time.time()
                )
                
                # Mettre dans la queue
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
                elapsed = time.time() - start_time
                if elapsed < sample_interval:
                    time.sleep(sample_interval - elapsed)
                    
            except Exception as e:
                logger.error(f"Erreur dans ultrasonic_loop: {e}")
                time.sleep(0.5)
    
    def _fusion_loop(self):
        """Thread de fusion des données."""
        fusion_times = []
        last_ultra_reading = None
        
        while self.running:
            try:
                start_fusion = time.time()
                
                # Récupérer la dernière lecture ultra
                ultra_readings = []
                while not self.ultra_queue.empty():
                    ultra_readings.append(self.ultra_queue.get_nowait())
                
                if ultra_readings:
                    last_ultra_reading = ultra_readings[-1]
                
                # Récupérer les détections
                try:
                    detections, timestamp = self.fusion_queue.get(timeout=0.05)
                except queue.Empty:
                    # Pas de nouvelle détection
                    if last_ultra_reading and time.time() - last_ultra_reading.timestamp < 0.5:
                        # Mettre à jour l'EOH avec seulement l'ultrason
                        self.eoh.update_ultrasound_only(
                            distance=last_ultra_reading.distance_cm,
                            timestamp=last_ultra_reading.timestamp
                        )
                    continue
                
                # Fusionner les données
                if last_ultra_reading:
                    self._fuse_detections(detections, last_ultra_reading)
                else:
                    # Utiliser seulement les détections visuelles
                    for detection in detections:
                        if detection.bearing is not None:
                            self.eoh.update(
                                bearing=detection.bearing,
                                distance=detection.distance_estimate or 200,  # Valeur par défaut
                                confidence=detection.confidence,
                                object_class=detection.class_name,
                                timestamp=detection.timestamp
                            )
                
                # Mesurer le temps de fusion
                fusion_time = time.time() - start_fusion
                fusion_times.append(fusion_time)
                
                if len(fusion_times) > 10:
                    fusion_times.pop(0)
                
                if fusion_times:
                    self.telemetry['latency']['fusion'] = sum(fusion_times) / len(fusion_times)
                
            except Exception as e:
                logger.error(f"Erreur dans fusion_loop: {e}", exc_info=True)
                time.sleep(0.05)
    
    def _fuse_detections(self, detections: List[Detection], ultra_reading: UltrasonicReading):
        """Fusionne les détections vision et ultrasons."""
        association_window = self.config['fusion']['association_window_ms'] / 1000.0
        
        for detection in detections:
            # Vérifier si la détection est récente
            if abs(detection.timestamp - ultra_reading.timestamp) > association_window:
                continue
            
            # Si l'objet est au centre (±15°), utiliser la distance ultrason
            if detection.bearing and abs(detection.bearing) < 15:
                detection.distance_estimate = ultra_reading.distance_cm
                confidence_boost = 1.0  # Ultrason considéré comme très fiable
            else:
                # Estimer la distance basée sur la taille de l'objet
                detection.distance_estimate = self._estimate_distance_from_bbox(
                    detection.class_name,
                    detection.bbox[3]  # height
                )
                confidence_boost = 0.7
            
            # Mettre à jour l'EOH
            if detection.bearing is not None and detection.distance_estimate is not None:
                self.eoh.update(
                    bearing=detection.bearing,
                    distance=detection.distance_estimate,
                    confidence=detection.confidence * confidence_boost,
                    object_class=detection.class_name,
                    timestamp=detection.timestamp
                )
    
    def _estimate_distance_from_bbox(self, class_name: str, bbox_height: float) -> float:
        """Estime la distance basée sur la hauteur du bounding box."""
        # Hauteurs de référence pour différentes classes (en pixels à 1m)
        reference_heights = {
            'person': 200,    # pixels
            'car': 150,       # pixels
            'bicycle': 120,   # pixels
            'motorcycle': 130, # pixels
            'bus': 180,       # pixels
            'truck': 170      # pixels
        }
        
        if class_name in reference_heights:
            ref_height = reference_heights[class_name]
            # Distance approximative = (hauteur de référence / hauteur détectée) * 100 cm
            distance = (ref_height / (bbox_height * self.config['camera']['height'])) * 100
            return max(50, min(500, distance))  # Limiter entre 50cm et 5m
        else:
            return 200  # Distance par défaut
    
    def _decision_loop(self):
        """Thread de prise de décision."""
        last_vocal_time = 0
        last_decision_time = 0
        
        while self.running:
            try:
                decision_start = time.time()
                
                # Obtenir le snapshot actuel de l'EOH
                snapshot = self.eoh.get_snapshot()
                
                # Évaluer la situation avec le PriorityEngine
                decision = self.priority_engine.evaluate(
                    eoh_snapshot=snapshot,
                    current_state=self.state
                )
                
                # Appliquer la décision
                if decision.action_needed:
                    current_time = time.time()
                    
                    # Vérifier le délai minimum entre messages
                    time_since_last_vocal = current_time - last_vocal_time
                    
                    if time_since_last_vocal >= self.config['thresholds']['min_vocal_interval_s']:
                        # Générer un message unique pour éviter les répétitions
                        message_hash = hash(decision.message)
                        
                        if message_hash not in self.recent_messages or \
                           current_time - self.recent_messages[message_hash] > 5.0:
                            
                            # Ajouter à la file TTS
                            self.tts_queue.put((
                                decision.priority,
                                {
                                    'text': decision.message,
                                    'priority': decision.priority,
                                    'timestamp': current_time
                                }
                            ))
                            
                            last_vocal_time = current_time
                            self.recent_messages[message_hash] = current_time
                            self.stats['warnings_issued'] += 1
                            
                            # Déclencher les callbacks
                            self._trigger_callbacks('on_alert', {
                                'type': decision.alert_type,
                                'distance': snapshot.min_distance,
                                'bearing': snapshot.closest_bearing,
                                'suggested_action': decision.suggested_action,
                                'confidence': decision.confidence,
                                'timestamp': current_time
                            })
                
                # Mettre à jour l'état si nécessaire
                if decision.new_state and decision.new_state != self.state:
                    self._set_state(decision.new_state)
                
                # Mesurer le temps de décision
                decision_time = time.time() - decision_start
                self.telemetry['latency']['decision'] = decision_time
                
                # Contrôle de fréquence (10 Hz)
                elapsed = time.time() - last_decision_time
                if elapsed < 0.1:
                    time.sleep(0.1 - elapsed)
                last_decision_time = time.time()
                
            except Exception as e:
                logger.error(f"Erreur dans decision_loop: {e}", exc_info=True)
                time.sleep(0.1)
    
    def _guidance_loop(self):
        """Thread de planification de guidage."""
        last_guidance_time = 0
        
        while self.running:
            try:
                # Ne fonctionne que dans les états ALERT et GUIDANCE
                if self.state not in [NavigationState.ALERT, NavigationState.GUIDANCE, NavigationState.EMERGENCY]:
                    time.sleep(0.2)
                    continue
                
                current_time = time.time()
                
                # Limiter la fréquence du guidage
                if current_time - last_guidance_time < 1.0:
                    time.sleep(0.1)
                    continue
                
                snapshot = self.eoh.get_snapshot()
                
                # Obtenir une suggestion de guidage
                guidance = self.guidance_planner.get_guidance(snapshot)
                
                if guidance['action'] != 'none':
                    # Créer le message de guidage
                    if guidance['action'] == 'stop':
                        message = "Arrêtez-vous, obstacle devant"
                    elif guidance['action'] == 'move_left':
                        message = f"Déplacez-vous à gauche, chemin libre sur {int(guidance['clear_distance'])} centimètres"
                    elif guidance['action'] == 'move_right':
                        message = f"Déplacez-vous à droite, chemin libre sur {int(guidance['clear_distance'])} centimètres"
                    elif guidance['action'] == 'slow_down':
                        message = "Ralentissez, obstacle approchant"
                    else:
                        message = "Continuez prudemment"
                    
                    # Ajouter à la file TTS avec priorité moyenne
                    self.tts_queue.put((
                        2,  # Priorité moyenne
                        {
                            'text': message,
                            'priority': 2,
                            'timestamp': current_time
                        }
                    ))
                    
                    # Déclencher callback
                    self._trigger_callbacks('on_guidance', guidance)
                
                last_guidance_time = current_time
                time.sleep(0.5)  # Vérifier toutes les 500ms
                
            except Exception as e:
                logger.error(f"Erreur dans guidance_loop: {e}")
                time.sleep(0.5)
    
    def _telemetry_loop(self):
        """Thread de télémetrie et logging."""
        last_telemetry_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Envoyer la télémetrie à intervalle régulier
                if current_time - last_telemetry_time >= self.config['system']['telemetry_interval_s']:
                    # Mettre à jour la télémetrie
                    snapshot = self.eoh.get_snapshot()
                    
                    self.telemetry.update({
                        'eoh_snapshot': snapshot.to_dict(),
                        'state': self.state.value,
                        'timestamp': current_time,
                        'uptime': current_time - self.stats['start_time'],
                        'stats': self.stats.copy(),
                        'queue_sizes': {
                            'frame': self.frame_queue.qsize(),
                            'ultra': self.ultra_queue.qsize(),
                            'fusion': self.fusion_queue.qsize(),
                            'tts': self.tts_queue.qsize()
                        }
                    })
                    
                    # Déclencher callback télémetrie
                    self._trigger_callbacks('on_telemetry', self.telemetry)
                    
                    # Sauvegarder si configuré
                    if self.config['system']['save_telemetry']:
                        self._save_telemetry_snapshot()
                    
                    last_telemetry_time = current_time
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Erreur dans telemetry_loop: {e}")
                time.sleep(1.0)
    
    def _health_monitor_loop(self):
        """Thread de monitoring de santé du système."""
        while self.running:
            try:
                # Vérifier les files d'attente bloquantes
                if (self.frame_queue.qsize() > 5 or 
                    self.tts_queue.qsize() > 15):
                    logger.warning(f"Files d'attente pleines: frame={self.frame_queue.qsize()}, tts={self.tts_queue.qsize()}")
                
                # Vérifier la latence
                if self.telemetry['latency']['detection'] > 0.3:
                    logger.warning(f"Latence de détection élevée: {self.telemetry['latency']['detection']:.2f}s")
                
                # Vérifier l'état des capteurs
                if self.ultra_adapter and self.ultra_adapter.last_read_time:
                    time_since_last_read = time.time() - self.ultra_adapter.last_read_time
                    if time_since_last_read > 2.0:
                        logger.warning(f"Pas de lecture ultrasonique depuis {time_since_last_read:.1f}s")
                
                time.sleep(5.0)  # Vérifier toutes les 5 secondes
                
            except Exception as e:
                logger.error(f"Erreur dans health_monitor_loop: {e}")
                time.sleep(5.0)
    
    def _save_telemetry_snapshot(self):
        """Sauvegarde un snapshot de télémetrie (simplifié)."""
        try:
            import json
            from pathlib import Path
            
            telemetry_dir = Path("telemetry")
            telemetry_dir.mkdir(exist_ok=True)
            
            filename = telemetry_dir / f"nav_telemetry_{int(time.time())}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.telemetry, f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde télémetrie: {e}")
    
    def _set_state(self, new_state: NavigationState):
        """Change l'état du module."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            
            # Ajouter à l'historique
            self.telemetry['state_history'].append({
                'old_state': old_state.value,
                'new_state': new_state.value,
                'timestamp': time.time()
            })
            
            # Garder seulement les 50 derniers états
            if len(self.telemetry['state_history']) > 50:
                self.telemetry['state_history'] = self.telemetry['state_history'][-50:]
            
            logger.info(f"État changé: {old_state.value} -> {new_state.value}")
            
            # Déclencher callback
            self._trigger_callbacks('on_state_change', {
                'old_state': old_state.value,
                'new_state': new_state.value,
                'timestamp': time.time()
            })
    
    def _trigger_callbacks(self, event_name: str, data: Dict):
        """Déclenche tous les callbacks pour un événement."""
        if event_name not in self.callbacks:
            return
        
        for callback in self.callbacks[event_name]:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Erreur dans callback {event_name}: {e}")
    
    def register_callback(self, event_name: str, callback: Callable):
        """Enregistre un callback pour un événement."""
        if event_name in self.callbacks:
            self.callbacks[event_name].append(callback)
            logger.debug(f"Callback enregistré pour {event_name}")
        else:
            logger.warning(f"Événement {event_name} non reconnu")
    
    def unregister_callback(self, event_name: str, callback: Callable):
        """Retire un callback."""
        if event_name in self.callbacks and callback in self.callbacks[event_name]:
            self.callbacks[event_name].remove(callback)
    
    def get_state(self) -> Dict:
        """Retourne l'état courant du module."""
        snapshot = self.eoh.get_snapshot() if self.eoh else None
        
        return {
            'module_state': self.state.value,
            'running': self.running,
            'eoh_snapshot': snapshot.to_dict() if snapshot else None,
            'telemetry_summary': {
                'fps': self.telemetry['fps'],
                'latency': self.telemetry['latency'],
                'uptime': time.time() - self.stats['start_time']
            },
            'statistics': self.stats,
            'config': {
                'thresholds': self.config['thresholds'],
                'guidance': self.config['guidance']
            }
        }
    
    def calibrate_camera(self, camera_params: Dict):
        """Calibre les paramètres de la caméra."""
        if 'fov_deg' in camera_params:
            self.config['camera']['fov_deg'] = camera_params['fov_deg']
            if self.eoh:
                self.eoh.fov = camera_params['fov_deg']
        
        if 'reference_heights' in camera_params:
            # Mettre à jour les hauteurs de référence pour l'estimation de distance
            pass
        
        logger.info(f"Caméra calibrée: {camera_params}")
        
        return True
    
    def set_thresholds(self, thresholds: Dict):
        """Met à jour les seuils de détection."""
        updated = False
        
        for key, value in thresholds.items():
            if key in self.config['thresholds']:
                old_value = self.config['thresholds'][key]
                self.config['thresholds'][key] = value
                
                # Mettre à jour les composants concernés
                if key in ['emergency_dist_cm', 'alert_dist_cm', 'warning_dist_cm', 'min_vocal_interval_s']:
                    if self.priority_engine:
                        if key == 'emergency_dist_cm':
                            self.priority_engine.emergency_dist = value
                        elif key == 'alert_dist_cm':
                            self.priority_engine.alert_dist = value
                        elif key == 'warning_dist_cm':
                            self.priority_engine.warning_dist = value
                        elif key == 'min_vocal_interval_s':
                            self.priority_engine.min_vocal_interval = value
                
                logger.info(f"Seuil {key} changé: {old_value} -> {value}")
                updated = True
        
        if updated:
            return True
        else:
            logger.warning(f"Aucun seuil reconnu dans: {thresholds.keys()}")
            return False
    
    def force_announce(self, text: str, priority: str = 'medium'):
        """Force l'annonce d'un message (debug/manuel)."""
        priority_map = {
            'emergency': 0,
            'high': 1,
            'medium': 2,
            'low': 3
        }
        
        priority_level = priority_map.get(priority, 2)
        
        self.tts_queue.put((
            priority_level,
            {
                'text': text,
                'priority': priority_level,
                'timestamp': time.time(),
                'forced': True
            }
        ))
        
        logger.info(f"Message forcé: '{text}' (priorité: {priority})")
        
        return True
    
    def get_sensor_data(self) -> Dict:
        """Retourne les dernières données des capteurs (debug)."""
        ultra_data = []
        while not self.ultra_queue.empty():
            ultra_data.append(self.ultra_queue.get_nowait())
        
        # Remettre les données dans la queue
        for data in ultra_data:
            try:
                self.ultra_queue.put_nowait(data)
            except queue.Full:
                pass
        
        return {
            'ultrasonic': {
                'last_reading': ultra_data[-1] if ultra_data else None,
                'queue_size': self.ultra_queue.qsize()
            },
            'camera': {
                'queue_size': self.frame_queue.qsize(),
                'fps': self.telemetry['fps']['camera']
            },
            'detection': {
                'queue_size': self.fusion_queue.qsize(),
                'latency': self.telemetry['latency']['detection']
            },
            'system': {
                'state': self.state.value,
                'threads_alive': sum(1 for t in self.threads if t.is_alive()),
                'uptime': time.time() - self.stats['start_time']
            }
        }
    
    def stop(self):
        """Arrête proprement tous les composants."""
        if not self.running:
            return
        
        logger.info("Arrêt du NavigationModule...")
        self.running = False
        
        # Arrêter les adaptateurs
        if self.camera_adapter:
            self.camera_adapter.close()
        
        if self.ultra_adapter:
            self.ultra_adapter.cleanup()
        
        # Arrêter TTS
        if self.tts_service:
            self.tts_service.stop()
        
        # Vider les queues
        queues = [self.frame_queue, self.ultra_queue, self.detection_queue, 
                  self.fusion_queue, self.tts_queue]
        
        for q in queues:
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    pass
        
        # Attendre la fin des threads
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
                if thread.is_alive():
                    logger.warning(f"Thread {thread.name} n'a pas terminé à temps")
        
        # Transition vers l'état IDLE
        self._set_state(NavigationState.IDLE)
        
        # Calculer les statistiques finales
        total_time = time.time() - self.stats['start_time']
        logger.info(f"NavigationModule arrêté. Statistiques:")
        logger.info(f"  Temps total: {total_time:.1f}s")
        logger.info(f"  Frames traitées: {self.stats['frames_processed']}")
        logger.info(f"  Détections: {self.stats['detections_count']}")
        logger.info(f"  Alertes émises: {self.stats['warnings_issued']}")
        
        return True
    
    def __enter__(self):
        """Support du contexte manager."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du contexte manager."""
        self.stop()
    
    def get_performance_stats(self) -> Dict:
        """Retourne les statistiques de performance."""
        total_time = time.time() - self.stats['start_time']
        
        return {
            'uptime_seconds': total_time,
            'frames_per_second': self.stats['frames_processed'] / total_time if total_time > 0 else 0,
            'detections_per_frame': self.stats['detections_count'] / self.stats['frames_processed'] if self.stats['frames_processed'] > 0 else 0,
            'warnings_per_minute': (self.stats['warnings_issued'] / total_time) * 60 if total_time > 0 else 0,
            'average_latencies': self.telemetry['latency'],
            'current_state': self.state.value,
            'memory_usage': self._get_memory_usage()
        }
    
    def _get_memory_usage(self):
        """Estime l'utilisation mémoire."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return None
    
    def reset_statistics(self):
        """Réinitialise les statistiques."""
        self.stats = {
            'start_time': time.time(),
            'frames_processed': 0,
            'detections_count': 0,
            'warnings_issued': 0
        }
        logger.info("Statistiques réinitialisées")